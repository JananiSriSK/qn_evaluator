import { useState } from 'react';

export default function EvaluationResult({ result }) {
  if (result.type === 'single') {
    return <SingleResult data={result.data} />;
  }
  return <PdfResults data={result.data} />;
}

function SingleResult({ data }) {
  const [showChunks, setShowChunks] = useState(false);

  const bloomColors = {
    BT1: '#28a745', BT2: '#17a2b8', BT3: '#ffc107',
    BT4: '#fd7e14', BT5: '#dc3545', BT6: '#6f42c1'
  };

  return (
    <div style={{ backgroundColor: 'white', padding: '30px', borderRadius: '8px' }}>
      <h2 style={{ marginBottom: '20px', borderBottom: '2px solid #007bff', paddingBottom: '10px' }}>Evaluation Result</h2>

      {/* Question */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ fontWeight: 'bold', marginBottom: '5px', color: '#666' }}>Question:</div>
        <div style={{ padding: '10px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>{data.question}</div>
      </div>

      {/* Bloom Level */}
      <div style={{ display: 'flex', gap: '20px', marginBottom: '20px' }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 'bold', marginBottom: '5px', color: '#666' }}>Bloom Level:</div>
          <div style={{ padding: '15px', backgroundColor: bloomColors[data.bloom_level] || '#6c757d', color: 'white', borderRadius: '4px', fontSize: '20px', fontWeight: 'bold', textAlign: 'center' }}>
            {data.bloom_level}
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 'bold', marginBottom: '5px', color: '#666' }}>Confidence:</div>
          <div style={{ padding: '15px', backgroundColor: '#e9ecef', borderRadius: '4px', fontSize: '20px', fontWeight: 'bold', textAlign: 'center' }}>
            {(data.bloom_confidence * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Unit & Topic */}
      {(data.unit || data.topic) && (
        <div style={{ display: 'flex', gap: '20px', marginBottom: '20px' }}>
          {data.unit && (
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 'bold', marginBottom: '5px', color: '#666' }}>Unit:</div>
              <div style={{ padding: '10px', backgroundColor: '#d1ecf1', borderRadius: '4px', border: '1px solid #bee5eb' }}>{data.unit}</div>
            </div>
          )}
          {data.topic && (
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 'bold', marginBottom: '5px', color: '#666' }}>Topic:</div>
              <div style={{ padding: '10px', backgroundColor: '#d1ecf1', borderRadius: '4px', border: '1px solid #bee5eb' }}>{data.topic}</div>
            </div>
          )}
        </div>
      )}

      {/* Course Outcomes */}
      {data.course_outcomes && data.course_outcomes.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <div style={{ fontWeight: 'bold', marginBottom: '5px', color: '#666' }}>Course Outcomes:</div>
          <div style={{ display: 'flex', gap: '10px' }}>
            {data.course_outcomes.map(co => (
              <span key={co} style={{ padding: '5px 15px', backgroundColor: '#007bff', color: 'white', borderRadius: '20px', fontSize: '14px' }}>{co}</span>
            ))}
          </div>
        </div>
      )}

      {/* Subtopics */}
      {data.subtopics && data.subtopics.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <div style={{ fontWeight: 'bold', marginBottom: '5px', color: '#666' }}>Subtopics:</div>
          <ul style={{ margin: 0, paddingLeft: '20px' }}>
            {data.subtopics.map((st, i) => <li key={i} style={{ marginBottom: '5px' }}>{st}</li>)}
          </ul>
        </div>
      )}

      {/* Warning if no syllabus match */}
      {data.warning && (
        <div style={{ padding: '15px', backgroundColor: '#fff3cd', border: '1px solid #ffc107', borderRadius: '4px', marginBottom: '20px', color: '#856404' }}>
          ⚠️ {data.warning}
        </div>
      )}
    </div>
  );
}

function PdfResults({ data }) {
  return (
    <div style={{ backgroundColor: 'white', padding: '30px', borderRadius: '8px' }}>
      <h2 style={{ marginBottom: '20px', borderBottom: '2px solid #007bff', paddingBottom: '10px' }}>
        PDF Evaluation Results ({data.total_questions} questions)
      </h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        {data.results && data.results.map((r, i) => (
          <div key={i} style={{ padding: '15px', border: '1px solid #ddd', borderRadius: '4px', backgroundColor: r.error ? '#f8d7da' : '#f8f9fa' }}>
            {r.error ? (
              <>
                <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>Q{r.question_number}: Error</div>
                <div style={{ color: '#721c24' }}>{r.error}</div>
              </>
            ) : (
              <>
                <div style={{ fontWeight: 'bold', marginBottom: '10px' }}>Q{r.question_number}: {r.question}</div>
                <div style={{ display: 'flex', gap: '15px', fontSize: '14px' }}>
                  <span><strong>Bloom:</strong> {r.bloom_level} ({(r.bloom_confidence * 100).toFixed(0)}%)</span>
                  <span><strong>Unit:</strong> {r.unit}</span>
                  <span><strong>Topic:</strong> {r.topic}</span>
                  <span><strong>COs:</strong> {r.course_outcomes ? r.course_outcomes.join(', ') : 'N/A'}</span>
                </div>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
