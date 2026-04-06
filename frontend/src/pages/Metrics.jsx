import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ElicitLayout from '../components/ElicitLayout';
import { api } from '../services/api-v2';

const PLACEHOLDER = `[
  {
    "question": "Explain inheritance in Java",
    "true_topic": "Inheritance",
    "true_bloom": "BT2",
    "true_co": "CO1"
  }
]`;

const BLOOM_COLORS = {
  BT1: '#6b7280', BT2: '#3b82f6', BT3: '#10b981',
  BT4: '#f59e0b', BT5: '#ef4444', BT6: '#8b5cf6',
};

const pct  = v => `${Math.round((v || 0) * 100)}%`;
const sc   = v => v >= 0.8 ? '#16a34a' : v >= 0.6 ? '#d97706' : '#dc2626';
const simc = v => v >= 0.7 ? '#16a34a' : v >= 0.5 ? '#d97706' : '#dc2626';

export default function Metrics() {
  const navigate = useNavigate();
  const [userId, setUserId]           = useState('');
  const [subjects, setSubjects]       = useState([]);
  const [selectedSubject, setSelectedSubject] = useState('');
  const [input, setInput]             = useState(PLACEHOLDER);
  const [r, setR]                     = useState(null);
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState('');

  useEffect(() => {
    const id = localStorage.getItem('user_id');
    if (!id) { navigate('/login'); return; }
    setUserId(id);
    api.getDomains(id).then(d => {
      setSubjects(d.domains || []);
      if (d.domains?.length > 0) setSelectedSubject(d.domains[0]);
    }).catch(() => {});
  }, [navigate]);

  const handleRun = async () => {
    if (!selectedSubject) { setError('Select a subject first'); return; }
    let labeled;
    try { labeled = JSON.parse(input); } catch { setError('Invalid JSON'); return; }
    setError(''); setLoading(true); setR(null);
    try {
      const res = await fetch('http://localhost:8002/metrics/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, domain_name: selectedSubject, labeled_data: labeled }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail?.error || data.error || 'Evaluation failed');
      if (data.error) throw new Error(data.error);
      setR(data);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const details = r?.details || [];

  return (
    <ElicitLayout selectedSubject={selectedSubject} subjects={subjects} onSubjectChange={setSelectedSubject} userId={userId}>
      <h1 style={{ fontSize: '24px', fontWeight: '600', color: '#1f2937', marginBottom: '24px' }}>
        Pipeline Metrics Evaluation
      </h1>

      {/* Input */}
      <div style={{ background: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', padding: '24px', marginBottom: '24px' }}>
        <label style={{ fontSize: '14px', fontWeight: '500', color: '#374151', display: 'block', marginBottom: '8px' }}>
          Labeled Dataset (JSON)
        </label>
        <textarea value={input} onChange={e => setInput(e.target.value)} rows={8}
          style={{ width: '100%', padding: '12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '13px', fontFamily: 'monospace', resize: 'vertical', boxSizing: 'border-box' }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '12px' }}>
          <button onClick={handleRun} disabled={loading}
            style={{ padding: '10px 24px', backgroundColor: loading ? '#9ca3af' : '#3b82f6', color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: '500', cursor: loading ? 'not-allowed' : 'pointer' }}>
            {loading ? 'Running...' : 'Run Evaluation'}
          </button>
          {error && <span style={{ color: '#ef4444', fontSize: '13px' }}>{error}</span>}
        </div>
      </div>

      {r && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

          <p style={{ margin: 0, fontSize: '14px', color: '#6b7280' }}>
            Evaluated <strong style={{ color: '#1f2937' }}>{r.evaluated}</strong> of{' '}
            <strong style={{ color: '#1f2937' }}>{r.total_questions}</strong> questions
            {r.errors?.length > 0 && <span style={{ marginLeft: '12px', color: '#dc2626' }}>⚠ {r.errors.length} failed</span>}
          </p>

          {/* 4 metric cards */}
          <div style={{ background: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', padding: '20px 24px' }}>
            <h2 style={{ fontSize: '15px', fontWeight: '600', color: '#374151', margin: '0 0 16px 0' }}>Accuracy Metrics</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '12px' }}>
              <MetricCard label="Bloom Accuracy" value={r.bloom_accuracy_relaxed} note="±1 relaxed match"
                sub={`${r.bloom_correct ?? 0}/${r.evaluated} correct`} accent />
              <MetricCard label="Topic Accuracy"  value={r.topic_accuracy}         note="cosine ≥ 0.70"
                sub={`${r.topic_correct ?? 0}/${r.evaluated} correct`} />
              <MetricCard label="CO Accuracy"     value={r.co_accuracy}            note="exact match"
                sub={`${r.co_correct ?? 0}/${r.evaluated} correct`} />
              {r.avg_bloom_confidence != null &&
                <MetricCard label="Avg Bloom Confidence" value={r.avg_bloom_confidence}
                  note="model softmax" sub="DeBERTa-v3" raw />}
            </div>
          </div>

          {/* Per-question table */}
          {details.length > 0 && (
            <div style={{ background: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', padding: '20px 24px' }}>
              <h2 style={{ fontSize: '15px', fontWeight: '600', color: '#374151', margin: '0 0 16px 0' }}>Per-Question Breakdown</h2>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#f9fafb' }}>
                      {['#','Question','True BL','Pred BL','BL','True Topic','Pred Topic','Sim','Topic','True CO','Pred CO','CO'].map(h => (
                        <th key={h} style={{ padding: '9px 12px', textAlign: 'left', fontWeight: '600', color: '#374151', borderBottom: '2px solid #e5e7eb', whiteSpace: 'nowrap' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {details.map((row, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid #f3f4f6', backgroundColor: i % 2 === 0 ? 'white' : '#fafafa' }}>
                        <td style={{ padding: '9px 12px', color: '#9ca3af' }}>{i + 1}</td>
                        <td style={{ padding: '9px 12px', color: '#1f2937', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={row.question}>{row.question}</td>
                        <td style={{ padding: '9px 12px' }}><BB level={row.true_bloom} /></td>
                        <td style={{ padding: '9px 12px' }}><BB level={row.pred_bloom} /></td>
                        <td style={{ padding: '9px 12px', textAlign: 'center' }}><Tick ok={row.bloom_correct} /></td>
                        <td style={{ padding: '9px 12px', color: '#6b7280', maxWidth: '110px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={row.true_topic}>{row.true_topic || '—'}</td>
                        <td style={{ padding: '9px 12px', maxWidth: '130px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={row.pred_topic}>
                          <span style={{ color: row.topic_correct ? '#16a34a' : '#dc2626' }}>{row.pred_topic || '—'}</span>
                        </td>
                        <td style={{ padding: '9px 12px', fontWeight: '600', color: simc(row.topic_similarity || 0), whiteSpace: 'nowrap' }}>{(row.topic_similarity || 0).toFixed(2)}</td>
                        <td style={{ padding: '9px 12px', textAlign: 'center' }}><Tick ok={row.topic_correct} /></td>
                        <td style={{ padding: '9px 12px' }}><CB co={row.true_co} /></td>
                        <td style={{ padding: '9px 12px' }}><CB co={row.pred_co} correct={row.co_correct} /></td>
                        <td style={{ padding: '9px 12px', textAlign: 'center' }}><Tick ok={row.co_correct} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p style={{ margin: '12px 0 0', fontSize: '12px', color: '#9ca3af' }}>
                For full diagnostics (confusion matrix, P/R/F1, similarity stats) run: <code>python evaluate_metrics.py --user_id {r.user_id || '<user>'} --domain {'<domain>'} --file labeled.json</code>
              </p>
            </div>
          )}
        </div>
      )}
    </ElicitLayout>
  );
}

function MetricCard({ label, value, note, sub, raw, accent }) {
  const v = value || 0;
  const color = sc(v);
  return (
    <div style={{ padding: '16px', backgroundColor: accent ? '#eff6ff' : '#f9fafb', borderRadius: '8px', border: `1px solid ${accent ? '#bfdbfe' : '#e5e7eb'}` }}>
      <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>{label}</div>
      <div style={{ fontSize: '30px', fontWeight: '700', color, lineHeight: 1 }}>{raw ? v.toFixed(3) : pct(v)}</div>
      {sub && <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '3px' }}>{sub}</div>}
      <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '2px' }}>{note}</div>
      {!raw && <div style={{ marginTop: '8px', height: '4px', backgroundColor: '#e5e7eb', borderRadius: '2px' }}>
        <div style={{ height: '100%', width: `${Math.min(v * 100, 100)}%`, backgroundColor: color, borderRadius: '2px' }} />
      </div>}
    </div>
  );
}

function BB({ level }) {
  return <span style={{ padding: '2px 8px', backgroundColor: BLOOM_COLORS[level] || '#e5e7eb', color: level ? 'white' : '#6b7280', borderRadius: '4px', fontWeight: '600', fontSize: '12px' }}>{level || '—'}</span>;
}
function CB({ co, correct }) {
  const bg   = correct === undefined ? '#ede9fe' : correct ? '#d1fae5' : '#fee2e2';
  const text = correct === undefined ? '#5b21b6'  : correct ? '#065f46' : '#991b1b';
  return <span style={{ padding: '2px 8px', backgroundColor: co ? bg : 'transparent', color: co ? text : '#9ca3af', borderRadius: '4px', fontWeight: '600', fontSize: '12px' }}>{co || '—'}</span>;
}
function Tick({ ok }) {
  return <span style={{ fontSize: '15px', fontWeight: '700', color: ok ? '#16a34a' : '#dc2626' }}>{ok ? '✓' : '✗'}</span>;
}
