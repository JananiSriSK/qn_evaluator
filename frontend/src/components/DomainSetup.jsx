import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api-v2';
import FileUpload from './FileUpload';
import Modal from './Modal';

export default function DomainSetup({ userId, domainName }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState('');
  const [modal, setModal] = useState({ isOpen: false, title: '', message: '', type: 'info' });
  const navigate = useNavigate();

  useEffect(() => {
    loadStatus();
  }, [userId, domainName]);

  const loadStatus = async () => {
    setLoading(true);
    try {
      const data = await api.getDomainStatus(userId, domainName);
      setStatus(data);
    } catch (err) {
      console.error('Failed to load status:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSyllabusUpload = async (file) => {
    setUploading(true);
    setUploadProgress('Uploading syllabus...');
    try {
      await api.uploadSyllabus(userId, domainName, file);
      setUploadProgress('Syllabus uploaded successfully!');
      await loadStatus();
      setTimeout(() => {
        setModal({ isOpen: true, title: 'Success', message: 'Syllabus uploaded successfully!', type: 'success' });
        setUploadProgress('');
        setUploading(false);
      }, 500);
    } catch (err) {
      setUploadProgress('');
      setUploading(false);
      setModal({ isOpen: true, title: 'Error', message: 'Failed to upload syllabus: ' + err.message, type: 'error' });
    }
  };

  const handleBooksUpload = async (files) => {
    setUploading(true);
    setUploadProgress(`Uploading ${files.length} book(s)... Building FAISS index and enriching syllabus...`);
    try {
      const result = await api.uploadBooks(userId, domainName, files);
      setUploadProgress(`Books uploaded! ${result.chunks_indexed} chunks indexed.`);
      await loadStatus();
      setTimeout(() => {
        setModal({ isOpen: true, title: 'Success', message: `Books uploaded! ${result.chunks_indexed} chunks indexed.`, type: 'success' });
        setUploadProgress('');
        setUploading(false);
      }, 500);
    } catch (err) {
      setUploadProgress('');
      setUploading(false);
      setModal({ isOpen: true, title: 'Error', message: 'Failed to upload books: ' + err.message, type: 'error' });
    }
  };

  if (loading) return <div style={{ padding: '20px' }}>Loading...</div>;

  return (
    <div style={{ backgroundColor: 'white', padding: '30px', borderRadius: '8px' }}>
      <Modal
        isOpen={modal.isOpen}
        onClose={() => setModal({ ...modal, isOpen: false })}
        title={modal.title}
        message={modal.message}
        type={modal.type}
      />
      <h2 style={{ marginBottom: '20px' }}>Domain: {domainName}</h2>

      {/* Status Overview */}
      <div style={{ display: 'flex', gap: '20px', marginBottom: '30px' }}>
        <div style={{ flex: 1, padding: '15px', backgroundColor: status?.syllabus_uploaded ? '#d4edda' : '#f8d7da', borderRadius: '4px', border: `1px solid ${status?.syllabus_uploaded ? '#c3e6cb' : '#f5c6cb'}` }}>
          <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>Syllabus</div>
          <div>{status?.syllabus_uploaded ? 'Uploaded' : 'Not uploaded'}</div>
        </div>
        <div style={{ flex: 1, padding: '15px', backgroundColor: status?.books_uploaded ? '#d4edda' : '#f8d7da', borderRadius: '4px', border: `1px solid ${status?.books_uploaded ? '#c3e6cb' : '#f5c6cb'}` }}>
          <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>Books</div>
          <div>{status?.books_uploaded ? `${status.chunks_count} chunks` : 'Not uploaded'}</div>
        </div>
        <div style={{ flex: 1, padding: '15px', backgroundColor: status?.index_ready ? '#d4edda' : '#f8d7da', borderRadius: '4px', border: `1px solid ${status?.index_ready ? '#c3e6cb' : '#f5c6cb'}` }}>
          <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>Status</div>
          <div>{status?.index_ready ? 'Ready' : 'Setup incomplete'}</div>
        </div>
      </div>

      {/* Upload Progress Indicator */}
      {uploading && (
        <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#e7f3ff', border: '1px solid #b3d9ff', borderRadius: '4px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '20px', height: '20px', border: '3px solid #007bff', borderTop: '3px solid transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
            <div style={{ color: '#004085', fontWeight: '500' }}>{uploadProgress}</div>
          </div>
        </div>
      )}

      {/* Upload Sections */}
      {!status?.syllabus_uploaded && (
        <div style={{ marginBottom: '30px' }}>
          <h3 style={{ marginBottom: '15px' }}>Step 1: Upload Syllabus</h3>
          <FileUpload onUpload={handleSyllabusUpload} accept=".pdf,.txt" multiple={false} label="Upload Syllabus (PDF or TXT)" disabled={uploading} />
        </div>
      )}

      {status?.syllabus_uploaded && !status?.books_uploaded && (
        <div style={{ marginBottom: '30px' }}>
          <h3 style={{ marginBottom: '15px' }}>Step 2: Upload Books</h3>
          <FileUpload onUpload={handleBooksUpload} accept=".pdf" multiple={true} label="Upload Books (Multiple PDFs)" disabled={uploading} />
        </div>
      )}

      {status?.index_ready && (
        <div style={{ padding: '20px', backgroundColor: '#d1ecf1', borderRadius: '4px', border: '1px solid #bee5eb' }}>
          <h3 style={{ marginBottom: '10px', color: '#0c5460' }}>Domain Ready for Evaluation</h3>
          <p style={{ marginBottom: '15px', color: '#0c5460' }}>Your domain is fully set up with {status.chunks_count} indexed chunks.</p>
          <button onClick={() => navigate('/evaluate')} style={{ padding: '10px 20px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '16px' }}>
            Go to Evaluation
          </button>
        </div>
      )}
    </div>
  );
}
