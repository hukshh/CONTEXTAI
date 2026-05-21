import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Sidebar from '../components/Sidebar';
import ChatInterface from '../components/ChatInterface';
import { listFiles, deleteFile, clearAllData, API_BASE_URL } from '../services/api';

interface FileWithStatus {
  name: string;
  isIndexed: boolean;
  status: string;
  progress: number;
  error?: string;
}

export default function Home() {
  const [uploadedFiles, setUploadedFiles] = useState<FileWithStatus[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [chatKey, setChatKey] = useState(0);

  const fetchFiles = async () => {
    try {
      const data = await listFiles();
      const filesToSet = data.files || [];
      setUploadedFiles(filesToSet);
      return filesToSet;
    } catch (error) {
      console.error("Home: Failed to fetch files", error);
      return [];
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchFiles().then(files => {
      // Auto-select already indexed files
      const indexed = files.filter((f: any) => f.isIndexed).map((f: any) => f.name);
      setSelectedFiles(indexed);
    });

    // Subscribe to Server-Sent Events for realtime progress updates
    const streamUrl = `${API_BASE_URL}/files/stream-status`;
    console.log("Home: Connecting to SSE stream at", streamUrl);
    const eventSource = new EventSource(streamUrl);

    eventSource.addEventListener("status_update", (event: any) => {
      try {
        const data = JSON.parse(event.data);
        console.log("Home: SSE status update received:", data);

        setUploadedFiles(prev => {
          const fileIndex = prev.findIndex(f => f.name === data.filename);
          
          if (fileIndex !== -1) {
            const updated = [...prev];
            updated[fileIndex] = {
              ...updated[fileIndex],
              status: data.status,
              progress: data.progress,
              error: data.error || undefined,
              isIndexed: data.status === 'ready'
            };
            return updated;
          } else {
            return [
              ...prev,
              {
                name: data.filename,
                isIndexed: data.status === 'ready',
                status: data.status,
                progress: data.progress,
                error: data.error || undefined
              }
            ];
          }
        });

        // Auto-select file when it becomes ready
        if (data.status === 'ready') {
          setSelectedFiles(prev => Array.from(new Set([...prev, data.filename])));
        }
      } catch (err) {
        console.error("Home: Error parsing SSE data", err);
      }
    });

    eventSource.onerror = (err) => {
      console.warn("Home: SSE connection error, browser will auto-reconnect", err);
    };

    return () => {
      console.log("Home: Closing SSE connection");
      eventSource.close();
    };
  }, []);

  const handleUploadSuccess = (filename: string) => {
    // Immediate local status update (before SSE event triggers)
    setUploadedFiles(prev => {
      if (prev.some(f => f.name === filename)) return prev;
      return [
        ...prev,
        {
          name: filename,
          isIndexed: false,
          status: 'uploaded',
          progress: 0.0
        }
      ];
    });
  };

  const handleDeleteFile = async (filename: string) => {
    try {
      await deleteFile(filename);
      setUploadedFiles(prev => prev.filter(f => f.name !== filename));
      setSelectedFiles(prev => prev.filter(f => f !== filename));
    } catch (error) {
      console.error("Home: Failed to delete file", error);
    }
  };

  const handleClearAll = async () => {
    try {
      await clearAllData();
      setUploadedFiles([]);
      setSelectedFiles([]);
      setChatKey(prev => prev + 1); // Reset chat state
    } catch (error) {
      console.error("Home: Failed to clear data", error);
    }
  };

  return (
    <div className="app-container" suppressHydrationWarning>
      <Head>
        <title>ContextAI - Intelligence for your documents</title>
        <meta name="description" content="Production-grade AI document assistant" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <Sidebar 
        files={uploadedFiles} 
        selectedFiles={selectedFiles}
        onUploadSuccess={handleUploadSuccess}
        onSelectionChange={setSelectedFiles}
        onDeleteFile={handleDeleteFile}
        onClearAll={handleClearAll}
      />
      <ChatInterface key={chatKey} selectedFiles={selectedFiles} />
    </div>
  );
}
