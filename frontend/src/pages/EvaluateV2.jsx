import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api-v2';
import ElicitLayout from '../components/ElicitLayout';
import ResultCard from '../components/ResultCard';
import ResultsTable from '../components/ResultsTable';

export default function EvaluateV2() {
  const [userId, setUserId] = useState('');
  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState('');
  const [mode, setMode] = useState('single');
  const [question, setQuestion] = useState('');
  const [pdfFile, setPdfFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const typingTimer = useRef(null);
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
      if (data.domains.length > 0) setSelectedSubject(data.domains[0]);
    } catch (err) {
      console.error('Failed to load subjects:', err);
    }
  };

  const handleQuestionChange = (e) => {
    const value = e.target.value;
    setQuestion(value);
    setPreviewData(null);
    setPreviewLoading(false);

    if (typingTimer.current) clearTimeout(typingTimer.current);

    if (value.length > 5 && selectedSubject && userId) {
      setPreviewLoading(true);
      typingTimer.current = setTimeout(async () => {
        try {
          const response = await fetch('http://localhost:8002/evaluate/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              user_id: userId,
              domain_name: selectedSubject,
              question: value
            })
          });
          const data = await response.json();
          console.log('Preview:', data);
          setPreviewData(data);
          setPreviewLoading(false);
        } catch (err) {
          console.error('Preview failed:', err);
          setPreviewLoading(false);
        }
      }, 400);
    }
  };

  const handleEvaluate = async () => {
    if (!selectedSubject) {
      alert('Please select a subject');
      return;
    }

    if (mode === 'single' && !question.trim()) {
      alert('Please enter a question');
      return;
    }

    if (mode === 'pdf' && !pdfFile) {
      alert('Please select a PDF file');
      return;
    }

    setLoading(true);

    try {
      if (mode === 'single') {
        const data = await api.evaluateQuestion(userId, selectedSubject, question);
        console.log('Result:', data);
        setResult({ type: 'single', data });
      } else {
        const data = await api.evaluatePdf(userId, selectedSubject, pdfFile);
        console.log('Result:', data);
        setResult({ type: 'pdf', data });
      }
    } catch (err) {
      alert('Evaluation failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const getDifficultyColor = (score) => {
    if (score < 40) return '#10b981';
    if (score < 70) return '#f59e0b';
    return '#ef4444';
  };

  const getStrengthColor = (score) => {
    if (score <= 40) return '#9ca3af';
    if (score <= 70) return '#60a5fa';
    return '#1d4ed8';
  };

  return (
    <ElicitLayout selectedSubject={selectedSubject} subjects={subjects} onSubjectChange={setSelectedSubject} userId={userId}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ margin: 0, fontSize: '24px', fontWeight: '600', color: '#1f2937' }}>Evaluate Questions</h1>
        <button onClick={() => navigate('/dashboard')} style={{ padding: '8px 16px', backgroundColor: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px', fontWeight: '500', cursor: 'pointer' }}>
          ← Back to Dashboard
        </button>
      </div>

      {/* Mode Toggle */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
        <button onClick={() => setMode('single')} style={{ padding: '10px 24px', backgroundColor: mode === 'single' ? '#3b82f6' : 'white', color: mode === 'single' ? 'white' : '#6b7280', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px', cursor: 'pointer', fontWeight: '500' }}>
          Single Question
        </button>
        <button onClick={() => setMode('pdf')} style={{ padding: '10px 24px', backgroundColor: mode === 'pdf' ? '#3b82f6' : 'white', color: mode === 'pdf' ? 'white' : '#6b7280', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px', cursor: 'pointer', fontWeight: '500' }}>
          Upload PDF
        </button>
      </div>

      {/* Input Area */}
      <div style={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', padding: '24px', marginBottom: '24px' }}>
        {mode === 'single' ? (
          <>
            <label style={{ display: 'block', marginBottom: '12px', fontSize: '14px', fontWeight: '500', color: '#374151' }}>Enter your question</label>
            <textarea
              value={question}
              onChange={handleQuestionChange}
              placeholder="Type your question here..."
              rows="5"
              style={{ width: '100%', padding: '12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px', fontFamily: 'inherit', resize: 'vertical' }}
            />
            
            {previewLoading && (
              <div style={{ marginTop: '8px', fontSize: '12px', color: '#3b82f6' }}>
                Evaluating question strength...
              </div>
            )}

            {previewData && (
              <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', gap: '24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '12px', color: '#6b7280' }}>Difficulty</span>
                  <div style={{ display: 'flex', gap: '2px' }}>
                    {[1, 2, 3, 4, 5].map((seg) => (
                      <div
                        key={seg}
                        style={{
                          width: '16px',
                          height: '8px',
                          borderRadius: '2px',
                          backgroundColor: seg <= Math.ceil((previewData.difficulty_score * 100) * 5)
                            ? getDifficultyColor(previewData.difficulty_score * 100)
                            : '#e5e7eb'
                        }}
                      />
                    ))}
                  </div>
                  <span style={{ fontSize: '12px', color: '#374151' }}>{Math.round(previewData.difficulty_score * 100)}</span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '12px', color: '#6b7280' }}>Strength</span>
                  <div style={{ width: '96px', height: '8px', backgroundColor: '#e5e7eb', borderRadius: '4px', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${previewData.strength_score * 100}%`,
                        height: '100%',
                        backgroundColor: getStrengthColor(previewData.strength_score * 100)
                      }}
                    />
                  </div>
                  <span style={{ fontSize: '12px', color: '#374151' }}>{Math.round(previewData.strength_score * 100)}</span>
                </div>
              </div>
            )}
          </>
        ) : (
          <>
            <label style={{ display: 'block', marginBottom: '12px', fontSize: '14px', fontWeight: '500', color: '#374151' }}>Upload PDF with questions</label>
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => setPdfFile(e.target.files[0])}
              style={{ display: 'block', marginBottom: '12px', fontSize: '14px' }}
            />
            {pdfFile && (
              <div style={{ padding: '10px 12px', backgroundColor: '#f0f9ff', border: '1px solid #bfdbfe', borderRadius: '6px', fontSize: '14px', color: '#1e40af', marginTop: '12px' }}>
                Selected: {pdfFile.name}
              </div>
            )}
          </>
        )}
        <button onClick={handleEvaluate} disabled={loading} style={{ marginTop: '16px', padding: '12px 24px', backgroundColor: loading ? '#9ca3af' : '#3b82f6', color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: '500', cursor: loading ? 'not-allowed' : 'pointer' }}>
          {loading ? 'Evaluating...' : 'Evaluate'}
        </button>
      </div>

      {/* Results */}
      {result && (
        result.type === 'single' ? (
          <ResultCard data={result.data} />
        ) : (
          <ResultsTable data={result.data} subjectName={selectedSubject} />
        )
      )}
    </ElicitLayout>
  );
}
