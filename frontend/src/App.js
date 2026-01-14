import React, { useState } from 'react';
import RepoInput from './components/RepoInput';
import FormatSelector from './components/FormatSelector';
import DownloadButton from './components/DownloadButton';

// API base URL - use environment variable or default to empty for proxy
const API_BASE_URL = process.env.REACT_APP_API_URL || '';

function App() {
  const [repoUrl, setRepoUrl] = useState('');
  const [format, setFormat] = useState('markdown');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null); // { type: 'success' | 'error' | 'loading', message: string }
  const [downloadUrl, setDownloadUrl] = useState(null);
  const [fileCount, setFileCount] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!repoUrl.trim()) {
      setStatus({ type: 'error', message: 'Please enter a repository URL' });
      return;
    }

    setLoading(true);
    setStatus({ type: 'loading', message: 'Processing repository... This may take a moment.' });
    setDownloadUrl(null);
    setFileCount(null);

    try {
      const response = await fetch(`${API_BASE_URL}/process-repo`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          repo_url: repoUrl,
          format: format,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to process repository');
      }

      setStatus({ type: 'success', message: data.message || 'Repository processed successfully!' });
      setDownloadUrl(`${API_BASE_URL}${data.download_url}`);
      setFileCount(data.file_count);
    } catch (error) {
      setStatus({ type: 'error', message: error.message || 'An error occurred. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setRepoUrl('');
    setFormat('markdown');
    setStatus(null);
    setDownloadUrl(null);
    setFileCount(null);
  };

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <h1>Repository Code Dumper</h1>
          <p>Clone any public GitHub repo and download all code as a single file</p>
        </header>

        <div className="card">
          <form onSubmit={handleSubmit}>
            <RepoInput 
              value={repoUrl} 
              onChange={setRepoUrl} 
              disabled={loading}
            />
            
            <FormatSelector 
              value={format} 
              onChange={setFormat}
              disabled={loading}
            />

            <button 
              type="submit" 
              className="btn btn-primary" 
              disabled={loading || !repoUrl.trim()}
            >
              {loading ? (
                <>
                  <span className="loading-spinner"></span>
                  Processing...
                </>
              ) : (
                'Generate Code Dump'
              )}
            </button>
          </form>

          {status && (
            <div className={`status-message status-${status.type}`}>
              {status.message}
            </div>
          )}

          {downloadUrl && (
            <div className="download-section">
              {fileCount && (
                <div className="download-info">
                  <span className="file-count">{fileCount}</span> files processed
                </div>
              )}
              <DownloadButton 
                url={downloadUrl} 
                format={format}
                onReset={handleReset}
              />
            </div>
          )}
        </div>

        <footer className="footer">
          <p>
            Only public GitHub repositories are supported.
            <br />
            Built with React and FastAPI
          </p>
        </footer>
      </div>
    </div>
  );
}

export default App;
