import { useState } from 'react';

const BLOOM_COLORS = {
  BT1: '#6b7280', BT2: '#3b82f6', BT3: '#10b981',
  BT4: '#f59e0b', BT5: '#ef4444', BT6: '#8b5cf6'
};

export default function ResultsTable({ data, subjectName, userId, hideAdaptive }) {
  const [downloading, setDownloading] = useState(false);
  const [reportType, setReportType] = useState('mapping');
  const [adaptive, setAdaptive] = useState(null);
  const [adaptiveLoading, setAdaptiveLoading] = useState(false);
  const [adaptiveError, setAdaptiveError] = useState('');
  const [showMeta, setShowMeta] = useState(false);
  const [meta, setMeta] = useState({
    programme: 'MCA (R & SS)',
    max_marks: 50,
    date: new Date().toLocaleDateString('en-GB').replace(/\//g, '/'),
    semester: 'I / III Sem',
    regulation: '2023',
    duration: '1 hour 30 mins',
    course_code: '',
    course_title: subjectName || '',
    assessment: 'Assessment Test – I',
  });
  const results = data.results || [];

  // Group by part
  const groupedByPart = results.reduce((acc, r) => {
    const part = r.part || 'Part A';
    if (!acc[part]) acc[part] = [];
    acc[part].push(r);
    return acc;
  }, {});

  const parts = ['Part A', 'Part B', 'Part C'].filter(p => groupedByPart[p]);

  const handleDownload = async (format) => {
    setDownloading(true);
    try {
      // Always fetch ALL COs from syllabus
      let cosWithDesc = [];
      try {
        const sRes = await fetch(`http://localhost:8002/domains/${userId}/${subjectName}/syllabus/view`);
        if (sRes.ok) {
          const syl = await sRes.json();
          const coMap = syl.course_outcomes || {};
          cosWithDesc = Object.entries(coMap)
            .sort(([a], [b]) => a.localeCompare(b, undefined, { numeric: true }))
            .map(([id, text]) => ({ id, text }));
        }
      } catch { /* fallback below */ }
      if (cosWithDesc.length === 0) {
        const coSet = new Set();
        results.forEach(r => (r.course_outcomes || []).forEach(co => coSet.add(co)));
        cosWithDesc = [...coSet].sort().map(id => ({ id, text: '' }));
      }

      // Always send cover page meta (use defaults if form not opened)
      const metaPayload = {
        ...meta,
        max_marks: Number(meta.max_marks),
        cos: cosWithDesc,
      };

      const response = await fetch('http://localhost:8002/report/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          domain_name: subjectName,
          results: results.map(r => ({
            question_number: r.question_number,
            part: r.part,
            question: r.question,
            course_outcomes: r.course_outcomes,
            bloom_level: r.bloom_level,
          })),
          format,
          type: reportType,
          meta: metaPayload,
        }),
      });

      if (!response.ok) throw new Error('Download failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${subjectName}_${meta.assessment || 'Assessment'}_question_paper.${format}`.replace(/\s+/g, '_');
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      alert('Download failed: ' + err.message);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div style={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2 style={{ margin: 0, fontSize: '18px', fontWeight: '600', color: '#1f2937' }}>
          Results ({data.total_questions} questions)
        </h2>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <select value={reportType} onChange={(e) => setReportType(e.target.value)} style={{ padding: '8px 12px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '13px', color: '#374151', backgroundColor: 'white', cursor: 'pointer' }}>
            <option value="mapping">Mapping Only (Q.No, CO, BL)</option>
            <option value="question_paper">With Questions (Q.No, Question, CO, BL)</option>
          </select>
          <button onClick={() => handleDownload('pdf')} disabled={downloading} style={{ padding: '8px 16px', backgroundColor: '#ef4444', color: 'white', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: '500', cursor: downloading ? 'not-allowed' : 'pointer' }}>
            Download PDF
          </button>
          <button onClick={() => handleDownload('docx')} disabled={downloading} style={{ padding: '8px 16px', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: '500', cursor: downloading ? 'not-allowed' : 'pointer' }}>
            Download DOCX
          </button>
        </div>
      </div>

      {/* Paper details form */}
      <div style={{ marginBottom: '20px' }}>
        <button onClick={() => setShowMeta(v => !v)}
          style={{ fontSize: '13px', color: '#3b82f6', background: 'none', border: 'none', cursor: 'pointer', padding: 0, textDecoration: 'underline' }}>
          {showMeta ? '▲ Hide paper details (cover page)' : '▼ Add paper details for cover page'}
        </button>
        {showMeta && (
          <div style={{ marginTop: '12px', padding: '16px', backgroundColor: '#f9fafb', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
            <div style={{ fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '12px' }}>Anna University Cover Page Details</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
              {[
                { key: 'assessment',  label: 'Assessment' },
                { key: 'programme',   label: 'Programme' },
                { key: 'course_code', label: 'Course Code' },
                { key: 'course_title',label: 'Course Title' },
                { key: 'date',        label: 'Date of Exam' },
                { key: 'semester',    label: 'Year / Semester' },
                { key: 'regulation',  label: 'Regulation' },
                { key: 'duration',    label: 'Duration' },
                { key: 'max_marks',   label: 'Max Marks' },
              ].map(({ key, label }) => (
                <div key={key}>
                  <label style={{ fontSize: '11px', color: '#6b7280', display: 'block', marginBottom: '3px' }}>{label}</label>
                  <input
                    value={meta[key]}
                    onChange={e => setMeta(prev => ({ ...prev, [key]: e.target.value }))}
                    style={{ width: '100%', padding: '6px 8px', border: '1px solid #d1d5db', borderRadius: '4px', fontSize: '13px', boxSizing: 'border-box' }}
                  />
                </div>
              ))}
            </div>
            <div style={{ marginTop: '8px', fontSize: '12px', color: '#9ca3af' }}>
              CO descriptions will be auto-populated from the evaluated results.
            </div>
          </div>
        )}
      </div>

      {/* Tables grouped by part */}
      {parts.map(part => (
        <div key={part} style={{ marginBottom: '32px' }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600', color: '#374151' }}>{part}</h3>
          <div style={{ overflowX: 'auto', border: '1px solid #e5e7eb', borderRadius: '6px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
              <thead>
                <tr style={{ backgroundColor: '#f9fafb' }}>
                  <th style={{ padding: '14px 16px', textAlign: 'left', fontWeight: '600', color: '#374151', borderBottom: '2px solid #e5e7eb' }}>Q.No</th>
                  <th style={{ padding: '14px 16px', textAlign: 'left', fontWeight: '600', color: '#374151', borderBottom: '2px solid #e5e7eb' }}>Question</th>
                  <th style={{ padding: '14px 16px', textAlign: 'left', fontWeight: '600', color: '#374151', borderBottom: '2px solid #e5e7eb' }}>Unit</th>
                  <th style={{ padding: '14px 16px', textAlign: 'left', fontWeight: '600', color: '#374151', borderBottom: '2px solid #e5e7eb' }}>Unit Name</th>
                  <th style={{ padding: '14px 16px', textAlign: 'left', fontWeight: '600', color: '#374151', borderBottom: '2px solid #e5e7eb' }}>CO</th>
                  <th style={{ padding: '14px 16px', textAlign: 'left', fontWeight: '600', color: '#374151', borderBottom: '2px solid #e5e7eb' }}>BL</th>
                </tr>
              </thead>
              <tbody>
                {groupedByPart[part].map((r, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #e5e7eb', backgroundColor: r._suggested ? '#f0fdf4' : r.out_of_syllabus ? '#fef3c7' : 'white' }}>
                    <td style={{ padding: '14px 16px', color: '#6b7280', fontWeight: '500' }}>{r.question_number}</td>
                    <td style={{ padding: '14px 16px', color: '#1f2937', maxWidth: '300px' }}>
                      {r.question?.substring(0, 100)}{r.question?.length > 100 ? '...' : ''}
                      {r.out_of_syllabus && <span style={{ marginLeft: '8px', padding: '2px 8px', backgroundColor: '#f59e0b', color: 'white', borderRadius: '4px', fontSize: '11px', fontWeight: '600' }}>OUT OF SYLLABUS</span>}
                      {r._suggested && !r.out_of_syllabus && (
                        <div style={{ marginTop: '4px' }}>
                          <span style={{ padding: '1px 7px', backgroundColor: '#d1fae5', color: '#065f46', borderRadius: '4px', fontSize: '11px', fontWeight: '700' }}>UPDATED</span>
                          {r._original && (
                            <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '3px', fontStyle: 'italic' }}>
                              Was: {r._original.substring(0, 80)}{r._original.length > 80 ? '...' : ''}
                            </div>
                          )}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '14px 16px', color: '#1f2937', fontWeight: '500' }}>{r.unit || '-'}</td>
                    <td style={{ padding: '14px 16px', color: '#6b7280', maxWidth: '160px', fontSize: 13 }}>{r.unit_title || '-'}</td>
                    <td style={{ padding: '14px 16px', minWidth: 100 }}>
                      {!r.out_of_syllabus ? (
                        <span style={{ fontWeight: 600, fontSize: 13, color: '#1f2937' }}>{r.course_outcomes?.[0] || '-'}</span>
                      ) : <span style={{ color: '#9ca3af' }}>-</span>}
                    </td>
                    <td style={{ padding: '14px 16px', minWidth: 110 }}>
                      {!r.out_of_syllabus ? (
                        <span style={{ padding: '3px 10px', backgroundColor: getBloomColor(r.bloom_level), color: 'white', borderRadius: '4px', fontSize: '12px', fontWeight: '600' }}>
                          {r.bloom_level || 'N/A'}
                        </span>
                      ) : <span style={{ color: '#9ca3af' }}>-</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}

      {results.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px', color: '#9ca3af' }}>
          No results available
        </div>
      )}

      {/* ── Bloom Distribution Summary ── */}
      {results.length > 0 && !hideAdaptive && (
        <BloomSummary
          results={results}
          subjectName={subjectName}
          userId={userId}
          adaptive={adaptive}
          setAdaptive={setAdaptive}
          adaptiveLoading={adaptiveLoading}
          setAdaptiveLoading={setAdaptiveLoading}
          adaptiveError={adaptiveError}
          setAdaptiveError={setAdaptiveError}
        />
      )}
    </div>
  );
}

function BloomSummary({ results, subjectName, userId, adaptive, setAdaptive, adaptiveLoading, setAdaptiveLoading, adaptiveError, setAdaptiveError }) {
  const total = results.length;
  const bloomCounts = results.reduce((acc, r) => {
    const bl = r.bloom_level;
    if (bl) acc[bl] = (acc[bl] || 0) + 1;
    return acc;
  }, {});

  const low = (bloomCounts['BT1'] || 0) + (bloomCounts['BT2'] || 0);
  const lowPct = Math.round((low / total) * 100);
  const targetLow = Math.floor(total * 0.4);
  const replacements = Math.max(0, low - targetLow);
  const needsImprovement = replacements > 0;

  const handleImprove = async () => {
    setAdaptiveError('');
    setAdaptiveLoading(true);
    setAdaptive(null);
    try {
      const payload = results
        .filter(r => !r.error)
        .map(r => ({ unit: r.unit, bloom_level: r.bloom_level, course_outcomes: r.course_outcomes || [] }));
      const res = await fetch('http://localhost:8002/adaptive/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, domain_name: subjectName, results: payload })
      });
      const d = await res.json();
      if (!res.ok) throw new Error(d.error || 'Failed');
      setAdaptive(d);
    } catch (e) {
      setAdaptiveError(e.message);
    } finally {
      setAdaptiveLoading(false);
    }
  };

  return (
    <div style={{ marginTop: '32px', borderTop: '2px solid #e5e7eb', paddingTop: '24px' }}>
      <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#1f2937', marginBottom: '16px' }}>
        📊 Bloom Level Distribution
      </h3>

      {/* Bar chart */}
      <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end', marginBottom: '16px', height: '80px' }}>
        {['BT1','BT2','BT3','BT4','BT5','BT6'].map(bl => {
          const count = bloomCounts[bl] || 0;
          const pct = total > 0 ? (count / total) * 100 : 0;
          return (
            <div key={bl} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
              <span style={{ fontSize: '11px', color: '#374151', marginBottom: '4px', fontWeight: '600' }}>{count}</span>
              <div style={{ width: '100%', height: `${Math.max(pct * 0.6, count > 0 ? 4 : 0)}px`, backgroundColor: BLOOM_COLORS[bl], borderRadius: '3px 3px 0 0', minHeight: count > 0 ? '4px' : '0' }} />
              <span style={{ fontSize: '11px', color: '#6b7280', marginTop: '4px' }}>{bl}</span>
            </div>
          );
        })}
      </div>

      {/* Stats row */}
      <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginBottom: '16px' }}>
        <Stat label="Total Questions" value={total} />
        <Stat label="Low-order (BT1/BT2)" value={`${low} (${lowPct}%)`} color={lowPct > 60 ? '#ef4444' : '#10b981'} />
        <Stat label="Higher-order (BT4+)" value={`${(bloomCounts['BT4']||0)+(bloomCounts['BT5']||0)+(bloomCounts['BT6']||0)} (${Math.round(((bloomCounts['BT4']||0)+(bloomCounts['BT5']||0)+(bloomCounts['BT6']||0))/total*100)}%)`} />
        {needsImprovement && (
          <Stat label="Replacements needed" value={replacements} color="#f59e0b"
            tooltip={`Replace ${replacements} low-level question(s) to bring BT1/BT2 below 40%`} />
        )}
      </div>

      {/* Improve button */}
      {needsImprovement && !adaptive && (
        <div style={{ padding: '14px 16px', backgroundColor: '#fef3c7', border: '1px solid #fbbf24', borderRadius: '8px', marginBottom: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ fontWeight: '600', color: '#92400e', fontSize: '14px' }}>⚠️ Paper needs improvement</div>
            <div style={{ color: '#78350f', fontSize: '13px', marginTop: '2px' }}>
              {lowPct}% of questions are BT1/BT2. Replace {replacements} question(s) with higher-order alternatives.
            </div>
          </div>
          <button onClick={handleImprove} disabled={adaptiveLoading}
            style={{ padding: '10px 20px', backgroundColor: adaptiveLoading ? '#9ca3af' : '#8b5cf6', color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: '500', cursor: adaptiveLoading ? 'not-allowed' : 'pointer', whiteSpace: 'nowrap' }}>
            {adaptiveLoading ? 'Generating...' : `Generate ${replacements} Replacement Question(s)`}
          </button>
        </div>
      )}

      {adaptiveError && (
        <div style={{ color: '#ef4444', fontSize: '13px', marginBottom: '12px' }}>{adaptiveError}</div>
      )}

      {/* Adaptive results */}
      {adaptive && (
        <div style={{ marginTop: '8px' }}>

          {/* Bloom guidance (no auto-gen) */}
          {adaptive.bloom_guidance?.length > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <h4 style={{ fontSize: '15px', fontWeight: '600', color: '#1f2937', marginBottom: '10px' }}>Bloom Gap Guidance</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {adaptive.bloom_guidance.map((g, i) => (
                  <BloomGuidanceCard key={i} guidance={g} syllabus={subjectName} userId={userId} />
                ))}
              </div>
            </div>
          )}

          {/* CO / Unit suggested questions */}
          {adaptive.suggested_questions?.length > 0 && (
            <div>
              <h4 style={{ fontSize: '15px', fontWeight: '600', color: '#1f2937', marginBottom: '10px' }}>
                Suggested Questions ({adaptive.suggested_questions.length})
                {adaptive.replacement_count > 0 && (
                  <span style={{ marginLeft: '8px', fontSize: '12px', fontWeight: '400', color: '#6b7280' }}>
                    — replace {adaptive.replacement_count} low-level question(s)
                  </span>
                )}
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {adaptive.suggested_questions.map((q, i) => (
                  <SuggestedCard key={i} q={q} userId={userId} subjectName={subjectName} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, color, tooltip }) {
  return (
    <div title={tooltip || ''} style={{ padding: '10px 14px', backgroundColor: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '6px', minWidth: '120px' }}>
      <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '2px' }}>{label}</div>
      <div style={{ fontSize: '16px', fontWeight: '700', color: color || '#1f2937' }}>{value}</div>
    </div>
  );
}

function BloomGuidanceCard({ guidance, userId, syllabus }) {
  const [question, setQuestion] = useState(null);
  const [loading, setLoading]   = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8002/adaptive/generate_bloom', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          domain_name: syllabus,
          target_bloom: guidance.target_bloom,
          target_unit: guidance.target_unit,
        }),
      });
      const d = await res.json();
      setQuestion(d.question || null);
    } catch { setQuestion('Generation failed. Try again.'); }
    finally { setLoading(false); }
  };

  return (
    <div style={{ padding: '16px', backgroundColor: '#fffbeb', borderRadius: '8px', border: '1px solid #fbbf24' }}>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '8px', alignItems: 'center' }}>
        <span style={{ padding: '2px 8px', backgroundColor: '#f59e0b', color: 'white', borderRadius: '4px', fontSize: '11px', fontWeight: '700' }}>BLOOM GAP</span>
        <span style={{ fontSize: '13px', color: '#92400e', fontWeight: '600' }}>{guidance.gap_message}</span>
      </div>
      <div style={{ fontSize: '13px', color: '#78350f', marginBottom: '6px' }}>
        Add higher-order questions using: <strong>{guidance.suggested_verbs}</strong>
      </div>
      <div style={{ fontSize: '12px', color: '#92400e', fontStyle: 'italic', marginBottom: '10px' }}>
        Example: {guidance.example_structure}
      </div>
      {question && (
        <div style={{ padding: '10px 12px', backgroundColor: '#fef9c3', borderRadius: '6px', fontSize: '13px', color: '#1f2937', marginBottom: '10px', lineHeight: '1.6' }}>
          {question}
        </div>
      )}
      <button onClick={handleGenerate} disabled={loading}
        style={{ padding: '7px 16px', backgroundColor: loading ? '#9ca3af' : '#f59e0b', color: 'white', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: '500', cursor: loading ? 'not-allowed' : 'pointer' }}>
        {loading ? 'Generating...' : question ? 'Regenerate' : 'Generate Question'}
      </button>
    </div>
  );
}

function SuggestedCard({ q, userId, subjectName }) {
  const [question, setQuestion] = useState(q.question);
  const [loading, setLoading]   = useState(false);

  const handleRegenerate = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8002/adaptive/regenerate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          domain_name: subjectName,
          unit: q.unit,
          bloom: q.bloom,
          co: q.co || null,
          gap_message: q.addresses,
        }),
      });
      const d = await res.json();
      if (d.question) setQuestion(d.question);
    } catch { /* keep existing */ }
    finally { setLoading(false); }
  };

  return (
    <div style={{ padding: '16px', backgroundColor: '#f0fdf4', borderRadius: '8px', border: '1px solid #bbf7d0' }}>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '10px', flexWrap: 'wrap' }}>
        <span style={{ padding: '2px 10px', backgroundColor: BLOOM_COLORS[q.bloom] || '#6b7280', color: 'white', borderRadius: '4px', fontSize: '12px', fontWeight: '600' }}>{q.bloom}</span>
        <span style={{ padding: '2px 10px', backgroundColor: '#dbeafe', color: '#1e40af', borderRadius: '4px', fontSize: '12px', fontWeight: '600' }}>Unit {q.unit}</span>
        {q.co && <span style={{ padding: '2px 10px', backgroundColor: '#d1fae5', color: '#065f46', borderRadius: '4px', fontSize: '12px', fontWeight: '600' }}>{q.co}</span>}
      </div>
      <p style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#1f2937', lineHeight: '1.6' }}>{question}</p>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
        <span style={{ fontSize: '12px', color: '#6b7280' }}>Addresses: {q.addresses}</span>
        <button onClick={handleRegenerate} disabled={loading}
          style={{ padding: '5px 14px', backgroundColor: loading ? '#9ca3af' : '#10b981', color: 'white', border: 'none', borderRadius: '6px', fontSize: '12px', fontWeight: '500', cursor: loading ? 'not-allowed' : 'pointer' }}>
          {loading ? '...' : 'Regenerate'}
        </button>
      </div>
    </div>
  );
}

function getBloomColor(level) {
  const colors = {
    BT1: '#6b7280', BT2: '#3b82f6', BT3: '#10b981',
    BT4: '#f59e0b', BT5: '#ef4444', BT6: '#8b5cf6'
  };
  return colors[level] || '#6b7280';
}
