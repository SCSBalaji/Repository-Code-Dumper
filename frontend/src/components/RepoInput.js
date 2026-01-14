import React from 'react';

/**
 * RepoInput Component
 * Input field for GitHub repository URL
 */
function RepoInput({ value, onChange, disabled }) {
  return (
    <div className="form-group">
      <label htmlFor="repo-url">GitHub Repository URL</label>
      <div className="input-wrapper">
        <input
          type="text"
          id="repo-url"
          placeholder="https://github.com/owner/repository"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          autoComplete="url"
          spellCheck="false"
        />
      </div>
    </div>
  );
}

export default RepoInput;
