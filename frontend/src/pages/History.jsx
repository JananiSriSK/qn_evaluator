import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api-v2';
import ElicitLayout from '../components/ElicitLayout';

export default function History({ userId }) {
  const navigate = useNavigate();
  const [history, setHistory] = useState({ single_questions: [], pdf_evaluations: [] });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('single');
  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState('');

  useEffect(() => {
    if (!userId) {
      navigate('/login');
      return;
    }
    loadSubjects();
    loadHistory();
  }, [userId]);

  const loadSubjects = async () => {
    try {
      const data = await api.getDomains(userId);
      setSubjects(data.domains || []);
      if (data.domains && data.domains.length > 0) {
        setSelectedSubject(data.domains[0]);
      }
    } catch (err) {
      console.error('Failed to load subjects:', err);
    }
  };

  const loadHistory = async () => {
    try {
      setLoading(true);
      const data = await api.getHistory(userId);
      setHistory(data);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSingle = async (questionId) => {
    if (!confirm('Delete this question from history?')) return;
    try {
      await api.deleteSingleQuestion(userId, questionId);
      await loadHistory();
    } catch (err) {
      alert('Failed to delete: ' + err.message);
    }
  };

  const handleDeletePdf = async (evalId) => {
    if (!confirm('Delete this PDF evaluation from history?')) return;
    try {
      await api.deletePdfEvaluation(userId, evalId);
      await loadHistory();
    } catch (err) {
      alert('Failed to delete: ' + err.message);
    }
  };

  const handleClearAll = async () => {
    if (!confirm('Clear all history? This cannot be undone.')) return;
    try {
      await api.clearAllHistory(userId);
      await loadHistory();
    } catch (err) {
      alert('Failed to clear history: ' + err.message);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
        Loading history...
      </div>
    );
  }

  return (
    <ElicitLayout
      selectedSubject={selectedSubject}
      subjects={subjects}
      onSubjectChange={setSelectedSubject}
      userId={userId}
    >
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h1 style={{ fontSize: '28px', fontWeight: '600', color: '#1f2937', margin: 0 }}>
            Evaluation History
          </h1>
          {(history.single_questions.length > 0 || history.pdf_evaluations.length > 0) && (
            <button
              onClick={handleClearAll}
              style={{ padding: '8px 16px', backgroundColor: '#ef4444', color: 'white', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: '500', cursor: 'pointer' }}
            >
              Clear All History
            </button>
          )}
        </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', borderBottom: '2px solid #e5e7eb' }}>
        <button
          onClick={() => setActiveTab('single')}
          style={{
            padding: '12px 24px',
            border: 'none',
            backgroundColor: 'transparent',
            color: activeTab === 'single' ? '#3b82f6' : '#6b7280',
            fontWeight: '500',
            fontSize: '14px',
            cursor: 'pointer',
            borderBottom: activeTab === 'single' ? '2px solid #3b82f6' : 'none',
            marginBottom: '-2px'
          }}
        >
          Single Questions ({history.single_questions.length})
        </button>
        <button
          onClick={() => setActiveTab('pdf')}
          style={{
            padding: '12px 24px',
            border: 'none',
            backgroundColor: 'transparent',
            color: activeTab === 'pdf' ? '#3b82f6' : '#6b7280',
            fontWeight: '500',
            fontSize: '14px',
            cursor: 'pointer',
            borderBottom: activeTab === 'pdf' ? '2px solid #3b82f6' : 'none',
            marginBottom: '-2px'
          }}
        >
          PDF Evaluations ({history.pdf_evaluations.length})
        </button>
      </div>

      {/* Single Questions Tab */}
      {activeTab === 'single' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {history.single_questions.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#9ca3af', backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
              No single question evaluations yet
            </div>
          ) : (
            history.single_questions.map((item) => (
              <div key={item.id} style={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '12px' }}>
                  <div>
                    <span style={{ fontSize: '12px', color: '#6b7280' }}>
                      {new Date(item.timestamp).toLocaleString()}
                    </span>
                    <span style={{ marginLeft: '12px', padding: '2px 8px', backgroundColor: '#dbeafe', color: '#1e40af', borderRadius: '4px', fontSize: '11px', fontWeight: '600' }}>
                      {item.domain_name}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    {item.out_of_syllabus && (
                      <span style={{ padding: '4px 10px', backgroundColor: '#fef3c7', color: '#92400e', borderRadius: '4px', fontSize: '11px', fontWeight: '600' }}>
                        OUT OF SYLLABUS
                      </span>
                    )}
                    <button
                      onClick={() => handleDeleteSingle(item.id)}
                      style={{ padding: '4px 8px', backgroundColor: '#fee2e2', color: '#991b1b', border: 'none', borderRadius: '4px', fontSize: '11px', fontWeight: '600', cursor: 'pointer' }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
                <p style={{ margin: '0 0 12px 0', color: '#1f2937', fontSize: '14px', lineHeight: '1.6' }}>
                  {item.question}
                </p>
                <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', fontSize: '13px' }}>
                  {item.unit && (
                    <div>
                      <span style={{ color: '#6b7280' }}>Unit: </span>
                      <span style={{ color: '#1f2937', fontWeight: '500' }}>{item.unit} - {item.unit_title}</span>
                    </div>
                  )}
                  {item.topic && (
                    <div>
                      <span style={{ color: '#6b7280' }}>Topic: </span>
                      <span style={{ color: '#1f2937', fontWeight: '500' }}>{item.topic}</span>
                    </div>
                  )}
                  {item.bloom_level && (
                    <div>
                      <span style={{ color: '#6b7280' }}>Bloom: </span>
                      <span style={{ padding: '2px 8px', backgroundColor: getBloomColor(item.bloom_level), color: 'white', borderRadius: '4px', fontSize: '11px', fontWeight: '600' }}>
                        {item.bloom_level}
                      </span>
                    </div>
                  )}
                  {item.course_outcomes && item.course_outcomes.length > 0 && (
                    <div>
                      <span style={{ color: '#6b7280' }}>CO: </span>
                      <span style={{ color: '#1f2937', fontWeight: '500' }}>{item.course_outcomes.join(', ')}</span>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* PDF Evaluations Tab */}
      {activeTab === 'pdf' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {history.pdf_evaluations.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#9ca3af', backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
              No PDF evaluations yet
            </div>
          ) : (
            history.pdf_evaluations.map((item) => (
              <div key={item.id} style={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: '14px', fontWeight: '600', color: '#1f2937', marginBottom: '4px' }}>
                      {item.filename}
                    </div>
                    <div style={{ fontSize: '12px', color: '#6b7280' }}>
                      {new Date(item.timestamp).toLocaleString()}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span style={{ padding: '4px 10px', backgroundColor: '#dbeafe', color: '#1e40af', borderRadius: '4px', fontSize: '11px', fontWeight: '600' }}>
                      {item.domain_name}
                    </span>
                    <span style={{ padding: '4px 10px', backgroundColor: '#f3f4f6', color: '#374151', borderRadius: '4px', fontSize: '11px', fontWeight: '600' }}>
                      {item.total_questions} questions
                    </span>
                    <button
                      onClick={() => navigate(`/results/${item.id}`)}
                      style={{ padding: '4px 12px', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px', fontSize: '11px', fontWeight: '600', cursor: 'pointer' }}
                    >
                      View Results
                    </button>
                    <button
                      onClick={() => handleDeletePdf(item.id)}
                      style={{ padding: '4px 8px', backgroundColor: '#fee2e2', color: '#991b1b', border: 'none', borderRadius: '4px', fontSize: '11px', fontWeight: '600', cursor: 'pointer' }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
    </ElicitLayout>
  );
}

function getBloomColor(level) {
  const colors = {
    BT1: '#6b7280', BT2: '#3b82f6', BT3: '#10b981',
    BT4: '#f59e0b', BT5: '#ef4444', BT6: '#8b5cf6'
  };
  return colors[level] || '#6b7280';
}
