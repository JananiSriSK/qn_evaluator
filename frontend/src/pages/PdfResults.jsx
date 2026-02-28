import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api-v2';
import ElicitLayout from '../components/ElicitLayout';
import ResultsTable from '../components/ResultsTable';

export default function PdfResults() {
  const { evalId } = useParams();
  const navigate = useNavigate();
  const [userId, setUserId] = useState('');
  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState('');
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const id = localStorage.getItem('user_id');
    if (!id) {
      navigate('/login');
      return;
    }
    setUserId(id);
    loadSubjects(id);
    loadEvaluation(id);
  }, [evalId, navigate]);

  const loadSubjects = async (id) => {
    try {
      const data = await api.getDomains(id);
      setSubjects(data.domains || []);
      if (data.domains && data.domains.length > 0) {
        setSelectedSubject(data.domains[0]);
      }
    } catch (err) {
      console.error('Failed to load subjects:', err);
    }
  };

  const loadEvaluation = async (id) => {
    try {
      setLoading(true);
      const data = await api.getPdfEvaluationResults(id, evalId);
      setEvaluation(data);
      if (data.domain_name) {
        setSelectedSubject(data.domain_name);
      }
    } catch (err) {
      console.error('Failed to load evaluation:', err);
      alert('Evaluation not found');
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <ElicitLayout selectedSubject={selectedSubject} subjects={subjects} onSubjectChange={setSelectedSubject} userId={userId}>
        <div style={{ textAlign: 'center', padding: '60px', color: '#6b7280' }}>
          Loading evaluation results...
        </div>
      </ElicitLayout>
    );
  }

  if (!evaluation) {
    return (
      <ElicitLayout selectedSubject={selectedSubject} subjects={subjects} onSubjectChange={setSelectedSubject} userId={userId}>
        <div style={{ textAlign: 'center', padding: '60px', color: '#ef4444' }}>
          Evaluation not found
        </div>
      </ElicitLayout>
    );
  }

  return (
    <ElicitLayout selectedSubject={selectedSubject} subjects={subjects} onSubjectChange={setSelectedSubject} userId={userId}>
      <div style={{ marginBottom: '24px' }}>
        <button 
          onClick={() => navigate('/dashboard')}
          style={{ padding: '8px 16px', backgroundColor: '#f3f4f6', color: '#374151', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: '500', cursor: 'pointer', marginBottom: '16px' }}
        >
          ← Back to Dashboard
        </button>
        <h1 style={{ fontSize: '24px', fontWeight: '600', color: '#1f2937', margin: '0 0 8px 0' }}>
          {evaluation.filename}
        </h1>
        <div style={{ fontSize: '14px', color: '#6b7280' }}>
          Evaluated on {new Date(evaluation.timestamp).toLocaleString()} • {evaluation.domain_name}
        </div>
      </div>

      <ResultsTable 
        data={{ 
          total_questions: evaluation.total_questions, 
          results: evaluation.results 
        }} 
        subjectName={evaluation.domain_name} 
      />
    </ElicitLayout>
  );
}
