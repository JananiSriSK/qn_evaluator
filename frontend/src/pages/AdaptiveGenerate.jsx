import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ElicitLayout from '../components/ElicitLayout';
import { api } from '../services/api-v2';

const BLOOM_COLORS = {
  BT1: '#6b7280', BT2: '#3b82f6', BT3: '#10b981',
  BT4: '#f59e0b', BT5: '#ef4444', BT6: '#8b5cf6'
};

export default function AdaptiveGenerate() {
  const navigate = useNavigate();
  const [userId, setUserId] = useState('');
  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState('');
  const [history, setHistory] = useState([]);
  const [selectedEval, setSelectedEval] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const id = localStorage.getItem('user_id');
    if (!id) { navigate('/login'); return; }
    setUserId(id);
    api.getDomains(id).then(d => {
      setSubjects(d.domains || []);
      if (d.domains?.length > 0) setSelectedSubject(d.domains[0]);
    }).catch(() => {});
    api.getHistory(id).then(h => setHistory(h.pdf_evaluations || [])).catch(() => {});
  }, [navigate]);

  const handleGenerate = async () => {
    if (!selectedSubject) { setError('Select a subject'); return; }
    if (!selectedEval) { setError('Select an evaluated paper'); return; }
    setError(''); setLoading(true); setResult(null);
    try {
      const evalData = await api.getPdfEvaluationResults(userId, selectedEval);
      const results = (evalData.results || []).filter(r => !r.error).map(r => ({
        unit: r.unit,
        bloom_level: r.bloom_level,
        course_outcomes: r.course_outcomes || []
      }));
      const res = await fetch('http://localhost:8002/adaptive/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, domain_name: selectedSubject, results })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed');
      setResult(data);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const domainEvals = history.filter(e => e.domain_name === selectedSubject);

  return (
    <ElicitLayout selectedSubject={selectedSubject} subjects={subjects} onSubjectChange={setSelectedSubject} userId={userId}>
      <h1 style={{ fontSize: '24px', fontWeight: '600', color: '#1f2937', marginBottom: '24px' }}>
        Adaptive Question Generation
      </h1>

      <div style={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', padding: '24px', marginBottom: '24px' }}>
        <label style={{ fontSize: '14px', fontWeight: '500', color: '#374151', display: 'block', marginBottom: '8px' }}>
          Select Evaluated Paper
        </label>
        <select value={selectedEval} onChange={e => setSelectedEval(e.target.value)}
          style={{ width: '100%', padding: '10px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px', marginBottom: '16px' }}>
          <option value=''>-- Select a paper --</option>
          {domainEvals.map(e => (
            <option key={e.id} value={e.id}>{e.filename} ({new Date(e.timestamp).toLocaleDateString()})</option>
          ))}
        </select>
        {domainEvals.length === 0 && (
          <p style={{ fontSize: '13px', color: '#9ca3af', marginBottom: '12px' }}>No evaluated papers found for this subject. Upload and evaluate a PDF first.</p>
        )}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button onClick={handleGenerate} disabled={loading || !selectedEval}
            style={{ padding: '10px 24px', backgroundColor: loading || !selectedEval ? '#9ca3af' : '#8b5cf6', color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: '500', cursor: loading || !selectedEval ? 'not-allowed' : 'pointer' }}>
            {loading ? 'Analysing & Generating...' : 'Detect Gaps & Generate'}
          </button>
          {error && <span style={{ color: '#ef4444', fontSize: '13px' }}>{error}</span>}
        </div>
      </div>

      {result && (
        <>
          {/* Gaps */}
          <div style={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', padding: '24px', marginBottom: '24px' }}>
            <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#1f2937', marginBottom: '16px' }}>
              Detected Gaps ({result.gaps?.length || 0})
            </h2>
            {result.gaps?.length === 0 ? (
              <p style={{ color: '#10b981', fontSize: '14px' }}>✓ No gaps detected — paper has good coverage.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {result.gaps.map((gap, i) => (
                  <div key={i} style={{ padding: '12px 14px', backgroundColor: '#fef3c7', border: '1px solid #fbbf24', borderRadius: '6px', fontSize: '14px', color: '#92400e', display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                    <span style={{ padding: '2px 8px', backgroundColor: '#f59e0b', color: 'white', borderRadius: '4px', fontSize: '11px', fontWeight: '700', whiteSpace: 'nowrap' }}>
                      {typeof gap === 'string' ? 'GAP' : (gap.gap_type || 'GAP')}
                    </span>
                    <div>
                      <div style={{ fontWeight: '600', marginBottom: '2px' }}>
                        {typeof gap === 'string' ? gap : gap.target}
                      </div>
                      <div style={{ fontSize: '13px', color: '#78350f' }}>
                        {typeof gap === 'string' ? '' : gap.reason}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Suggested Questions */}
          {result.suggested_questions?.length > 0 && (
            <div style={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', padding: '24px' }}>
              <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#1f2937', marginBottom: '16px' }}>
                Suggested Questions ({result.suggested_questions.length})
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {result.suggested_questions.map((q, i) => (
                  <div key={i} style={{ padding: '16px', backgroundColor: '#f9fafb', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', gap: '8px', marginBottom: '10px', flexWrap: 'wrap' }}>
                      <span style={{ padding: '2px 10px', backgroundColor: BLOOM_COLORS[q.bloom] || '#6b7280', color: 'white', borderRadius: '4px', fontSize: '12px', fontWeight: '600' }}>
                        {q.bloom}
                      </span>
                      <span style={{ padding: '2px 10px', backgroundColor: '#dbeafe', color: '#1e40af', borderRadius: '4px', fontSize: '12px', fontWeight: '600' }}>
                        Unit {q.unit}
                      </span>
                      {q.co && (
                        <span style={{ padding: '2px 10px', backgroundColor: '#d1fae5', color: '#065f46', borderRadius: '4px', fontSize: '12px', fontWeight: '600' }}>
                          {q.co}
                        </span>
                      )}
                    </div>
                    <p style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#1f2937', lineHeight: '1.6' }}>{q.question}</p>
                    <p style={{ margin: 0, fontSize: '12px', color: '#9ca3af' }}>Addresses: {q.gap_addressed}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </ElicitLayout>
  );
}
