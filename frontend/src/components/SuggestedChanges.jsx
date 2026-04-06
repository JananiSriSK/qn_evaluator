import { useState } from 'react';

const BLOOM_COLORS = {
  BT1: '#6b7280', BT2: '#3b82f6', BT3: '#10b981',
  BT4: '#f59e0b', BT5: '#ef4444', BT6: '#8b5cf6',
};
const BLOOM_ORDER = ['BT1', 'BT2', 'BT3', 'BT4', 'BT5', 'BT6'];
const LOW_LEVELS  = new Set(['BT1', 'BT2']);
const API         = 'http://localhost:8002';

export default function SuggestedChanges({ adaptive, results, userId, subjectName, onFinalise }) {
  const allGaps       = adaptive.gaps                || [];
  const bloomGuidance = adaptive.bloom_guidance      || [];
  const suggestions   = adaptive.suggested_questions || [];

  // Split suggestions by gap_type
  const coSuggestions   = suggestions.filter(q => q.gap_type === 'co_gap');
  const unitSuggestions = suggestions.filter(q => q.gap_type === 'unit_gap');

  // Split gaps for display
  const bloomGaps = allGaps.filter(g => g.type === 'bloom_gap');
  const coGaps    = allGaps.filter(g => g.type === 'co_gap');
  const unitGaps  = allGaps.filter(g => g.type === 'unit_gap');

  // replacements: { resultIdx → { newQuestion, newBloom, newCo, newUnit, originalQuestion } }
  const [replacements, setReplacements] = useState({});

  const applyReplacement  = (idx, payload) => setReplacements(prev => ({ ...prev, [idx]: payload }));
  const undoReplacement   = (idx)          => setReplacements(prev => { const n = { ...prev }; delete n[idx]; return n; });

  // Eligible = BT1/BT2, not already replaced, not error
  const eligibleRows = results
    .map((r, idx) => ({ ...r, _idx: idx }))
    .filter(r => !r.error && !r._suggested && LOW_LEVELS.has(r.bloom_level) && !replacements[r._idx]);

  // Bloom distribution stats
  const bloomCounts = results.reduce((acc, r) => {
    if (r.bloom_level) acc[r.bloom_level] = (acc[r.bloom_level] || 0) + 1;
    return acc;
  }, {});
  const total = results.length || 1;
  const low   = (bloomCounts['BT1'] || 0) + (bloomCounts['BT2'] || 0);
  const high  = BLOOM_ORDER.slice(3).reduce((s, b) => s + (bloomCounts[b] || 0), 0);
  const totalReplacements = Object.keys(replacements).length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

      {/* ── Paper overview ── */}
      <div style={{ padding: '16px 20px', backgroundColor: '#f9fafb', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
        <div style={{ fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '12px' }}>Current Paper Overview</div>
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginBottom: '12px' }}>
          <Stat label="Total Questions"     value={results.length} />
          <Stat label="Low-order (BT1/BT2)" value={`${low} (${Math.round(low / total * 100)}%)`}  color={low / total > 0.6 ? '#dc2626' : '#16a34a'} />
          <Stat label="Higher-order (BT4+)" value={`${high} (${Math.round(high / total * 100)}%)`} color={high === 0 ? '#dc2626' : '#16a34a'} />
        </div>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'flex-end', height: '48px' }}>
          {BLOOM_ORDER.map(bl => {
            const c = bloomCounts[bl] || 0;
            const h = Math.max((c / total) * 44, c > 0 ? 4 : 0);
            return (
              <div key={bl} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
                <span style={{ fontSize: '10px', color: '#374151', fontWeight: '600' }}>{c || ''}</span>
                <div style={{ width: '100%', height: `${h}px`, backgroundColor: BLOOM_COLORS[bl], borderRadius: '2px 2px 0 0' }} />
                <span style={{ fontSize: '10px', color: '#6b7280', marginTop: '2px' }}>{bl}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── All detected gaps ── */}
      {allGaps.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <SectionTitle>Detected Gaps ({allGaps.length})</SectionTitle>
          {allGaps.map((g, i) => (
            <div key={i} style={{ padding: '10px 14px', backgroundColor: '#fef3c7', border: '1px solid #fbbf24', borderRadius: '6px', fontSize: '13px', color: '#92400e', display: 'flex', gap: '8px', alignItems: 'center' }}>
              <span style={{ padding: '1px 7px', backgroundColor: '#f59e0b', color: 'white', borderRadius: '4px', fontSize: '11px', fontWeight: '700', whiteSpace: 'nowrap' }}>
                {g.type === 'bloom_gap' ? 'BLOOM' : g.type === 'co_gap' ? 'CO' : 'UNIT'}
              </span>
              ⚠ {g.message}
            </div>
          ))}
        </div>
      )}

      {/* ── BLOOM GAP SECTION — guidance + on-demand generation ── */}
      {bloomGuidance.length > 0 && (
        <div>
          <SectionTitle>Bloom Level Improvements ({bloomGuidance.length})</SectionTitle>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {bloomGuidance.map((g, i) => (
              <BloomGapCard
                key={i}
                guidance={g}
                userId={userId}
                subjectName={subjectName}
                eligibleRows={eligibleRows}
                replacements={replacements}
                onReplace={applyReplacement}
                onUndo={undoReplacement}
              />
            ))}
          </div>
        </div>
      )}

      {/* ── CO GAP SECTION — auto-generated ── */}
      {coSuggestions.length > 0 && (
        <div>
          <SectionTitle>Missing CO — Suggested Questions ({coSuggestions.length})</SectionTitle>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {coSuggestions.map((q, i) => (
              <SuggestionCard
                key={i}
                suggestion={q}
                userId={userId}
                subjectName={subjectName}
                eligibleRows={eligibleRows}
                replacements={replacements}
                onReplace={applyReplacement}
                onUndo={undoReplacement}
              />
            ))}
          </div>
        </div>
      )}

      {/* ── UNIT GAP SECTION — auto-generated ── */}
      {unitSuggestions.length > 0 && (
        <div>
          <SectionTitle>Missing Unit Coverage — Suggested Questions ({unitSuggestions.length})</SectionTitle>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {unitSuggestions.map((q, i) => (
              <SuggestionCard
                key={i}
                suggestion={q}
                userId={userId}
                subjectName={subjectName}
                eligibleRows={eligibleRows}
                replacements={replacements}
                onReplace={applyReplacement}
                onUndo={undoReplacement}
              />
            ))}
          </div>
        </div>
      )}

      {allGaps.length === 0 && bloomGuidance.length === 0 && suggestions.length === 0 && (
        <div style={{ textAlign: 'center', padding: '32px', color: '#16a34a', fontSize: '14px' }}>
          ✓ No gaps detected — paper has good Bloom and CO coverage.
        </div>
      )}

      {/* ── Finalise bar ── */}
      <div style={{ position: 'sticky', bottom: 0, backgroundColor: 'white', borderTop: '1px solid #e5e7eb', padding: '14px 0', display: 'flex', alignItems: 'center', gap: '16px' }}>
        <span style={{ fontSize: '14px', color: '#6b7280' }}>
          {totalReplacements > 0
            ? <><strong style={{ color: '#1f2937' }}>{totalReplacements}</strong> replacement(s) ready</>
            : 'Click "Replace Question" on any suggestion to update the paper'}
        </span>
        <button onClick={() => onFinalise(replacements)} disabled={totalReplacements === 0}
          style={{ padding: '10px 28px', backgroundColor: totalReplacements === 0 ? '#9ca3af' : '#3b82f6', color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: '600', cursor: totalReplacements === 0 ? 'not-allowed' : 'pointer' }}>
          Apply {totalReplacements > 0 ? `${totalReplacements} ` : ''}Replacement(s) to Paper
        </button>
      </div>
    </div>
  );
}

// ── BLOOM GAP CARD — guidance only, generate on click ────────────────────────

const BLOOM_LABELS_UI = {
  BT1: 'Remember', BT2: 'Understand', BT3: 'Apply',
  BT4: 'Analyze',  BT5: 'Evaluate',  BT6: 'Create',
};

function BloomGapCard({ guidance, userId, subjectName, eligibleRows, replacements, onReplace, onUndo }) {
  // Default selected bloom = the gap's target, but user can change it
  const [selectedBloom, setSelectedBloom] = useState(guidance.target_bloom);
  const [question, setQuestion]           = useState(null);
  const [loading, setLoading]             = useState(false);
  const [picking, setPicking]             = useState(false);
  const [replaced, setReplaced]           = useState(null);
  const [replaceLoading, setReplaceLoading] = useState(false);
  const [manualMode, setManualMode]       = useState(false);
  const [manualText, setManualText]       = useState('');

  const generate = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/adaptive/generate_bloom`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, domain_name: subjectName, target_bloom: selectedBloom, target_unit: guidance.target_unit }),
      });
      const d = await res.json();
      setQuestion(d.question || null);
      setManualMode(false);
      setPicking(false);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  const activeQuestion = manualMode ? manualText.trim() : question;

  const confirmReplace = async (row) => {
    if (!activeQuestion) return;
    setReplaceLoading(true);
    try {
      const res = await fetch(`${API}/adaptive/replace-question`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question_index: row._idx, new_question: activeQuestion, new_bloom: selectedBloom, new_unit: guidance.target_unit }),
      });
      const d = await res.json();
      if (d.status === 'success') {
        onReplace(row._idx, { newQuestion: activeQuestion, newBloom: selectedBloom, newCo: null, newUnit: guidance.target_unit, originalQuestion: row.question });
        setReplaced({ resultIdx: row._idx, originalQuestion: row.question });
        setPicking(false);
      }
    } catch { /* ignore */ }
    finally { setReplaceLoading(false); }
  };

  const undo = () => { if (replaced) { onUndo(replaced.resultIdx); setReplaced(null); setQuestion(null); } };
  const available = eligibleRows.filter(r => !replacements[r._idx]);

  // Reset question when bloom selection changes
  const handleBloomChange = (bl) => {
    setSelectedBloom(bl);
    setQuestion(null);
    setManualMode(false);
    setManualText('');
    setPicking(false);
  };

  return (
    <div style={{ padding: '16px', backgroundColor: replaced ? '#f0fdf4' : '#fffbeb', borderRadius: '8px', border: `1px solid ${replaced ? '#bbf7d0' : '#fbbf24'}` }}>

      {/* Gap message */}
      <div style={{ fontSize: '13px', color: '#92400e', fontWeight: '600', marginBottom: '4px' }}>{guidance.gap_message}</div>
      <div style={{ fontSize: '12px', color: '#78350f', fontStyle: 'italic', marginBottom: '12px' }}>
        Example: {guidance.example_structure}
      </div>

      {/* Bloom level selector */}
      {!replaced && (
        <div style={{ marginBottom: '12px' }}>
          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '6px', fontWeight: '500' }}>Select Bloom level to generate:</div>
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {['BT4', 'BT5', 'BT6'].map(bl => {
              const isSelected  = selectedBloom === bl;
              const isTarget    = bl === guidance.target_bloom;
              const isMissing   = isTarget;
              return (
                <button key={bl} onClick={() => handleBloomChange(bl)}
                  style={{
                    padding: '5px 14px',
                    backgroundColor: isSelected ? BLOOM_COLORS[bl] : 'white',
                    color: isSelected ? 'white' : BLOOM_COLORS[bl],
                    border: `2px solid ${BLOOM_COLORS[bl]}`,
                    borderRadius: '6px', fontSize: '12px', fontWeight: '600', cursor: 'pointer',
                    position: 'relative',
                  }}>
                  {bl} — {BLOOM_LABELS_UI[bl]}
                  {isMissing && !isSelected && (
                    <span style={{ marginLeft: '5px', fontSize: '10px', color: '#dc2626', fontWeight: '700' }}>missing</span>
                  )}
                </button>
              );
            })}
          </div>
          <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '5px' }}>
            Verbs for <strong style={{ color: BLOOM_COLORS[selectedBloom] }}>{selectedBloom}</strong>: {guidance.suggested_verbs}
          </div>
        </div>
      )}

      {/* Generate / manual buttons */}
      {!question && !manualMode && !replaced && (
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={generate} disabled={loading}
            style={solidBtn(loading ? '#9ca3af' : BLOOM_COLORS[selectedBloom] || '#f59e0b')}>
            {loading ? 'Generating...' : `Generate ${selectedBloom} Question`}
          </button>
          <button onClick={() => setManualMode(true)} style={outlineBtn}>Write My Own</button>
        </div>
      )}

      {/* Manual input */}
      {manualMode && !replaced && (
        <div style={{ marginTop: '4px' }}>
          <textarea value={manualText} onChange={e => setManualText(e.target.value)}
            placeholder={`Type your ${selectedBloom} question here...`} rows={3}
            style={{ width: '100%', padding: '8px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '13px', fontFamily: 'inherit', resize: 'vertical', boxSizing: 'border-box', marginBottom: '8px' }} />
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button onClick={() => setPicking(true)} disabled={!manualText.trim()} style={solidBtn(!manualText.trim() ? '#9ca3af' : '#3b82f6')}>Replace Question</button>
            <button onClick={() => { setManualMode(false); setManualText(''); }} style={outlineBtn}>Cancel</button>
            <button onClick={generate} disabled={loading} style={outlineBtn}>{loading ? '...' : 'Generate Instead'}</button>
          </div>
        </div>
      )}

      {/* Generated question */}
      {question && !manualMode && !replaced && (
        <div style={{ backgroundColor: 'white', borderRadius: '6px', border: '1px solid #e5e7eb', padding: '12px' }}>
          <div style={{ display: 'flex', gap: '6px', marginBottom: '8px' }}>
            <span style={{ padding: '1px 8px', backgroundColor: BLOOM_COLORS[selectedBloom], color: 'white', borderRadius: '4px', fontSize: '11px', fontWeight: '700' }}>{selectedBloom}</span>
            <span style={{ fontSize: '11px', color: '#6b7280' }}>Unit {guidance.target_unit} — {guidance.unit_title}</span>
          </div>
          <p style={{ margin: '0 0 10px', fontSize: '14px', color: '#1f2937', lineHeight: '1.6' }}>{question}</p>
          {picking ? (
            <ReplacePicker available={available} loading={replaceLoading} onPick={confirmReplace} onCancel={() => setPicking(false)} />
          ) : (
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <button onClick={() => setPicking(true)} style={solidBtn('#3b82f6')}>Replace Question</button>
              <button onClick={() => { setManualMode(true); setManualText(question); }} style={outlineBtn}>Edit Question</button>
              <button onClick={generate} disabled={loading} style={outlineBtn}>{loading ? '...' : 'Regenerate'}</button>
            </div>
          )}
        </div>
      )}

      {picking && manualMode && (
        <ReplacePicker available={available} loading={replaceLoading} onPick={confirmReplace} onCancel={() => setPicking(false)} />
      )}

      {replaced && <ReplacedBadge originalQuestion={replaced.originalQuestion} onUndo={undo} />}
    </div>
  );
}

// ── CO / UNIT SUGGESTION CARD — auto-generated ────────────────────────────────

function SuggestionCard({ suggestion, userId, subjectName, eligibleRows, replacements, onReplace, onUndo }) {
  const [selectedBloom, setSelectedBloom] = useState(suggestion.bloom || 'BT4');
  const [question, setQuestion]           = useState(suggestion.question);
  const [picking, setPicking]             = useState(false);
  const [replaced, setReplaced]           = useState(null);
  const [replaceLoading, setReplaceLoading] = useState(false);
  const [manualMode, setManualMode]       = useState(false);
  const [manualText, setManualText]       = useState('');
  const [genLoading, setGenLoading]       = useState(false);

  const activeQuestion = manualMode ? manualText.trim() : question;

  // Regenerate with currently selected bloom
  const regenerate = async (bloom) => {
    setGenLoading(true);
    try {
      const res = await fetch(`${API}/adaptive/regenerate`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId, domain_name: subjectName,
          unit: suggestion.unit, bloom: bloom || selectedBloom,
          co: suggestion.co || null, gap_message: suggestion.addresses,
        }),
      });
      const d = await res.json();
      if (d.question) { setQuestion(d.question); setPicking(false); setManualMode(false); }
    } catch { /* keep */ }
    finally { setGenLoading(false); }
  };

  // When bloom selection changes, auto-regenerate
  const handleBloomChange = (bl) => {
    setSelectedBloom(bl);
    setQuestion(null);
    setManualMode(false);
    setManualText('');
    setPicking(false);
    regenerate(bl);
  };

  const confirmReplace = async (row) => {
    if (!activeQuestion) return;
    setReplaceLoading(true);
    try {
      const res = await fetch(`${API}/adaptive/replace-question`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question_index: row._idx, new_question: activeQuestion, new_bloom: selectedBloom, new_co: suggestion.co || null, new_unit: suggestion.unit }),
      });
      const d = await res.json();
      if (d.status === 'success') {
        onReplace(row._idx, { newQuestion: activeQuestion, newBloom: selectedBloom, newCo: suggestion.co || null, newUnit: suggestion.unit, originalQuestion: row.question });
        setReplaced({ resultIdx: row._idx, originalQuestion: row.question });
        setPicking(false);
      }
    } catch { /* ignore */ }
    finally { setReplaceLoading(false); }
  };

  const undo = () => { if (replaced) { onUndo(replaced.resultIdx); setReplaced(null); } };
  const available = eligibleRows.filter(r => !replacements[r._idx]);

  return (
    <div style={{ padding: '16px', backgroundColor: replaced ? '#f0fdf4' : '#f9fafb', borderRadius: '8px', border: `1px solid ${replaced ? '#bbf7d0' : '#e5e7eb'}` }}>

      {/* Badges */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '10px', flexWrap: 'wrap' }}>
        <span style={{ padding: '2px 10px', backgroundColor: BLOOM_COLORS[selectedBloom] || '#6b7280', color: 'white', borderRadius: '4px', fontSize: '12px', fontWeight: '600' }}>{selectedBloom}</span>
        <span style={{ padding: '2px 10px', backgroundColor: '#dbeafe', color: '#1e40af', borderRadius: '4px', fontSize: '12px', fontWeight: '600' }}>Unit {suggestion.unit}</span>
        {suggestion.co && (
          <span style={{ padding: '2px 10px', backgroundColor: '#d1fae5', color: '#065f46', borderRadius: '4px', fontSize: '12px', fontWeight: '600' }}>{suggestion.co}</span>
        )}
      </div>

      <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '10px' }}>Addresses: {suggestion.addresses}</div>

      {/* Bloom selector */}
      {!replaced && (
        <div style={{ marginBottom: '12px' }}>
          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '6px', fontWeight: '500' }}>Select cognitive level:</div>
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {['BT3', 'BT4', 'BT5', 'BT6'].map(bl => (
              <button key={bl} onClick={() => handleBloomChange(bl)}
                style={{
                  padding: '4px 12px',
                  backgroundColor: selectedBloom === bl ? BLOOM_COLORS[bl] : 'white',
                  color: selectedBloom === bl ? 'white' : BLOOM_COLORS[bl],
                  border: `2px solid ${BLOOM_COLORS[bl]}`,
                  borderRadius: '6px', fontSize: '12px', fontWeight: '600', cursor: 'pointer',
                }}>
                {bl} — {BLOOM_LABELS_UI[bl]}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Loading state */}
      {genLoading && (
        <div style={{ fontSize: '13px', color: '#6b7280', padding: '8px 0' }}>Generating {selectedBloom} question...</div>
      )}

      {/* Generated question */}
      {!manualMode && question && !genLoading && (
        <p style={{ margin: '0 0 10px', fontSize: '14px', color: '#1f2937', lineHeight: '1.6',
          padding: '10px 12px', backgroundColor: 'white', borderRadius: '6px', border: '1px solid #e5e7eb' }}>
          {question}
        </p>
      )}

      {/* Manual edit */}
      {manualMode && !replaced && (
        <div style={{ marginBottom: '10px' }}>
          <textarea value={manualText} onChange={e => setManualText(e.target.value)}
            placeholder={`Type your ${selectedBloom} question here...`} rows={3}
            style={{ width: '100%', padding: '8px', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '13px', fontFamily: 'inherit', resize: 'vertical', boxSizing: 'border-box', marginBottom: '8px' }} />
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button onClick={() => setPicking(true)} disabled={!manualText.trim()} style={solidBtn(!manualText.trim() ? '#9ca3af' : '#3b82f6')}>Replace Question</button>
            <button onClick={() => { setManualMode(false); setManualText(''); }} style={outlineBtn}>Cancel</button>
          </div>
        </div>
      )}

      {replaced ? (
        <ReplacedBadge originalQuestion={replaced.originalQuestion} onUndo={undo} />
      ) : picking ? (
        <ReplacePicker available={available} loading={replaceLoading} onPick={confirmReplace} onCancel={() => setPicking(false)} />
      ) : !manualMode && !genLoading ? (
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button onClick={() => setPicking(true)} disabled={!question} style={solidBtn(!question ? '#9ca3af' : '#3b82f6')}>Replace Question</button>
          <button onClick={() => { setManualMode(true); setManualText(question || ''); }} style={outlineBtn}>Edit / Write My Own</button>
          <button onClick={() => regenerate(selectedBloom)} disabled={genLoading} style={outlineBtn}>Regenerate</button>
        </div>
      ) : null}
    </div>
  );
}

// ── Replace picker ────────────────────────────────────────────────────────────

function ReplacePicker({ available, loading, onPick, onCancel }) {
  return (
    <div style={{ backgroundColor: '#f0f9ff', border: '1px solid #bfdbfe', borderRadius: '6px', padding: '12px' }}>
      <div style={{ fontSize: '13px', fontWeight: '600', color: '#1e40af', marginBottom: '8px' }}>
        Which question do you want to replace?
      </div>
      {available.length === 0 ? (
        <div style={{ fontSize: '13px', color: '#6b7280' }}>No eligible low-level (BT1/BT2) questions available.</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '200px', overflowY: 'auto' }}>
          {available.map(r => (
            <button key={r._idx} onClick={() => !loading && onPick(r)} disabled={loading}
              style={{ padding: '8px 12px', backgroundColor: 'white', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '13px', color: '#1f2937', textAlign: 'left', cursor: loading ? 'not-allowed' : 'pointer', display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
              <span style={{ padding: '1px 7px', backgroundColor: BLOOM_COLORS[r.bloom_level] || '#e5e7eb', color: 'white', borderRadius: '4px', fontSize: '11px', fontWeight: '700', whiteSpace: 'nowrap' }}>
                Q{r.question_number} · {r.bloom_level}
              </span>
              <span style={{ color: '#374151', lineHeight: '1.4' }}>{r.question?.substring(0, 90)}{r.question?.length > 90 ? '...' : ''}</span>
            </button>
          ))}
        </div>
      )}
      <button onClick={onCancel} style={{ marginTop: '8px', fontSize: '12px', color: '#6b7280', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}>
        Cancel
      </button>
    </div>
  );
}

// ── Replaced badge ────────────────────────────────────────────────────────────

function ReplacedBadge({ originalQuestion, onUndo }) {
  const [show, setShow] = useState(false);
  return (
    <div style={{ backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '6px', padding: '10px 12px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '12px', fontWeight: '700', color: '#065f46', backgroundColor: '#d1fae5', padding: '1px 8px', borderRadius: '4px' }}>UPDATED</span>
        <button onClick={() => setShow(v => !v)} style={{ fontSize: '12px', color: '#6b7280', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}>
          {show ? 'Hide original' : 'Show original'}
        </button>
        <button onClick={onUndo} style={{ marginLeft: 'auto', fontSize: '12px', color: '#dc2626', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}>Undo</button>
      </div>
      {show && (
        <div style={{ fontSize: '12px', color: '#6b7280', fontStyle: 'italic', borderTop: '1px solid #d1fae5', paddingTop: '8px', marginTop: '8px' }}>
          Original: {originalQuestion}
        </div>
      )}
    </div>
  );
}

// ── Atoms ─────────────────────────────────────────────────────────────────────

function SectionTitle({ children }) {
  return <div style={{ fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '10px' }}>{children}</div>;
}

function Stat({ label, value, color }) {
  return (
    <div style={{ padding: '8px 14px', backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '6px' }}>
      <div style={{ fontSize: '11px', color: '#6b7280' }}>{label}</div>
      <div style={{ fontSize: '15px', fontWeight: '700', color: color || '#1f2937' }}>{value}</div>
    </div>
  );
}

const solidBtn  = bg => ({ padding: '6px 16px', backgroundColor: bg, color: 'white', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: '500', cursor: 'pointer' });
const outlineBtn = { padding: '6px 14px', backgroundColor: 'transparent', color: '#6b7280', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '12px', cursor: 'pointer' };
