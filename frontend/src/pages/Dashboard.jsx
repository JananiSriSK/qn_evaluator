import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api-v2';
import ElicitLayout from '../components/ElicitLayout';
import DomainSetup from '../components/DomainSetup';

export default function Dashboard() {
  const [userId, setUserId] = useState('');
  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newSubjectName, setNewSubjectName] = useState('');
  const [loading, setLoading] = useState(false);
  const [files, setFiles] = useState({ syllabus: false, books: [], papers: [] });
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

  useEffect(() => {
    if (selectedSubject && userId) {
      loadFiles();
    }
  }, [selectedSubject, userId]);

  const loadSubjects = async (id) => {
    try {
      const data = await api.getDomains(id);
      setSubjects(data.domains);
      if (data.domains.length > 0) setSelectedSubject(data.domains[0]);
    } catch (err) {
      console.error('Failed to load subjects:', err);
    }
  };

  const loadFiles = async () => {
    try {
      const status = await api.getDomainStatus(userId, selectedSubject);
      setFiles({
        syllabus: status.syllabus_file || null,
        books: status.books || [],
        papers: status.evaluated_papers || []
      });
    } catch (err) {
      console.error('Failed to load files:', err);
    }
  };

  const handleCreateSubject = async (e) => {
    e.preventDefault();
    if (!newSubjectName.trim()) return;
    setLoading(true);
    try {
      await api.createDomain(userId, newSubjectName.trim());
      await loadSubjects(userId);
      setShowCreateModal(false);
      setNewSubjectName('');
      setSelectedSubject(newSubjectName.trim());
    } catch (err) {
      alert('Failed to create subject: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ElicitLayout selectedSubject={selectedSubject} subjects={subjects} onSubjectChange={setSelectedSubject} userId={userId}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ margin: 0, fontSize: '24px', fontWeight: '600', color: '#1f2937' }}>Subject Setup</h1>
        <button onClick={() => setShowCreateModal(true)} style={{ padding: '10px 20px', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: '500', cursor: 'pointer' }}>
          + Create Subject
        </button>
      </div>

      {selectedSubject ? (
        <>
          {/* Setup Section */}
          <DomainSetup userId={userId} domainName={selectedSubject} />

          {/* Files Section */}
          <div style={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', padding: '24px', marginTop: '24px' }}>
            <h2 style={{ margin: '0 0 20px 0', fontSize: '18px', fontWeight: '600', color: '#1f2937' }}>Uploaded Files</h2>

            {/* Syllabus */}
            <div style={{ marginBottom: '20px' }}>
              <div style={{ fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '8px' }}>Syllabus</div>
              {files.syllabus ? (
                <div style={{ padding: '10px 12px', backgroundColor: '#f0f9ff', border: '1px solid #bfdbfe', borderRadius: '6px', fontSize: '14px', color: '#1e40af' }}>
                  ✓ {files.syllabus}
                </div>
              ) : (
                <div style={{ padding: '10px 12px', backgroundColor: '#fef3c7', border: '1px solid #fbbf24', borderRadius: '6px', fontSize: '14px', color: '#92400e' }}>
                  Not uploaded
                </div>
              )}
            </div>

            {/* Books */}
            <div>
              <div style={{ fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '8px' }}>Reference Books ({files.books.length})</div>
              {files.books.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {files.books.map((book, i) => (
                    <div key={i} style={{ padding: '10px 12px', backgroundColor: '#f0f9ff', border: '1px solid #bfdbfe', borderRadius: '6px', fontSize: '14px', color: '#1e40af' }}>
                      ✓ {book}
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ padding: '10px 12px', backgroundColor: '#fef3c7', border: '1px solid #fbbf24', borderRadius: '6px', fontSize: '14px', color: '#92400e' }}>
                  No books uploaded
                </div>
              )}
            </div>
          </div>
        </>
      ) : (
        <div style={{ textAlign: 'center', padding: '60px', backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
          <h2 style={{ color: '#6b7280', marginBottom: '10px', fontSize: '18px', fontWeight: '500' }}>No Subject Selected</h2>
          <p style={{ color: '#9ca3af', fontSize: '14px' }}>Select a subject from above or create a new one</p>
        </div>
      )}

      {/* Create Subject Modal */}
      {showCreateModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ backgroundColor: 'white', padding: '30px', borderRadius: '8px', width: '400px', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)' }}>
            <h2 style={{ marginBottom: '20px', fontSize: '18px', fontWeight: '600', color: '#1f2937' }}>Create New Subject</h2>
            <form onSubmit={handleCreateSubject}>
              <input
                type="text"
                value={newSubjectName}
                onChange={(e) => setNewSubjectName(e.target.value)}
                placeholder="Subject name (e.g., JAVA_PROGRAMMING)"
                style={{ width: '100%', padding: '10px 12px', border: '1px solid #d1d5db', borderRadius: '6px', marginBottom: '20px', fontSize: '14px' }}
                required
              />
              <div style={{ display: 'flex', gap: '10px' }}>
                <button type="submit" disabled={loading} style={{ flex: 1, padding: '10px', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '6px', cursor: loading ? 'not-allowed' : 'pointer', fontSize: '14px', fontWeight: '500' }}>
                  {loading ? 'Creating...' : 'Create'}
                </button>
                <button type="button" onClick={() => setShowCreateModal(false)} style={{ flex: 1, padding: '10px', backgroundColor: '#f3f4f6', color: '#374151', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '14px', fontWeight: '500' }}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </ElicitLayout>
  );
}
