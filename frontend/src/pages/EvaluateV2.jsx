import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api-v2';
import ElicitLayout from '../components/ElicitLayout';
import ResultCard from '../components/ResultCard';
import ResultsTable from '../components/ResultsTable';
import SuggestedChanges from '../components/SuggestedChanges';

const BLOOM_COLORS = {
  BT1: '#6b7280', BT2: '#3b82f6', BT3: '#10b981',
  BT4: '#f59e0b', BT5: '#ef4444', BT6: '#8b5cf6',
};

export default function EvaluateV2() {
  const navigate   = useNavigate();
  const typingTimer = useRef(null);

  const [userId, setUserId]                   = useState('');
  const [subjects, setSubjects]               = useState([]);
  const [selectedSubject, setSelectedSubject] = useState('');

  // left nav: 'single' | 'paper'
  const [mode, setMode]       = useState('single');
  // inner tab for paper mode: 'evaluation' | 'suggested'
  const [paperTab, setPaperTab] = useState('evaluation');

  // single question state
  const [question, setQuestion]         = useState('');
  const [previewData, setPreviewData]   = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [singleResult, setSingleResult] = useState(null);

  // paper state
  const [pdfFile, setPdfFile]       = useState(null);
  const [pdfResult, setPdfResult]   = useState(null);   // original evaluated results
  const [revisedResult, setRevisedResult] = useState(null); // after finalising suggestions
  const [adaptive, setAdaptive]     = useState(null);
  const [adaptiveLoading, setAdaptiveLoading] = useState(false);

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const id = localStorage.getItem('user_id');
    if (!id) { navigate('/login'); return; }
    setUserId(id);
    api.getDomains(id).then(d => {
      setSubjects(d.domains || []);
      if (d.domains?.length > 0) setSelectedSubject(d.domains[0]);
    }).catch(() => {});
  }, [navigate]);

  // ── Single question handlers ──────────────────────────────────────────────

  const handleQuestionChange = (e) => {
    const value = e.target.value;
    setQuestion(value);
    setPreviewData(null);
    if (typingTimer.current) clearTimeout(typingTimer.current);
    if (value.length > 5 && selectedSubject && userId) {
      setPreviewLoading(true);
      typingTimer.current = setTimeout(async () => {
        try {
          const res = await fetch('http://localhost:8002/evaluate/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, domain_name: selectedSubject, question: value }),
          });
          setPreviewData(await res.json());
        } catch { /* ignore */ }
        finally { setPreviewLoading(false); }
      }, 400);
    }
  };

  const handleEvaluateSingle = async () => {
    if (!selectedSubject || !question.trim()) return;
    setLoading(true);
    try {
      const data = await api.evaluateQuestion(userId, selectedSubject, question);
      setSingleResult(data);
    } catch (err) { alert('Evaluation failed: ' + err.message); }
    finally { setLoading(false); }
  };

  // ── Paper handlers ────────────────────────────────────────────────────────

  const handleEvaluatePdf = async () => {
    if (!selectedSubject || !pdfFile) return;
    setLoading(true);
    setPdfResult(null); setRevisedResult(null); setAdaptive(null);
    try {
      const data = await api.evaluatePdf(userId, selectedSubject, pdfFile);
      setPdfResult(data);
      setPaperTab('evaluation');
    } catch (err) { alert('Evaluation failed: ' + err.message); }
    finally { setLoading(false); }
  };

  const handleLoadSuggestions = async () => {
    if (!pdfResult) return;
    setPaperTab('suggested');
    if (adaptive) return; // already loaded
    setAdaptiveLoading(true);
    try {
      const payload = (pdfResult.results || [])
        .filter(r => !r.error)
        .map(r => ({ unit: r.unit, bloom_level: r.bloom_level, course_outcomes: r.course_outcomes || [] }));
      const res = await fetch('http://localhost:8002/adaptive/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, domain_name: selectedSubject, results: payload }),
      });
      const d = await res.json();
      if (!res.ok) throw new Error(d.error || 'Failed');
      setAdaptive(d);
    } catch (e) { alert('Could not load suggestions: ' + e.message); }
    finally { setAdaptiveLoading(false); }
  };

  // Called from SuggestedChanges when user clicks "Apply Replacements"
  const handleFinalise = (replacements) => {
    if (!pdfResult) return;
    const updatedResults = (pdfResult.results || []).map((r, idx) => {
      const rep = replacements[idx];
      if (!rep) return r;
      return {
        ...r,
        question:        rep.newQuestion,
        bloom_level:     rep.bloom,
        course_outcomes: rep.co ? [rep.co] : r.course_outcomes,
        unit:            rep.unit || r.unit,
        _original:       rep.originalQuestion,
        _suggested:      true,
      };
    });
    setRevisedResult({
      ...pdfResult,
      results: updatedResults,
    });
    setPaperTab('evaluation');
  };

  const activeData = revisedResult || pdfResult;

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <ElicitLayout selectedSubject={selectedSubject} subjects={subjects} onSubjectChange={setSelectedSubject} userId={userId}>

      {/* Left sub-nav */}
      <div style={{ display: 'flex', gap: '0', marginBottom: '24px', borderBottom: '2px solid #e5e7eb' }}>
        {[
          { id: 'single', label: 'Single Question' },
          { id: 'paper',  label: 'Question Paper'  },
        ].map(item => (
          <button key={item.id} onClick={() => setMode(item.id)}
            style={{
              padding: '10px 28px', border: 'none', cursor: 'pointer', fontSize: '14px', fontWeight: mode === item.id ? '600' : '400',
              color: mode === item.id ? '#1e40af' : '#6b7280',
              backgroundColor: 'transparent',
              borderBottom: mode === item.id ? '2px solid #3b82f6' : '2px solid transparent',
              marginBottom: '-2px',
            }}>
            {item.label}
          </button>
        ))}
      </div>

      {/* ── SINGLE QUESTION ── */}
      {mode === 'single' && (
        <>
          <div style={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', padding: '24px', marginBottom: '24px' }}>
            <label style={{ display: 'block', marginBottom: '12px', fontSize: '14px', fontWeight: '500', color: '#374151' }}>Enter your question</label>
            <textarea value={question} onChange={handleQuestionChange} placeholder="Type your question here..." rows={5}
              style={{ width: '100%', padding: '12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '14px', fontFamily: 'inherit', resize: 'vertical', boxSizing: 'border-box' }} />

            {previewLoading && <div style={{ marginTop: '8px', fontSize: '12px', color: '#3b82f6' }}>Analysing...</div>}
            {previewData && <PreviewBar data={previewData} />}

            <button onClick={handleEvaluateSingle} disabled={loading || !question.trim()}
              style={{ marginTop: '16px', padding: '10px 24px', backgroundColor: loading ? '#9ca3af' : '#3b82f6', color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: '500', cursor: loading ? 'not-allowed' : 'pointer' }}>
              {loading ? 'Evaluating...' : 'Evaluate'}
            </button>
          </div>
          {singleResult && <ResultCard data={singleResult} />}
        </>
      )}

      {/* ── QUESTION PAPER ── */}
      {mode === 'paper' && (
        <>
          {/* Upload bar — always visible */}
          <div style={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', padding: '20px 24px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
            <input type="file" accept=".pdf" onChange={e => { setPdfFile(e.target.files[0]); setPdfResult(null); setRevisedResult(null); setAdaptive(null); }}
              style={{ fontSize: '14px' }} />
            {pdfFile && <span style={{ fontSize: '13px', color: '#1e40af' }}>{pdfFile.name}</span>}
            <button onClick={handleEvaluatePdf} disabled={loading || !pdfFile}
              style={{ padding: '9px 22px', backgroundColor: loading || !pdfFile ? '#9ca3af' : '#3b82f6', color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: '500', cursor: loading || !pdfFile ? 'not-allowed' : 'pointer' }}>
              {loading ? 'Evaluating...' : 'Evaluate Paper'}
            </button>
          </div>

          {/* Inner tabs — only show after evaluation */}
          {activeData && (
            <>
              <div style={{ display: 'flex', gap: '0', marginBottom: '0', borderBottom: '2px solid #e5e7eb' }}>
                <InnerTab label="Evaluation" active={paperTab === 'evaluation'} onClick={() => setPaperTab('evaluation')}
                  badge={revisedResult ? 'Updated' : null} />
                <InnerTab label="Suggested Changes" active={paperTab === 'suggested'} onClick={handleLoadSuggestions}
                  badge={adaptive ? `${(adaptive.gaps?.length || 0)} gaps` : null} />
              </div>

              <div style={{ backgroundColor: 'white', borderRadius: '0 0 8px 8px', border: '1px solid #e5e7eb', borderTop: 'none' }}>
                {paperTab === 'evaluation' && (
                  <div style={{ padding: '0' }}>
                    {revisedResult && (
                      <div style={{ padding: '12px 24px', backgroundColor: '#f0fdf4', borderBottom: '1px solid #bbf7d0', fontSize: '13px', color: '#065f46', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        ✓ {revisedResult.results.filter(r => r._suggested).length} question(s) replaced in the paper.
                        <button onClick={() => { setRevisedResult(null); }} style={{ marginLeft: 'auto', fontSize: '12px', color: '#6b7280', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}>
                          Revert to original
                        </button>
                      </div>
                    )}
                    <ResultsTable data={activeData} subjectName={selectedSubject} userId={userId} hideAdaptive />
                  </div>
                )}

                {paperTab === 'suggested' && (
                  <div style={{ padding: '24px' }}>
                    {adaptiveLoading ? (
                      <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280', fontSize: '14px' }}>
                        Analysing paper and generating suggestions...
                      </div>
                    ) : adaptive ? (
                      <SuggestedChanges
                        adaptive={adaptive}
                        results={pdfResult?.results || []}
                        userId={userId}
                        subjectName={selectedSubject}
                        onFinalise={handleFinalise}
                      />
                    ) : null}
                  </div>
                )}
              </div>
            </>
          )}
        </>
      )}
    </ElicitLayout>
  );
}

function InnerTab({ label, active, onClick, badge }) {
  return (
    <button onClick={onClick} style={{
      padding: '10px 24px', border: 'none', cursor: 'pointer', fontSize: '14px',
      fontWeight: active ? '600' : '400',
      color: active ? '#1e40af' : '#6b7280',
      backgroundColor: 'transparent',
      borderBottom: active ? '2px solid #3b82f6' : '2px solid transparent',
      marginBottom: '-2px', display: 'flex', alignItems: 'center', gap: '8px',
    }}>
      {label}
      {badge && (
        <span style={{ padding: '1px 7px', backgroundColor: active ? '#dbeafe' : '#f3f4f6', color: active ? '#1e40af' : '#6b7280', borderRadius: '10px', fontSize: '11px', fontWeight: '600' }}>
          {badge}
        </span>
      )}
    </button>
  );
}

function PreviewBar({ data }) {
  const diff = Math.round((data.difficulty_score || 0) * 100);
  const str  = Math.round((data.strength_score  || 0) * 100);
  const diffColor = diff < 40 ? '#10b981' : diff < 70 ? '#f59e0b' : '#ef4444';
  const strColor  = str  <= 40 ? '#9ca3af' : str  <= 70 ? '#60a5fa' : '#1d4ed8';
  return (
    <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', gap: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '12px', color: '#6b7280' }}>Difficulty</span>
        <div style={{ display: 'flex', gap: '2px' }}>
          {[1,2,3,4,5].map(s => (
            <div key={s} style={{ width: '16px', height: '8px', borderRadius: '2px', backgroundColor: s <= Math.ceil(diff / 20) ? diffColor : '#e5e7eb' }} />
          ))}
        </div>
        <span style={{ fontSize: '12px', color: '#374151' }}>{diff}</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '12px', color: '#6b7280' }}>Strength</span>
        <div style={{ width: '96px', height: '8px', backgroundColor: '#e5e7eb', borderRadius: '4px', overflow: 'hidden' }}>
          <div style={{ width: `${str}%`, height: '100%', backgroundColor: strColor }} />
        </div>
        <span style={{ fontSize: '12px', color: '#374151' }}>{str}</span>
      </div>
    </div>
  );
}
