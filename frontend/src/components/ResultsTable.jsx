import { useState } from 'react';

export default function ResultsTable({ data, subjectName }) {
  const [downloading, setDownloading] = useState(false);
  const [reportType, setReportType] = useState('mapping');
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
            bloom_level: r.bloom_level
          })),
          format,
          type: reportType
        })
      });

      if (!response.ok) throw new Error('Download failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${subjectName}.${format}`;
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
                  <th style={{ padding: '14px 16px', textAlign: 'left', fontWeight: '600', color: '#374151', borderBottom: '2px solid #e5e7eb' }}>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {groupedByPart[part].map((r, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #e5e7eb', backgroundColor: r.out_of_syllabus ? '#fef3c7' : 'white' }}>
                    <td style={{ padding: '14px 16px', color: '#6b7280', fontWeight: '500' }}>{r.question_number}</td>
                    <td style={{ padding: '14px 16px', color: '#1f2937', maxWidth: '350px' }}>
                      {r.question?.substring(0, 100)}{r.question?.length > 100 ? '...' : ''}
                      {r.out_of_syllabus && <span style={{ marginLeft: '8px', padding: '2px 8px', backgroundColor: '#f59e0b', color: 'white', borderRadius: '4px', fontSize: '11px', fontWeight: '600' }}>OUT OF SYLLABUS</span>}
                    </td>
                    <td style={{ padding: '14px 16px', color: '#1f2937', fontWeight: '500' }}>{r.unit || '-'}</td>
                    <td style={{ padding: '14px 16px', color: '#6b7280', maxWidth: '200px' }}>{r.unit_title || '-'}</td>
                    <td style={{ padding: '14px 16px', color: '#1f2937', fontWeight: '500' }}>{r.course_outcomes?.join(', ') || '-'}</td>
                    <td style={{ padding: '14px 16px' }}>
                      {!r.out_of_syllabus && (
                        <span style={{ padding: '4px 10px', backgroundColor: getBloomColor(r.bloom_level), color: 'white', borderRadius: '4px', fontSize: '12px', fontWeight: '600' }}>
                          {r.bloom_level || 'N/A'}
                        </span>
                      )}
                      {r.out_of_syllabus && <span style={{ color: '#9ca3af' }}>-</span>}
                    </td>
                    <td style={{ padding: '14px 16px', color: '#1f2937', fontWeight: '500' }}>
                      {!r.out_of_syllabus && (r.bloom_confidence ? `${(r.bloom_confidence * 100).toFixed(0)}%` : 'N/A')}
                      {r.out_of_syllabus && <span style={{ color: '#9ca3af' }}>-</span>}
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
