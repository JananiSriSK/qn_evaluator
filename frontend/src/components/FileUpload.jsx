import { useState } from 'react';

export default function FileUpload({ onUpload, accept, multiple, label }) {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    try {
      await onUpload(multiple ? files : files[0]);
      setFiles([]);
    } catch (err) {
      console.error('Upload failed:', err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ padding: '20px', border: '2px dashed #ddd', borderRadius: '4px', backgroundColor: '#fafafa' }}>
      <label style={{ display: 'block', marginBottom: '10px', fontWeight: '500' }}>{label}</label>
      <input
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleFileChange}
        style={{ marginBottom: '10px' }}
      />
      {files.length > 0 && (
        <div style={{ marginBottom: '10px', fontSize: '14px', color: '#666' }}>
          {files.length} file(s) selected
        </div>
      )}
      <button
        onClick={handleUpload}
        disabled={files.length === 0 || uploading}
        style={{ padding: '10px 20px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: files.length === 0 || uploading ? 'not-allowed' : 'pointer', opacity: files.length === 0 || uploading ? 0.6 : 1 }}
      >
        {uploading ? 'Uploading...' : 'Upload'}
      </button>
    </div>
  );
}
