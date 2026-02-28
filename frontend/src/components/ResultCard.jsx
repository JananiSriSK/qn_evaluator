export default function ResultCard({ data }) {
  const bloomColors = {
    BT1: '#6b7280', BT2: '#3b82f6', BT3: '#10b981',
    BT4: '#f59e0b', BT5: '#ef4444', BT6: '#8b5cf6'
  };

  const isOutOfSyllabus = data.out_of_syllabus || data.topic === 'Out of Syllabus';

  return (
    <div style={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', padding: '24px' }}>
      <h2 style={{ margin: '0 0 20px 0', fontSize: '18px', fontWeight: '600', color: '#1f2937' }}>Evaluation Result</h2>

      {/* Question */}
      <div style={{ marginBottom: '20px', padding: '16px', backgroundColor: isOutOfSyllabus ? '#fef3c7' : '#f9fafb', borderRadius: '6px', borderLeft: `3px solid ${isOutOfSyllabus ? '#f59e0b' : '#3b82f6'}` }}>
        <div style={{ fontSize: '12px', fontWeight: '500', color: '#6b7280', marginBottom: '6px' }}>QUESTION</div>
        <div style={{ fontSize: '14px', color: '#1f2937' }}>{data.question}</div>
        {isOutOfSyllabus && (
          <div style={{ marginTop: '8px', padding: '4px 10px', backgroundColor: '#f59e0b', color: 'white', borderRadius: '4px', fontSize: '11px', fontWeight: '600', display: 'inline-block' }}>
            OUT OF SYLLABUS
          </div>
        )}
      </div>

      {/* Bloom & Confidence - Only show if NOT out of syllabus */}
      {!isOutOfSyllabus && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
          <div>
            <div style={{ fontSize: '12px', fontWeight: '500', color: '#6b7280', marginBottom: '8px' }}>BLOOM LEVEL</div>
            <div style={{ display: 'inline-block', padding: '6px 16px', backgroundColor: bloomColors[data.bloom_level] || '#6b7280', color: 'white', borderRadius: '6px', fontSize: '16px', fontWeight: '600' }}>
              {data.bloom_level}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', fontWeight: '500', color: '#6b7280', marginBottom: '8px' }}>CONFIDENCE</div>
            <div style={{ fontSize: '24px', fontWeight: '600', color: '#1f2937' }}>
              {(data.bloom_confidence * 100).toFixed(1)}%
            </div>
          </div>
        </div>
      )}

      {/* Unit & Topic */}
      {(data.unit || data.topic) && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '16px', marginBottom: '20px' }}>
          {data.unit && (
            <div>
              <div style={{ fontSize: '12px', fontWeight: '500', color: '#6b7280', marginBottom: '8px' }}>UNIT</div>
              <div style={{ padding: '8px 12px', backgroundColor: '#dbeafe', borderRadius: '6px', fontSize: '14px', color: '#1e40af', fontWeight: '500' }}>
                Unit {data.unit}
              </div>
            </div>
          )}
          {data.topic && (
            <div>
              <div style={{ fontSize: '12px', fontWeight: '500', color: '#6b7280', marginBottom: '8px' }}>TOPIC</div>
              <div style={{ padding: '8px 12px', backgroundColor: '#dbeafe', borderRadius: '6px', fontSize: '14px', color: '#1e40af' }}>
                {data.topic}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Course Outcomes */}
      {data.course_outcomes && data.course_outcomes.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <div style={{ fontSize: '12px', fontWeight: '500', color: '#6b7280', marginBottom: '8px' }}>COURSE OUTCOMES</div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {data.course_outcomes.map(co => (
              <span key={co} style={{ padding: '4px 12px', backgroundColor: '#3b82f6', color: 'white', borderRadius: '12px', fontSize: '13px', fontWeight: '500' }}>
                {co}
              </span>
            ))}
          </div>
        </div>
      )}



      {/* Warning */}
      {data.warning && (
        <div style={{ marginTop: '20px', padding: '12px', backgroundColor: '#fef3c7', border: '1px solid #fbbf24', borderRadius: '6px', color: '#92400e', fontSize: '14px' }}>
          ⚠️ {data.warning}
        </div>
      )}
    </div>
  );
}
