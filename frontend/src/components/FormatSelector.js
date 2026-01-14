import React from 'react';

/**
 * FormatSelector Component
 * Dropdown to select output format (Markdown or Plain Text)
 */
function FormatSelector({ value, onChange, disabled }) {
  return (
    <div className="form-group">
      <label htmlFor="output-format">Output Format</label>
      <div className="select-wrapper">
        <select
          id="output-format"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
        >
          <option value="markdown">Markdown (.md)</option>
          <option value="text">Plain Text (.txt)</option>
        </select>
      </div>
    </div>
  );
}

export default FormatSelector;
