const BLOOM_COLORS = {
  BT1: '#6b7280', BT2: '#3b82f6', BT3: '#10b981',
  BT4: '#f59e0b', BT5: '#ef4444', BT6: '#8b5cf6'
};

const BLOOM_LABELS = {
  BT1: 'Remember', BT2: 'Understand', BT3: 'Apply',
  BT4: 'Analyse', BT5: 'Evaluate', BT6: 'Create'
};

function ConfidenceBar({ label, value, color }) {
  const pct = Math.round((value || 0) * 100);
  const barColor = color || (pct >= 75 ? '#10b981' : pct >= 50 ? '#f59e0b' : '#ef4444');
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: 11, fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</span>
        <span style={{ fontSize: 12, fontWeight: 700, color: barColor }}>{pct}%</span>
      </div>
      <div style={{ height: 6, background: '#e5e7eb', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${pct}%`, background: barColor, borderRadius: 3, transition: 'width 0.5s ease' }} />
      </div>
    </div>
  );
}

export default function ResultCard({ data }) {
  const isOOS = data.out_of_syllabus || data.topic === 'Out of Syllabus';
  const bloomColor = BLOOM_COLORS[data.bloom_level] || '#6b7280';

  return (
    <div style={{ background: 'white', borderRadius: 8, border: '1px solid #e5e7eb', padding: 24 }}>
      <h2 style={{ margin: '0 0 20px 0', fontSize: 18, fontWeight: 600, color: '#1f2937' }}>Evaluation Result</h2>

      {/* Question */}
      <div style={{ marginBottom: 20, padding: 16, background: isOOS ? '#fef3c7' : '#f9fafb', borderRadius: 6, borderLeft: `3px solid ${isOOS ? '#f59e0b' : '#3b82f6'}` }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: '#6b7280', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Question</div>
        <div style={{ fontSize: 14, color: '#1f2937' }}>{data.question}</div>
        {isOOS && (
          <div style={{ marginTop: 8, display: 'inline-block', padding: '3px 10px', background: '#f59e0b', color: 'white', borderRadius: 4, fontSize: 11, fontWeight: 700 }}>
            OUT OF SYLLABUS
          </div>
        )}
      </div>

      {!isOOS && (
        <>
          {/* Score cards row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 20 }}>

            {/* Bloom Level */}
            <div style={{ padding: 16, background: '#f9fafb', borderRadius: 8, border: '1px solid #e5e7eb' }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#6b7280', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Bloom Level</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                <span style={{ padding: '4px 12px', background: bloomColor, color: 'white', borderRadius: 6, fontSize: 15, fontWeight: 700 }}>
                  {data.bloom_level}
                </span>
                <span style={{ fontSize: 12, color: '#6b7280' }}>{BLOOM_LABELS[data.bloom_level]}</span>
              </div>
              <ConfidenceBar label="Confidence" value={data.bloom_confidence} color={bloomColor} />
            </div>

            {/* Syllabus Match */}
            <div style={{ padding: 16, background: '#f9fafb', borderRadius: 8, border: '1px solid #e5e7eb' }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#6b7280', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Syllabus Match</div>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#1e40af', marginBottom: 4 }}>
                {data.unit ? `Unit ${data.unit}` : '—'}
              </div>
              <div style={{ fontSize: 12, color: '#374151', marginBottom: 12, minHeight: 16 }}>
                {data.topic || '—'}
              </div>
              <ConfidenceBar label="Match Score" value={data.topic_confidence} />
            </div>

            {/* Course Outcome */}
            <div style={{ padding: 16, background: '#f9fafb', borderRadius: 8, border: '1px solid #e5e7eb' }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#6b7280', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Course Outcome</div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 12, minHeight: 28 }}>
                {data.course_outcomes?.length > 0
                  ? data.course_outcomes.map(co => (
                      <span key={co} style={{ padding: '4px 12px', background: '#3b82f6', color: 'white', borderRadius: 12, fontSize: 13, fontWeight: 600 }}>{co}</span>
                    ))
                  : <span style={{ fontSize: 13, color: '#9ca3af' }}>—</span>
                }
              </div>
              <ConfidenceBar label="CO Confidence" value={data.co_confidence} color="#3b82f6" />
            </div>
          </div>

          {/* Unit title */}
          {data.unit_title && (
            <div style={{ marginBottom: 16, padding: '8px 12px', background: '#dbeafe', borderRadius: 6, fontSize: 13, color: '#1e40af' }}>
              {`Unit ${data.unit}: ${data.unit_title}`}
            </div>
          )}

          {/* Subtopics */}
          {data.subtopics?.length > 0 && (
            <div>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#6b7280', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Related Subtopics</div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {data.subtopics.map((st, i) => (
                  <span key={i} style={{ padding: '3px 10px', background: '#f3f4f6', border: '1px solid #e5e7eb', borderRadius: 12, fontSize: 12, color: '#374151' }}>{st}</span>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {data.warning && (
        <div style={{ marginTop: 16, padding: 12, background: '#fef3c7', border: '1px solid #fbbf24', borderRadius: 6, color: '#92400e', fontSize: 14 }}>
          {data.warning}
        </div>
      )}
    </div>
  );
}
