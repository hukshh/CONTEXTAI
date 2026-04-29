import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Sidebar from '../components/Sidebar';
import ChatInterface from '../components/ChatInterface';
import { listFiles, deleteFile, clearAllData } from '../services/api';

export default function Home() {
  const [uploadedFiles, setUploadedFiles] = useState<{name: string, isIndexed: boolean}[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [chatKey, setChatKey] = useState(0);

  const fetchFiles = async () => {
    try {
      const data = await listFiles();
      const filesToSet = data.files || [];
      setUploadedFiles(filesToSet);
      return filesToSet;
    } catch (error) {
      return [];
    }
  };

  useEffect(() => {
    fetchFiles().then(files => {
      // Auto-select already indexed files
      const indexed = files.filter((f: any) => f.isIndexed).map((f: any) => f.name);
      setSelectedFiles(indexed);
    });
  }, []);

  const handleUploadSuccess = (filename: string) => {
    // Start polling for the file until it is fully indexed
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;
      try {
        const currentFiles = await fetchFiles();
        const file = currentFiles.find((f: any) => f.name === filename);
        
        // Stop polling if file is indexed or we timed out (10 minutes)
        if ((file && file.isIndexed) || attempts > 300) {
          clearInterval(interval);
          if (file && file.isIndexed) {
            setSelectedFiles(prev => Array.from(new Set([...prev, filename])));
          }
        }
      } catch (error) {
        // Polling error silently ignored in prod
      }
    }, 2000);
  };

  const handleDeleteFile = async (filename: string) => {
    try {
      await deleteFile(filename);
      setUploadedFiles(prev => prev.filter(f => f.name !== filename));
      setSelectedFiles(prev => prev.filter(f => f !== filename));
    } catch (error) {
      // Handle error gracefully if needed
    }
  };

  const handleClearAll = async () => {
    try {
      await clearAllData();
      setUploadedFiles([]);
      setSelectedFiles([]);
      setChatKey(prev => prev + 1); // Reset chat state
    } catch (error) {
      // Clear all failed silently ignored
    }
  };

  return (
    <div className="app-container" suppressHydrationWarning>
      <Head>
        <title>ContextAI - Intelligence for your documents</title>
        <meta name="description" content="Production-ready AI document assistant" />
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
