import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Sidebar from '../components/Sidebar';
import ChatInterface from '../components/ChatInterface';
import { listFiles, deleteFile, clearAllData } from '../services/api';

export default function Home() {
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [chatKey, setChatKey] = useState(0); // Used to force-clear ChatInterface state

  const fetchFiles = async () => {
    try {
      const data = await listFiles();
      setUploadedFiles(data.files);
      return data.files;
    } catch (error) {
      console.error("Failed to fetch files:", error);
      return [];
    }
  };

  // Sync with backend on mount
  useEffect(() => {
    fetchFiles().then(files => {
      // Default select all on first load
      setSelectedFiles(files);
    });
  }, []);

  const handleUploadSuccess = (filename: string) => {
    // Start polling for the file until it appears in the list
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;
      const currentFiles = await fetchFiles();
      if (currentFiles.includes(filename) || attempts > 60) { // 2 mins timeout
        clearInterval(interval);
        if (currentFiles.includes(filename)) {
          setSelectedFiles(prev => Array.from(new Set([...prev, filename])));
        }
      }
    }, 2000); // Poll every 2 seconds
  };

  const handleDeleteFile = async (filename: string) => {
    try {
      await deleteFile(filename);
      setUploadedFiles(prev => prev.filter(f => f !== filename));
      setSelectedFiles(prev => prev.filter(f => f !== filename));
    } catch (error) {
      console.error("Delete failed:", error);
    }
  };

  const handleClearAll = async () => {
    try {
      await clearAllData();
      setUploadedFiles([]);
      setSelectedFiles([]);
      setChatKey(prev => prev + 1); // Reset chat state
    } catch (error) {
      console.error("Clear all failed:", error);
    }
  };

  return (
    <div className="app-container">
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
