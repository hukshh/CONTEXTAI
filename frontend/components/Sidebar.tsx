import React, { useRef } from 'react';
import { uploadFile } from '../services/api';

interface SidebarProps {
  files: string[];
  onUploadSuccess: (filename: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ files, onUploadSuccess }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const result = await uploadFile(file);
      onUploadSuccess(result.filename);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Failed to upload file");
    }
  };

  return (
    <div className="sidebar">
      <div className="logo">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
        ContextAI
      </div>

      <div className="upload-section">
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleFileChange} 
          style={{ display: 'none' }} 
          accept=".pdf"
        />
        <button className="upload-button" onClick={handleUploadClick}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          Upload PDF
        </button>
      </div>

      <div className="sidebar-divider"></div>

      <div className="sidebar-title">
        Uploaded Files
      </div>
      
      <ul className="file-list">
        {files.length === 0 ? (
          <li className="file-item" style={{ fontStyle: 'italic', opacity: 0.5 }}>
            No files uploaded yet
          </li>
        ) : (
          files.map((file, index) => (
            <li key={index} className="file-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{file}</span>
            </li>
          ))
        )}
      </ul>
    </div>
  );
};

export default Sidebar;
