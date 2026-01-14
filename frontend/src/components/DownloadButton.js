import React from 'react';

/**
 * DownloadButton Component
 * Button to download the generated output file
 */
function DownloadButton({ url, format, onReset }) {
  const handleDownload = () => {
    // Create a temporary link and trigger download
    const link = document.createElement('a');
    link.href = url;
    link.download = format === 'markdown' ? 'repository-dump.md' : 'repository-dump.txt';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div>
      <button 
        type="button" 
        className="btn btn-success" 
        onClick={handleDownload}
      >
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          width="20" 
          height="20" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2" 
          strokeLinecap="round" 
          strokeLinejoin="round"
        >
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="7 10 12 15 17 10"></polyline>
          <line x1="12" y1="15" x2="12" y2="3"></line>
        </svg>
        Download {format === 'markdown' ? 'Markdown' : 'Text'} File
      </button>
      
      <button 
        type="button" 
        className="btn btn-primary" 
        onClick={onReset}
        style={{ marginTop: '0.75rem', backgroundColor: 'transparent', border: '1px solid var(--border-color)' }}
      >
        Process Another Repository
      </button>
    </div>
  );
}

export default DownloadButton;
