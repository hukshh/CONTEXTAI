import React, { useRef, useState } from 'react';
import { uploadFile } from '../services/api';

interface SidebarProps {
  files: {name: string, isIndexed: boolean}[];
  selectedFiles: string[];
  onUploadSuccess: (filename: string) => void;
  onSelectionChange: (selected: string[]) => void;
  onDeleteFile: (filename: string) => void;
  onClearAll: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  files, 
  selectedFiles, 
  onUploadSuccess, 
  onSelectionChange, 
  onDeleteFile, 
  onClearAll 
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUploadClick = () => {
    if (isUploading) return;
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      const result = await uploadFile(file);
      // Immediately clear loading so user can use the app
      setIsUploading(false);
      alert(`Upload complete! "${result.filename}" is being processed in the background and will appear in the list shortly.`);
      onUploadSuccess(result.filename);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (error) {
      alert("Failed to upload file. Please ensure it is a valid PDF.");
      setIsUploading(false);
    }
  };

  const toggleFileSelection = (filename: string) => {
    if (selectedFiles.includes(filename)) {
      onSelectionChange(selectedFiles.filter(f => f !== filename));
    } else {
      onSelectionChange([...selectedFiles, filename]);
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
        <button 
          className="upload-button" 
          onClick={handleUploadClick} 
          disabled={isUploading}
          style={{ opacity: isUploading ? 0.7 : 1, cursor: isUploading ? 'not-allowed' : 'pointer' }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          {isUploading ? 'Processing...' : 'Upload PDF'}
        </button>
      </div>

      <div className="sidebar-divider"></div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 20px', marginBottom: '12px' }}>
        <div className="sidebar-title" style={{ margin: 0 }}>Documents</div>
        {files.length > 0 && (
          <button 
            onClick={() => window.confirm("Reset entire system? This will clear all files and history.") && onClearAll()}
            style={{ 
              fontSize: '0.7rem', 
              color: '#ff4d4f', 
              background: 'none', 
              border: 'none', 
              cursor: 'pointer',
              textTransform: 'uppercase',
              fontWeight: 700
            }}
          >
            Clear All
          </button>
        )}
      </div>
      
      <ul className="file-list" style={{ flex: 1, overflowY: 'auto' }}>
        {files.length === 0 ? (
          <li className="file-item" style={{ fontStyle: 'italic', opacity: 0.5, justifyContent: 'center' }}>
            No files uploaded
          </li>
        ) : (
          files.map((file, index) => (
            <li 
              key={index} 
              className={`file-item ${selectedFiles.includes(file.name) ? 'active' : ''}`}
              style={{ 
                cursor: file.isIndexed ? 'pointer' : 'default', 
                backgroundColor: selectedFiles.includes(file.name) ? 'rgba(0,0,0,0.04)' : 'transparent',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                opacity: file.isIndexed ? 1 : 0.7
              }}
              onClick={() => file.isIndexed && toggleFileSelection(file.name)}
            >
              <input 
                type="checkbox" 
                checked={selectedFiles.includes(file.name)} 
                disabled={!file.isIndexed}
                onChange={() => {}} 
                style={{ cursor: file.isIndexed ? 'pointer' : 'default' }}
              />
              <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                <span style={{ 
                  overflow: 'hidden', 
                  textOverflow: 'ellipsis', 
                  whiteSpace: 'nowrap',
                  fontSize: '0.85rem',
                  fontWeight: selectedFiles.includes(file.name) ? 600 : 400
                }}>
                  {file.name}
                </span>
                {!file.isIndexed && (
                  <span style={{ fontSize: '0.65rem', color: 'var(--primary-color)', fontWeight: 700 }}>
                    Indexing...
                  </span>
                )}
              </div>
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  if (window.confirm(`Delete ${file.name}?`)) onDeleteFile(file.name);
                }}
                style={{ 
                  background: 'none', 
                  border: 'none', 
                  color: '#ff4d4f', 
                  cursor: 'pointer',
                  padding: '4px',
                  display: 'flex',
                  alignItems: 'center'
                }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="3 6 5 6 21 6" />
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                </svg>
              </button>
            </li>
          ))
        )}
      </ul>
      
      {files.length > 0 && (
        <div style={{ padding: '16px', fontSize: '0.75rem', color: 'var(--secondary-text)', textAlign: 'center', borderTop: '1px solid var(--border-color)' }}>
          {selectedFiles.length} file(s) selected
        </div>
      )}
    </div>
  );
};

export default Sidebar;
