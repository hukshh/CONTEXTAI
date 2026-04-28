import React, { useState } from 'react';
import Head from 'next/head';
import Sidebar from '../components/Sidebar';
import ChatInterface from '../components/ChatInterface';

export default function Home() {
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);

  const handleUploadSuccess = (filename: string) => {
    setUploadedFiles(prev => [...prev, filename]);
  };

  return (
    <div className="app-container">
      <Head>
        <title>ContextAI - Intelligence for your documents</title>
        <meta name="description" content="Production-ready AI document assistant" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <Sidebar files={uploadedFiles} onUploadSuccess={handleUploadSuccess} />
      <ChatInterface />
    </div>
  );
}
