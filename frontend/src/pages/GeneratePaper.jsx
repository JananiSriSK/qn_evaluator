import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ElicitLayout from '../components/ElicitLayout';
import { api } from '../services/api-v2';

const API = 'http://localhost:8002';
const BT_ALL = ['BT1', 'BT2', 'BT3', 'BT4', 'BT5', 'BT6'];
const BT_LABELS = { BT1: 'Remember', BT2: 'Understand', BT3: 'Apply', BT4: 'Analyse', BT5: 'Evaluate', BT6: 'Create' };
const BT_COLORS = { BT1: '#6b7280', BT2: '#3b82f6', BT3: '#10b981', BT4: '#f59e0b', BT5: '#ef4444', BT6: '#8b5cf6' };

const inp = { padding: '6px 10px', border: '1px solid #d1d5db', borderRadius: 6, fontSize: 13, boxSizing: 'border-box', width: '100%' };
const sel = { ...inp, background: 'white', cursor: 'pointer' };

function Badge({ label, color, bg }) {
  return <span style={{ padding: '2px 9px', background: bg || color, color: color && !bg ? 'white' : '#374151', borderRadius: 4, fontSize: 11, fontWeight: 700, whiteSpace: 'nowrap' }}>{label}</span>;
}

// ── Cover page editor ───────────────────────────────────────────────────────
function CoverPageEditor({ cover, setCover }) {
  const [open, setOpen] = useState(false);
  const f = (k, v) => setCover(c => ({ ...c, [k]: v }));
  const row = (label, key, type = 'text') => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <label style={{ fontSize: 11, fontWeight: 600, color: '#6b7280', textTransform: 'uppercase' }}>{label}</label>
      <input type={type} value={cover[key] || ''} onChange={e => f(key, e.target.value)} style={inp} />
    </div>
  );
  return (
    <div style={{ background: 'white', borderRadius: 8, border: '1px solid #e5e7eb', marginBottom: 20 }}>
      <button onClick={() => setOpen(o => !o)}
        style={{ width: '100%', padding: '12px 20px', background: 'none', border: 'none', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 14, fontWeight: 600, color: '#374151' }}>{open ? '▲ Hide' : '▼ Show'} paper details (cover page)</span>
        <span style={{ fontSize: 12, color: '#6b7280' }}>Anna University Cover Page Details</span>
      </button>
      {open && (
        <div style={{ padding: '0 20px 20px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
            {row('Assessment', 'assessment')}
            {row('Programme', 'programme')}
            {row('Course Code', 'course_code')}
            {row('Course Title', 'course_title')}
            {row('Date of Exam', 'date', 'date')}
            {row('Year / Semester', 'semester')}
            {row('Regulation', 'regulation')}
            {row('Duration', 'duration')}
          </div>
          <p style={{ fontSize: 11, color: '#9ca3af', marginTop: 10, marginBottom: 0 }}>CO descriptions will be auto-populated from the evaluated results.</p>
        </div>
      )}
    </div>
  );
}

// ── Step 1: Part config ───────────────────────────────────────────────────────
function PartConfigurator({ parts, setParts }) {
  const update = (i, f, v) => setParts(p => p.map((x, j) => j === i ? { ...x, [f]: v } : x));
  const add = () => {
    const labels = 'ABCDEFGH';
    setParts(p => [...p, { part: labels[p.length] || `P${p.length + 1}`, marks_per_question: 10, question_count: 5 }]);
  };
  const remove = i => setParts(p => p.filter((_, j) => j !== i));
  const total = parts.reduce((s, p) => s + p.marks_per_question * p.question_count, 0);
  const totalQ = parts.reduce((s, p) => s + p.question_count, 0);

  return (
    <div style={{ background: 'white', borderRadius: 8, border: '1px solid #e5e7eb', padding: 24, marginBottom: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: '#374151' }}>Step 1 — Define Parts</div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <span style={{ fontSize: 13, color: '#6b7280' }}>{totalQ} questions · {total} marks</span>
          <button onClick={add} disabled={parts.length >= 6}
            style={{ padding: '5px 12px', background: '#f0f9ff', color: '#1e40af', border: '1px solid #bfdbfe', borderRadius: 6, fontSize: 13, cursor: 'pointer' }}>
            + Add Part
          </button>
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
        {parts.map((p, i) => (
          <div key={i} style={{ padding: 14, background: '#f9fafb', borderRadius: 8, border: '1px solid #e5e7eb', position: 'relative' }}>
            {parts.length > 1 && (
              <button onClick={() => remove(i)} style={{ position: 'absolute', top: 6, right: 8, background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer', fontSize: 16 }}>×</button>
            )}
            <div style={{ fontSize: 12, fontWeight: 700, color: '#1e40af', marginBottom: 10 }}>Part {p.part}</div>
            <label style={{ fontSize: 11, color: '#6b7280', fontWeight: 600, display: 'block', marginBottom: 3 }}>LABEL</label>
            <input value={p.part} maxLength={2} onChange={e => update(i, 'part', e.target.value.toUpperCase())} style={{ ...inp, marginBottom: 8 }} />
            <label style={{ fontSize: 11, color: '#6b7280', fontWeight: 600, display: 'block', marginBottom: 3 }}>MARKS / QN</label>
            <input type="number" min={1} max={100} value={p.marks_per_question} onChange={e => update(i, 'marks_per_question', parseInt(e.target.value) || 1)} style={{ ...inp, marginBottom: 8 }} />
            <label style={{ fontSize: 11, color: '#6b7280', fontWeight: 600, display: 'block', marginBottom: 3 }}>NO. OF QNS</label>
            <input type="number" min={1} max={50} value={p.question_count} onChange={e => update(i, 'question_count', parseInt(e.target.value) || 1)} style={inp} />
            <div style={{ marginTop: 8, fontSize: 11, color: '#6b7280' }}>Subtotal: <strong>{p.marks_per_question * p.question_count}M</strong></div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Step 2: Slot editor ───────────────────────────────────────────────────────
function SlotEditor({ slotsData, onSlotsChange, onGenerate, loading }) {
  const { units = [], co_keys = [], parts = [] } = slotsData;
  const [activeTab, setActiveTab] = useState(0);

  const updateSlot = (partIdx, slotIdx, field, value) => {
    const next = parts.map((pt, pi) => pi !== partIdx ? pt : {
      ...pt,
      slots: pt.slots.map((s, si) => si !== slotIdx ? s : { ...s, [field]: value })
    });
    onSlotsChange({ ...slotsData, parts: next });
  };

  // when unit changes, reset topic to first topic of that unit
  const handleUnitChange = (partIdx, slotIdx, unitNum) => {
    const unit = units.find(u => u.number === unitNum);
    const firstTopic = unit?.topics?.[0] || '';
    const next = parts.map((pt, pi) => pi !== partIdx ? pt : {
      ...pt,
      slots: pt.slots.map((s, si) => si !== slotIdx ? s : { ...s, unit: unitNum, unit_title: unit?.title || '', topic: firstTopic })
    });
    onSlotsChange({ ...slotsData, parts: next });
  };

  return (
    <div style={{ background: 'white', borderRadius: 8, border: '1px solid #e5e7eb', marginBottom: 20 }}>
      <div style={{ padding: '16px 24px', borderBottom: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: '#374151' }}>Step 2 — Set Unit / CO / Bloom for each question</div>
        <button onClick={onGenerate} disabled={loading}
          style={{ padding: '9px 24px', background: loading ? '#9ca3af' : '#8b5cf6', color: 'white', border: 'none', borderRadius: 6, fontSize: 14, fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer' }}>
          {loading ? 'Generating...' : '⚡ Generate Paper'}
        </button>
      </div>

      {/* Part tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid #e5e7eb' }}>
        {parts.map((pt, i) => (
          <button key={i} onClick={() => setActiveTab(i)}
            style={{ padding: '10px 20px', background: activeTab === i ? '#faf5ff' : 'white', border: 'none', borderBottom: activeTab === i ? '2px solid #8b5cf6' : '2px solid transparent', fontSize: 13, fontWeight: activeTab === i ? 600 : 400, color: activeTab === i ? '#6d28d9' : '#6b7280', cursor: 'pointer' }}>
            Part {pt.part} <span style={{ fontSize: 11, color: '#9ca3af' }}>({pt.slots.length}Q)</span>
          </button>
        ))}
      </div>

      {parts[activeTab] && (
        <div style={{ padding: 20 }}>
          {/* Column headers */}
          <div style={{ display: 'grid', gridTemplateColumns: '40px 90px 1fr 110px 90px 80px', gap: 8, marginBottom: 8, padding: '0 4px' }}>
            {['#', 'Marks', 'Topic', 'Bloom', 'CO', 'Unit'].map(h => (
              <div key={h} style={{ fontSize: 11, fontWeight: 600, color: '#6b7280', textTransform: 'uppercase' }}>{h}</div>
            ))}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {parts[activeTab].slots.map((slot, si) => {
              const unitObj = units.find(u => u.number === slot.unit);
              const topicList = unitObj?.topics || [];
              return (
                <div key={si} style={{ display: 'grid', gridTemplateColumns: '40px 90px 1fr 110px 90px 80px', gap: 8, alignItems: 'center', padding: '8px 4px', background: si % 2 === 0 ? '#fafafa' : 'white', borderRadius: 6 }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: '#374151' }}>{slot.q_no}</span>
                  <span style={{ fontSize: 12, color: '#6b7280' }}>{slot.marks}M</span>

                  {/* Topic (depends on unit) */}
                  <select value={slot.topic} onChange={e => updateSlot(activeTab, si, 'topic', e.target.value)} style={sel}>
                    {topicList.map(t => <option key={t} value={t}>{t}</option>)}
                    {!topicList.includes(slot.topic) && <option value={slot.topic}>{slot.topic}</option>}
                  </select>

                  {/* Bloom */}
                  <select value={slot.bloom} onChange={e => updateSlot(activeTab, si, 'bloom', e.target.value)} style={{ ...sel, color: BT_COLORS[slot.bloom] }}>
                    {BT_ALL.map(bt => <option key={bt} value={bt}>{bt} – {BT_LABELS[bt]}</option>)}
                  </select>

                  {/* CO */}
                  <select value={slot.co || ''} onChange={e => updateSlot(activeTab, si, 'co', e.target.value)} style={sel}>
                    {co_keys.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>

                  {/* Unit */}
                  <select value={slot.unit} onChange={e => handleUnitChange(activeTab, si, e.target.value)} style={sel}>
                    {units.map(u => <option key={u.number} value={u.number}>Unit {u.number}</option>)}
                  </select>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Step 3: Generated paper ───────────────────────────────────────────────────
function GeneratedPaper({ paper, userId, domainName, onPaperChange, coverPage, setCoverPage }) {
  const [editingKey, setEditingKey] = useState(null);
  const [editText, setEditText] = useState('');
  const [regenLoading, setRegenLoading] = useState(null);
  const [exportLoading, setExportLoading] = useState(null);
  const [coverOpen, setCoverOpen] = useState(false);

  const f = (k, v) => setCoverPage(c => ({ ...c, [k]: v }));
  const coverRow = (label, key, type = 'text') => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <label style={{ fontSize: 11, fontWeight: 600, color: '#6b7280', textTransform: 'uppercase' }}>{label}</label>
      <input type={type} value={coverPage[key] || ''} onChange={e => f(key, e.target.value)} style={inp} />
    </div>
  );

  const handleExport = async (fmt) => {
    setExportLoading(fmt);
    try {
      const res = await fetch(`${API}/generate/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ paper, format: fmt, meta: coverPage, user_id: userId, domain_name: domainName }),
      });
      if (!res.ok) throw new Error('Export failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${(paper.course_name || 'paper').replace(/\s+/g, '_')}.${fmt}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) { alert(e.message); }
    finally { setExportLoading(null); }
  };

  const updateQuestion = (partIdx, qIdx, field, value) => {
    const next = {
      ...paper,
      parts: paper.parts.map((pt, pi) => pi !== partIdx ? pt : {
        ...pt,
        questions: pt.questions.map((q, qi) => qi !== qIdx ? q : { ...q, [field]: value })
      })
    };
    onPaperChange(next);
  };

  const handleRegen = async (partIdx, qIdx, slot) => {
    const key = `${partIdx}-${qIdx}`;
    setRegenLoading(key);
    try {
      const res = await fetch(`${API}/generate/question`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, domain_name: domainName, slot }),
      });
      const data = await res.json();
      if (data.question) updateQuestion(partIdx, qIdx, 'question', data.question);
    } catch (e) { console.error(e); }
    finally { setRegenLoading(null); }
  };

  const { summary } = paper;

  return (
    <div>
      <div style={{ background: 'white', borderRadius: 8, border: '1px solid #e5e7eb', marginBottom: 16 }}>
        <button onClick={() => setCoverOpen(o => !o)}
          style={{ width: '100%', padding: '12px 20px', background: 'none', border: 'none', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 14, fontWeight: 600, color: '#374151' }}>{coverOpen ? '\u25b2 Hide' : '\u25bc Show'} paper details (cover page)</span>
          <span style={{ fontSize: 12, color: '#6b7280' }}>Anna University Cover Page Details</span>
        </button>
        {coverOpen && (
          <div style={{ padding: '0 20px 20px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
              {coverRow('Assessment', 'assessment')}
              {coverRow('Programme', 'programme')}
              {coverRow('Course Code', 'course_code')}
              {coverRow('Course Title', 'course_title')}
              {coverRow('Date of Exam', 'date', 'date')}
              {coverRow('Year / Semester', 'semester')}
              {coverRow('Regulation', 'regulation')}
              {coverRow('Duration', 'duration')}
            </div>
            <p style={{ fontSize: 11, color: '#9ca3af', marginTop: 10, marginBottom: 0 }}>CO descriptions will be auto-populated from the evaluated results.</p>
          </div>
        )}
      </div>

      {/* Summary */}
      <div style={{ background: 'white', borderRadius: 8, border: '1px solid #e5e7eb', padding: 20, marginBottom: 16 }}>
        <div style={{ fontSize: 15, fontWeight: 600, color: '#1f2937', marginBottom: 2 }}>{paper.course_name}</div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div style={{ fontSize: 13, color: '#6b7280' }}>{summary.total_questions} questions · {summary.total_marks} marks</div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={() => handleExport('pdf')} disabled={exportLoading === 'pdf'}
              style={{ padding: '6px 16px', background: exportLoading === 'pdf' ? '#e5e7eb' : '#fef2f2', color: exportLoading === 'pdf' ? '#9ca3af' : '#dc2626', border: '1px solid #fca5a5', borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: exportLoading === 'pdf' ? 'not-allowed' : 'pointer' }}>
              {exportLoading === 'pdf' ? 'Exporting...' : '↓ PDF'}
            </button>
            <button onClick={() => handleExport('docx')} disabled={exportLoading === 'docx'}
              style={{ padding: '6px 16px', background: exportLoading === 'docx' ? '#e5e7eb' : '#eff6ff', color: exportLoading === 'docx' ? '#9ca3af' : '#1d4ed8', border: '1px solid #bfdbfe', borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: exportLoading === 'docx' ? 'not-allowed' : 'pointer' }}>
              {exportLoading === 'docx' ? 'Exporting...' : '↓ DOCX'}
            </button>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
          {[['Bloom', summary.bloom_distribution, k => BT_COLORS[k]],
            ['CO', summary.co_distribution, () => '#3b82f6'],
            ['Unit', summary.unit_distribution, () => '#6b7280']].map(([label, dist, colorFn]) => (
            <div key={label}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#6b7280', marginBottom: 5, textTransform: 'uppercase' }}>{label}</div>
              <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                {Object.entries(dist).map(([k, v]) => (
                  <span key={k} style={{ padding: '2px 8px', background: colorFn(k), color: 'white', borderRadius: 4, fontSize: 11, fontWeight: 600 }}>{k}: {v}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* All parts flat — exam paper style */}
      <div style={{ background: 'white', borderRadius: 8, border: '1px solid #e5e7eb', padding: 24 }}>
        {paper.parts.map((pt, partIdx) => (
          <div key={partIdx} style={{ marginBottom: partIdx < paper.parts.length - 1 ? 32 : 0 }}>
            {/* Part header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14, paddingBottom: 10, borderBottom: '2px solid #e5e7eb' }}>
              <span style={{ fontSize: 15, fontWeight: 700, color: '#1e40af' }}>Part {pt.part}</span>
              <span style={{ fontSize: 13, color: '#6b7280' }}>({pt.marks_per_question} marks each · {pt.question_count} questions)</span>
            </div>
            {pt.questions.map((q, qi) => {
              const key = `${partIdx}-${qi}`;
              const isEditing = editingKey === key;
              const isRegen = regenLoading === key;
              return (
                <div key={qi} style={{ marginBottom: 10, padding: '12px 14px', background: qi % 2 === 0 ? '#f9fafb' : 'white', borderRadius: 8, border: '1px solid #e5e7eb' }}>
                  <div style={{ display: 'flex', gap: 6, marginBottom: isEditing ? 8 : 6, flexWrap: 'wrap', alignItems: 'center' }}>
                    <span style={{ fontSize: 13, fontWeight: 700, color: '#374151', minWidth: 26 }}>{q.q_no}.</span>
                    <Badge label={q.bloom} color={BT_COLORS[q.bloom]} />
                    <Badge label={`Unit ${q.unit}`} bg="#dbeafe" />
                    {q.co && <Badge label={q.co} bg="#d1fae5" />}
                    <span style={{ fontSize: 11, color: '#9ca3af' }}>{q.topic}</span>
                    <span style={{ marginLeft: 'auto', fontSize: 12, color: '#6b7280', fontWeight: 600 }}>[{q.marks}M]</span>
                    {!isEditing && (
                      <>
                        <button onClick={() => { setEditingKey(key); setEditText(q.question); }}
                          style={{ padding: '2px 9px', background: '#f3f4f6', border: '1px solid #d1d5db', borderRadius: 5, fontSize: 12, cursor: 'pointer', color: '#374151' }}>Edit</button>
                        <button onClick={() => handleRegen(partIdx, qi, { q_no: q.q_no, part: q.part, marks: q.marks, unit: q.unit, unit_title: q.unit_title, topic: q.topic, bloom: q.bloom, co: q.co })}
                          disabled={isRegen}
                          style={{ padding: '2px 9px', background: isRegen ? '#e5e7eb' : '#faf5ff', border: '1px solid #ddd6fe', borderRadius: 5, fontSize: 12, cursor: isRegen ? 'not-allowed' : 'pointer', color: '#6d28d9' }}>
                          {isRegen ? '...' : '↺ Regen'}
                        </button>
                      </>
                    )}
                  </div>
                  {isEditing ? (
                    <div>
                      <textarea value={editText} onChange={e => setEditText(e.target.value)} rows={3}
                        style={{ width: '100%', padding: '8px 10px', border: '1px solid #a78bfa', borderRadius: 6, fontSize: 14, fontFamily: 'inherit', resize: 'vertical', boxSizing: 'border-box' }} />
                      <div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
                        <button onClick={() => { updateQuestion(partIdx, qi, 'question', editText); setEditingKey(null); }}
                          style={{ padding: '4px 14px', background: '#8b5cf6', color: 'white', border: 'none', borderRadius: 5, fontSize: 12, cursor: 'pointer' }}>Save</button>
                        <button onClick={() => setEditingKey(null)}
                          style={{ padding: '4px 14px', background: '#f3f4f6', border: '1px solid #d1d5db', borderRadius: 5, fontSize: 12, cursor: 'pointer' }}>Cancel</button>
                      </div>
                    </div>
                  ) : (
                    <div style={{ fontSize: 14, color: '#1f2937', lineHeight: 1.65, paddingLeft: 26 }}>{q.question}</div>
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function GeneratePaper() {
  const navigate = useNavigate();
  const [userId, setUserId] = useState('');
  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState('');

  const [step, setStep] = useState(1); // 1=config, 2=slots, 3=paper
  const [coverPage, setCoverPage] = useState({
    assessment: 'Assessment Test – I',
    programme: 'MCA (R & SS)',
    course_code: '',
    course_title: '',
    date: '',
    semester: 'I / III Sem',
    regulation: '2023',
    duration: '1 hour 30 mins',
  });
  const [parts, setParts] = useState([
    { part: 'A', marks_per_question: 2, question_count: 10 },
    { part: 'B', marks_per_question: 13, question_count: 5 },
  ]);
  const [slotsData, setSlotsData] = useState(null);
  const [paper, setPaper] = useState(null);
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
  }, [navigate]);

  const handleBuildSlots = async () => {
    if (!selectedSubject) { setError('Select a subject'); return; }
    setError(''); setLoading(true);
    try {
      const res = await fetch(`${API}/generate/slots`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, domain_name: selectedSubject, parts }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail?.error || 'Failed');
      setSlotsData(data);
      setStep(2);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const handleGeneratePaper = async () => {
    setError(''); setLoading(true);
    try {
      const res = await fetch(`${API}/generate/paper`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, domain_name: selectedSubject, parts: slotsData.parts }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail?.error || 'Failed');
      setPaper(data);
      setStep(3);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  return (
    <ElicitLayout selectedSubject={selectedSubject} subjects={subjects} onSubjectChange={setSelectedSubject} userId={userId}>
      {/* Header + stepper */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 600, color: '#1f2937' }}>Generate Question Paper</h1>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          {[['1', 'Pattern'], ['2', 'Slots'], ['3', 'Paper']].map(([n, label], i) => (
            <div key={n} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 26, height: 26, borderRadius: '50%', background: step >= i + 1 ? '#8b5cf6' : '#e5e7eb', color: step >= i + 1 ? 'white' : '#9ca3af', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700 }}>{n}</div>
              <span style={{ fontSize: 13, color: step >= i + 1 ? '#6d28d9' : '#9ca3af', fontWeight: step === i + 1 ? 600 : 400 }}>{label}</span>
              {i < 2 && <span style={{ color: '#d1d5db', fontSize: 16 }}>›</span>}
            </div>
          ))}
        </div>
      </div>

      {error && <div style={{ marginBottom: 12, padding: '10px 14px', background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: 6, color: '#dc2626', fontSize: 13 }}>{error}</div>}

      {/* Step 1 */}
      {step === 1 && (
        <>
          <CoverPageEditor cover={coverPage} setCover={setCoverPage} />
          <PartConfigurator parts={parts} setParts={setParts} />
          <button onClick={handleBuildSlots} disabled={loading}
            style={{ padding: '10px 28px', background: loading ? '#9ca3af' : '#8b5cf6', color: 'white', border: 'none', borderRadius: 6, fontSize: 14, fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer' }}>
            {loading ? 'Loading...' : 'Next: Configure Slots →'}
          </button>
        </>
      )}

      {/* Step 2 */}
      {step === 2 && slotsData && (
        <>
          <button onClick={() => setStep(1)} style={{ marginBottom: 14, padding: '5px 14px', background: '#f3f4f6', border: '1px solid #d1d5db', borderRadius: 6, fontSize: 13, cursor: 'pointer', color: '#374151' }}>← Back</button>
          <SlotEditor slotsData={slotsData} onSlotsChange={setSlotsData} onGenerate={handleGeneratePaper} loading={loading} />
        </>
      )}

      {/* Step 3 */}
      {step === 3 && paper && (
        <>
          <button onClick={() => setStep(2)} style={{ marginBottom: 14, padding: '5px 14px', background: '#f3f4f6', border: '1px solid #d1d5db', borderRadius: 6, fontSize: 13, cursor: 'pointer', color: '#374151' }}>← Back to Slots</button>
          <GeneratedPaper paper={paper} userId={userId} domainName={selectedSubject} onPaperChange={setPaper} coverPage={coverPage} setCoverPage={setCoverPage} />
        </>
      )}
    </ElicitLayout>
  );
}
