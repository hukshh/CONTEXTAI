import React, { useRef, useState } from 'react';
import { uploadFileWithProgress } from '../services/api';

interface FileWithStatus {
  name: string;
  isIndexed: boolean;
  status: string;
  progress: number;
  error?: string;
}

interface SidebarProps {
  files: FileWithStatus[];
  selectedFiles: string[];
  onUploadSuccess: (filename: string) => void;
  onSelectionChange: (selected: string[]) => void;
  onDeleteFile: (filename: string) => void;
  onClearAll: () => void;
}

interface LocalUploadState {
  name: string;
  progress: number;
  status: 'uploading' | 'failed';
}

const Sidebar: React.FC<SidebarProps> = ({ 
  files, 
  selectedFiles, 
  onUploadSuccess, 
  onSelectionChange, 
  onDeleteFile, 
  onClearAll 
}) => {
  const [localUploads, setLocalUploads] = useState<{[key: string]: LocalUploadState}>({});
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const startUpload = async (file: File) => {
    const tempId = `${Date.now()}_${file.name}`;
    setLocalUploads(prev => ({
      ...prev,
      [tempId]: { name: file.name, progress: 0, status: 'uploading' }
    }));

    try {
      const result = await uploadFileWithProgress(file, (progress) => {
        setLocalUploads(prev => ({
          ...prev,
          [tempId]: { ...prev[tempId], progress }
        }));
      });

      // Clear from local network uploads since it's now tracked by the backend
      setLocalUploads(prev => {
        const copy = { ...prev };
        delete copy[tempId];
        return copy;
      });

      onUploadSuccess(result.filename);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (error: any) {
      setLocalUploads(prev => ({
        ...prev,
        [tempId]: { ...prev[tempId], status: 'failed', progress: 0 }
      }));
    }
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    await startUpload(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === "application/pdf" || file.name.endsWith(".pdf")) {
        await startUpload(file);
      } else {
        alert("Only PDF files are supported!");
      }
    }
  };

  const toggleFileSelection = (filename: string) => {
    if (selectedFiles.includes(filename)) {
      onSelectionChange(selectedFiles.filter(f => f !== filename));
    } else {
      onSelectionChange([...selectedFiles, filename]);
    }
  };

  const formatDisplayName = (filename: string) => {
    if (filename.length > 33 && filename[32] === '_') {
      return filename.substring(33);
    }
    return filename;
  };

  const renderStatusInfo = (file: FileWithStatus) => {
    switch (file.status) {
      case 'parsing':
        return (
          <div style={{ width: '100%' }}>
            <span className="status-indicator parsing pulsate">
              Parsing Document... ({Math.round(file.progress)}%)
            </span>
            <div className="progress-bar-container">
              <div className="progress-bar" style={{ width: `${file.progress}%` }}></div>
            </div>
          </div>
        );
      case 'embedding':
        return (
          <div style={{ width: '100%' }}>
            <span className="status-indicator embedding pulsate">
              Generating Embeddings... ({Math.round(file.progress)}%)
            </span>
            <div className="progress-bar-container">
              <div className="progress-bar" style={{ width: `${file.progress}%` }}></div>
            </div>
          </div>
        );
      case 'indexing':
        return (
          <div style={{ width: '100%' }}>
            <span className="status-indicator indexing pulsate">
              Indexing Vectors... ({Math.round(file.progress)}%)
            </span>
            <div className="progress-bar-container">
              <div className="progress-bar" style={{ width: `${file.progress}%` }}></div>
            </div>
          </div>
        );
      case 'failed':
        return (
          <span className="status-indicator failed" style={{ fontSize: '0.7rem' }}>
            ⚠️ Failed: {file.error || 'Ingestion failed'}
          </span>
        );
      case 'ready':
      default:
        return (
          <span className="status-indicator ready">
            ✓ Ready for chat
          </span>
        );
    }
  };

  const isUploadingAny = Object.values(localUploads).some(u => u.status === 'uploading');

  return (
    <div className="sidebar">
      <div className="logo">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
        ContextAI
      </div>

      <div 
        className={`drag-drop-zone ${isDragActive ? 'active' : ''}`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => !isUploadingAny && fileInputRef.current?.click()}
      >
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleFileChange} 
          style={{ display: 'none' }} 
          accept=".pdf"
        />
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ color: 'var(--text-secondary)', marginBottom: '4px' }}>
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="12" y1="18" x2="12" y2="12" />
          <polyline points="9 15 12 12 15 15" />
        </svg>
        <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>
          {isDragActive ? "Drop your PDF here" : "Drag & Drop PDF here"}
        </div>
        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
          or click to browse files
        </div>
      </div>

      <div className="sidebar-divider"></div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <div className="sidebar-title" style={{ margin: 0, fontSize: '0.8rem', fontWeight: 700 }}>Documents</div>
        {files.length > 0 && (
          <button 
            onClick={() => window.confirm("Reset entire system? This will clear all files and index history.") && onClearAll()}
            style={{ 
              fontSize: '0.7rem', 
              color: '#ff4d4f', 
              background: 'none', 
              border: 'none', 
              cursor: 'pointer',
              textTransform: 'uppercase',
              fontWeight: 700,
              letterSpacing: '0.05em'
            }}
          >
            Clear All
          </button>
        )}
      </div>
      
      <ul className="file-list" style={{ flex: 1, overflowY: 'auto' }}>
        {/* Network uploading files list */}
        {Object.entries(localUploads).map(([id, upload]) => (
          <li key={id} className="file-item" style={{ opacity: 0.8, pointerEvents: 'none' }}>
            <div style={{ width: '100%', display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {upload.name}
              </span>
              {upload.status === 'uploading' ? (
                <div style={{ width: '100%' }}>
                  <span className="status-indicator parsing pulsate">
                    Uploading... ({Math.round(upload.progress)}%)
                  </span>
                  <div className="progress-bar-container">
                    <div className="progress-bar" style={{ width: `${upload.progress}%` }}></div>
                  </div>
                </div>
              ) : (
                <span className="status-indicator failed">
                  ⚠️ Upload failed
                </span>
              )}
            </div>
          </li>
        ))}

        {/* Saved/ingesting files list */}
        {files.length === 0 && Object.keys(localUploads).length === 0 ? (
          <li className="file-item" style={{ fontStyle: 'italic', opacity: 0.5, justifyContent: 'center', border: '1px dashed var(--border)' }}>
            No files uploaded
          </li>
        ) : (
          files.map((file, index) => (
            <li 
              key={index} 
              className={`file-item ${selectedFiles.includes(file.name) ? 'active' : ''}`}
              style={{ 
                cursor: file.isIndexed ? 'pointer' : 'default',
              }}
              onClick={() => file.isIndexed && toggleFileSelection(file.name)}
            >
              <input 
                type="checkbox" 
                checked={selectedFiles.includes(file.name)} 
                disabled={!file.isIndexed}
                onChange={() => {}} 
                onClick={(e) => e.stopPropagation()}
                style={{ 
                  cursor: file.isIndexed ? 'pointer' : 'default',
                  accentColor: 'var(--accent-color)'
                }}
              />
              <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                <span style={{ 
                  overflow: 'hidden', 
                  textOverflow: 'ellipsis', 
                  whiteSpace: 'nowrap',
                  fontSize: '0.85rem',
                  fontWeight: selectedFiles.includes(file.name) ? 600 : 500
                }}>
                  {formatDisplayName(file.name)}
                </span>
                {renderStatusInfo(file)}
              </div>
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  if (window.confirm(`Delete ${formatDisplayName(file.name)}?`)) onDeleteFile(file.name);
                }}
                style={{ 
                  background: 'none', 
                  border: 'none', 
                  color: '#ff4d4f', 
                  cursor: 'pointer',
                  padding: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  opacity: 0.6,
                  transition: 'opacity 0.2s'
                }}
                onMouseEnter={(e) => (e.currentTarget.style.opacity = '1')}
                onMouseLeave={(e) => (e.currentTarget.style.opacity = '0.6')}
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
        <div style={{ padding: '12px 0 0 0', fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center', borderTop: '1px solid var(--border)' }}>
          {selectedFiles.length} of {files.length} active
        </div>
      )}
    </div>
  );
};

export default Sidebar;
