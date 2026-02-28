import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api-v2';
import ElicitLayout from '../components/ElicitLayout';

export default function ManageSubjects() {
  const [userId, setUserId] = useState('');
  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState('');
  const [subjectStatus, setSubjectStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [viewingSyllabus, setViewingSyllabus] = useState(false);
  const [syllabusData, setSyllabusData] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const id = localStorage.getItem('user_id');
    if (!id) {
      navigate('/login');
      return;
    }
    setUserId(id);
    loadSubjects(id);
  }, [navigate]);

  const loadSubjects = async (id) => {
    try {
      const data = await api.getDomains(id);
      setSubjects(data.domains);
      if (data.domains.length > 0) {
        setSelectedSubject(data.domains[0]);
        loadSubjectStatus(id, data.domains[0]);
      }
    } catch (err) {
      console.error('Failed to load subjects:', err);
    }
  };

  const loadSubjectStatus = async (uid, domain) => {
    try {
      const status = await api.getDomainStatus(uid, domain);
      setSubjectStatus(status);
    } catch (err) {
      console.error('Failed to load status:', err);
    }
  };

  const handleSubjectChange = (domain) => {
    setSelectedSubject(domain);
    loadSubjectStatus(userId, domain);
  };

  const handleDeleteSyllabus = async () => {
    if (!confirm('Delete syllabus? This will remove the syllabus file.')) return;
    
    setLoading(true);
    try {
      await fetch(`http://localhost:8002/domains/${userId}/${selectedSubject}/syllabus`, {
        method: 'DELETE'
      });
      alert('Syllabus deleted');
      loadSubjectStatus(userId, selectedSubject);
    } catch (err) {
      alert('Failed to delete syllabus');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteBook = async (bookName) => {
    if (!confirm(`Delete book: ${bookName}?`)) return;
    
    setLoading(true);
    try {
      await fetch(`http://localhost:8002/domains/${userId}/${selectedSubject}/books/${encodeURIComponent(bookName)}`, {
        method: 'DELETE'
      });
      alert('Book deleted');
      loadSubjectStatus(userId, selectedSubject);
    } catch (err) {
      alert('Failed to delete book');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSubject = async () => {
    if (!confirm(`Delete entire subject: ${selectedSubject}? This cannot be undone.`)) return;
    
    setLoading(true);
    try {
      await api.deleteDomain(userId, selectedSubject);
      alert('Subject deleted');
      setSelectedSubject('');
      setSubjectStatus(null);
      loadSubjects(userId);
    } catch (err) {
      alert('Failed to delete subject');
    } finally {
      setLoading(false);
    }
  };

  const handleReplaceSyllabus = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setLoading(true);
    try {
      const response = await api.uploadSyllabus(userId, selectedSubject, file);
      if (response.index_rebuilt) {
        alert('Syllabus replaced and FAISS index rebuilt successfully');
      } else {
        alert('Syllabus replaced successfully');
      }
      loadSubjectStatus(userId, selectedSubject);
    } catch (err) {
      alert('Failed to replace syllabus');
    } finally {
      setLoading(false);
    }
  };

  const handleAddBooks = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    setLoading(true);
    try {
      await api.uploadBooks(userId, selectedSubject, files);
      alert('Books added successfully');
      loadSubjectStatus(userId, selectedSubject);
    } catch (err) {
      alert('Failed to add books');
    } finally {
      setLoading(false);
    }
  };

  const handleRebuildIndex = async () => {
    if (!confirm('Rebuild FAISS index? This will reprocess all books with current syllabus.')) return;
    
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8002/domains/${userId}/${selectedSubject}/rebuild`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      
      if (response.ok) {
        alert(`Index rebuilt: ${data.chunks_indexed} chunks indexed`);
        loadSubjectStatus(userId, selectedSubject);
      } else {
        alert(data.detail?.error || 'Failed to rebuild index');
      }
    } catch (err) {
      console.error('Rebuild error:', err);
      alert('Failed to rebuild index');
    } finally {
      setLoading(false);
    }
  };

  const handleViewSyllabus = async () => {
    try {
      const response = await fetch(`http://localhost:8002/domains/${userId}/${selectedSubject}/syllabus/view`);
      const data = await response.json();
      setSyllabusData(data);
      setViewingSyllabus(true);
    } catch (err) {
      alert('Failed to load syllabus');
    }
  };

  return (
    <ElicitLayout selectedSubject={selectedSubject} subjects={subjects} onSubjectChange={handleSubjectChange} userId={userId}>
      {viewingSyllabus ? (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
            <h1 style={{ margin: 0, fontSize: '24px', fontWeight: '600', color: '#1f2937' }}>View Syllabus</h1>
            <button onClick={() => setViewingSyllabus(false)} style={{ padding: '8px 16px', backgroundColor: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px', fontWeight: '500', cursor: 'pointer' }}>
              ← Back
            </button>
          </div>
          <div style={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', padding: '24px' }}>
            <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '16px' }}>{syllabusData?.course_name}</h2>
            
            <div style={{ marginBottom: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px' }}>Course Outcomes</h3>
              {Object.entries(syllabusData?.course_outcomes || {}).map(([co, desc]) => (
                <div key={co} style={{ marginBottom: '8px', padding: '12px', backgroundColor: '#f9fafb', borderRadius: '6px' }}>
                  <span style={{ fontWeight: '600', color: '#3b82f6' }}>{co}:</span> {desc}
                </div>
              ))}
            </div>
            
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px' }}>Units</h3>
              {syllabusData?.units?.map((unit) => (
                <div key={unit.unit_number} style={{ marginBottom: '16px', padding: '16px', backgroundColor: '#f9fafb', borderRadius: '6px', border: '1px solid #e5e7eb' }}>
                  <h4 style={{ fontSize: '15px', fontWeight: '600', marginBottom: '8px' }}>Unit {unit.unit_number}: {unit.unit_title}</h4>
                  <ul style={{ margin: 0, paddingLeft: '20px' }}>
                    {unit.topics?.map((topic, idx) => (
                      <li key={idx} style={{ marginBottom: '4px', fontSize: '14px', color: '#374151' }}>{topic.topic_name}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ margin: 0, fontSize: '24px', fontWeight: '600', color: '#1f2937' }}>Manage Subjects</h1>
        <button onClick={() => navigate('/dashboard')} style={{ padding: '8px 16px', backgroundColor: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px', fontWeight: '500', cursor: 'pointer' }}>
          ← Back to Dashboard
        </button>
      </div>

      {!selectedSubject ? (
        <div style={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', padding: '48px', textAlign: 'center' }}>
          <p style={{ color: '#6b7280', fontSize: '16px' }}>No subjects available. Create one from Dashboard.</p>
        </div>
      ) : (
        <>
          {/* Syllabus Section */}
          <div style={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', padding: '24px', marginBottom: '20px' }}>
            <h2 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: '600', color: '#1f2937' }}>Syllabus</h2>
            
            {subjectStatus?.syllabus_uploaded ? (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                  <span style={{ padding: '4px 12px', backgroundColor: '#d1fae5', color: '#065f46', borderRadius: '6px', fontSize: '13px', fontWeight: '500' }}>
                    ✓ Uploaded
                  </span>
                  <span style={{ color: '#6b7280', fontSize: '14px' }}>{subjectStatus.syllabus_file}</span>
                </div>
                
                <div style={{ display: 'flex', gap: '12px' }}>
                  <label style={{ padding: '8px 16px', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: '500', cursor: 'pointer' }}>
                    Replace Syllabus
                    <input type="file" accept=".pdf,.txt" onChange={handleReplaceSyllabus} style={{ display: 'none' }} disabled={loading} />
                  </label>
                  <a href={`http://localhost:8002/domains/${userId}/${selectedSubject}/files/syllabus`} target="_blank" rel="noopener noreferrer" style={{ padding: '8px 16px', backgroundColor: '#10b981', color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: '500', textDecoration: 'none', display: 'inline-block' }}>
                    📄 Open File
                  </a>
                  <button onClick={handleDeleteSyllabus} disabled={loading} style={{ padding: '8px 16px', backgroundColor: '#ef4444', color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: '500', cursor: loading ? 'not-allowed' : 'pointer' }}>
                    Delete Syllabus
                  </button>
                </div>
              </div>
            ) : (
              <div>
                <p style={{ color: '#6b7280', fontSize: '14px', marginBottom: '12px' }}>No syllabus uploaded</p>
                <label style={{ padding: '8px 16px', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: '500', cursor: 'pointer' }}>
                  Upload Syllabus
                  <input type="file" accept=".pdf,.txt" onChange={handleReplaceSyllabus} style={{ display: 'none' }} disabled={loading} />
                </label>
              </div>
            )}
          </div>

          {/* Books Section */}
          <div style={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', padding: '24px', marginBottom: '20px' }}>
            <h2 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: '600', color: '#1f2937' }}>Reference Books</h2>
            
            {subjectStatus?.books_uploaded && subjectStatus.books.length > 0 ? (
              <div>
                <div style={{ marginBottom: '16px' }}>
                  <p style={{ color: '#6b7280', fontSize: '14px', marginBottom: '12px' }}>
                    {subjectStatus.books.length} book(s) • {subjectStatus.chunks_count} chunks indexed
                  </p>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {subjectStatus.books.map((book, idx) => (
                      <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', backgroundColor: '#f9fafb', borderRadius: '6px', border: '1px solid #e5e7eb' }}>
                        <a href={`http://localhost:8002/domains/${userId}/${selectedSubject}/files/books/${encodeURIComponent(book)}`} target="_blank" rel="noopener noreferrer" style={{ fontSize: '14px', color: '#3b82f6', textDecoration: 'none' }}>
                          📖 {book}
                        </a>
                        <button onClick={() => handleDeleteBook(book)} disabled={loading} style={{ padding: '4px 12px', backgroundColor: '#ef4444', color: 'white', border: 'none', borderRadius: '4px', fontSize: '12px', cursor: loading ? 'not-allowed' : 'pointer' }}>
                          Delete
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div style={{ display: 'flex', gap: '12px' }}>
                  <label style={{ padding: '8px 16px', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: '500', cursor: 'pointer' }}>
                    Add More Books
                    <input type="file" accept=".pdf" multiple onChange={handleAddBooks} style={{ display: 'none' }} disabled={loading} />
                  </label>
                  <button onClick={handleRebuildIndex} disabled={loading} style={{ padding: '8px 16px', backgroundColor: '#10b981', color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: '500', cursor: loading ? 'not-allowed' : 'pointer' }}>
                    🔄 Rebuild Index
                  </button>
                </div>
              </div>
            ) : (
              <div>
                <p style={{ color: '#6b7280', fontSize: '14px', marginBottom: '12px' }}>No books uploaded</p>
                <label style={{ padding: '8px 16px', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: '500', cursor: 'pointer' }}>
                  Upload Books
                  <input type="file" accept=".pdf" multiple onChange={handleAddBooks} style={{ display: 'none' }} disabled={loading} />
                </label>
              </div>
            )}
          </div>

          {/* Delete Subject Section */}
          <div style={{ backgroundColor: '#fef2f2', borderRadius: '8px', border: '1px solid #fecaca', padding: '24px' }}>
            <h2 style={{ margin: '0 0 12px 0', fontSize: '18px', fontWeight: '600', color: '#991b1b' }}>Danger Zone</h2>
            <p style={{ color: '#6b7280', fontSize: '14px', marginBottom: '16px' }}>
              Delete this subject permanently. This will remove all syllabus, books, and evaluation history.
            </p>
            <button onClick={handleDeleteSubject} disabled={loading} style={{ padding: '10px 20px', backgroundColor: '#dc2626', color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: '500', cursor: loading ? 'not-allowed' : 'pointer' }}>
              Delete Subject: {selectedSubject}
            </button>
          </div>
        </>
      )}
      </div>
      )}
    </ElicitLayout>
  );
}
