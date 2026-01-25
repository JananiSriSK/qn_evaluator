import { useState } from 'react';

/**
 * Form component for uploading reference books
 * Handles PDF upload and processing
 */
const BookUploadForm = () => {
  const [formData, setFormData] = useState({
    courseName: '',
    bookName: ''
  });
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setError('');
    } else {
      setSelectedFile(null);
      setError('Please select a PDF file');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select a PDF file');
      return;
    }

    setLoading(true);
    setResult(null);
    setError('');

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('file', selectedFile);
      formDataToSend.append('course_name', formData.courseName);
      formDataToSend.append('book_name', formData.bookName);

      const response = await fetch('http://localhost:8001/process-book', {
        method: 'POST',
        body: formDataToSend,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to process book');
      }

      const bookResult = await response.json();
      setResult(bookResult);
      
    } catch (err) {
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h2>Reference Book Upload</h2>
      <p>Upload PDF reference books to enhance question explanations.</p>
      
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '15px' }}>
          <label htmlFor="courseName" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Course Name:
          </label>
          <input
            type="text"
            id="courseName"
            value={formData.courseName}
            onChange={(e) => setFormData({ ...formData, courseName: e.target.value })}
            required
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
            placeholder="e.g., PYTHON PROGRAMMING WITH DATA SCIENCE"
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label htmlFor="bookName" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Book Name:
          </label>
          <input
            type="text"
            id="bookName"
            value={formData.bookName}
            onChange={(e) => setFormData({ ...formData, bookName: e.target.value })}
            required
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
            placeholder="e.g., Python Programming Fundamentals"
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label htmlFor="pdfFile" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            PDF File:
          </label>
          <input
            type="file"
            id="pdfFile"
            accept=".pdf"
            onChange={handleFileChange}
            required
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
          />
          {selectedFile && (
            <div style={{ marginTop: '5px', fontSize: '14px', color: '#666' }}>
              Selected: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={loading || !selectedFile}
          style={{
            backgroundColor: loading || !selectedFile ? '#ccc' : '#007bff',
            color: 'white',
            padding: '10px 20px',
            border: 'none',
            borderRadius: '4px',
            cursor: loading || !selectedFile ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Processing...' : 'Upload Book'}
        </button>
      </form>

      {error && (
        <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#f8d7da', border: '1px solid #f5c6cb', borderRadius: '4px' }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#d4edda', border: '1px solid #c3e6cb', borderRadius: '4px' }}>
          <h3>Upload Results</h3>
          <div><strong>Message:</strong> {result.message}</div>
          <div><strong>Book:</strong> {result.book_name}</div>
          <div><strong>Chunks Processed:</strong> {result.chunks_processed}</div>
          <div><strong>Units Mapped:</strong> {result.units_mapped}</div>
        </div>
      )}
    </div>
  );
};

export default BookUploadForm;