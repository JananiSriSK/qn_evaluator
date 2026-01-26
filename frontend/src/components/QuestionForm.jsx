import { useState } from 'react';
import { evaluateQuestion } from '../services/api';

/**
 * Form component for question evaluation
 * Handles question input and displays CO prediction results
 */
const QuestionForm = () => {
  const [formData, setFormData] = useState({
    courseName: '',
    question: ''
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setError('');

    try {
      const questionData = {
        course_name: formData.courseName,
        question: formData.question
      };

      const evaluationResult = await evaluateQuestion(questionData);
      setResult(evaluationResult);
      
    } catch (err) {
      setError(` Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h2>Question Evaluation</h2>
      <p>Evaluate questions against course content to predict Course Outcomes.</p>
      
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '15px' }}>
          <label htmlFor="courseName" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Course Name:
          </label>
          <input
            type="text"
            id="courseName"
            value={formData.courseName}
            onChange={(e) => setFormData({ ...formData, courseName: e.target.value })}
            required
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
            placeholder="e.g., Data Structures"
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label htmlFor="question" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Question:
          </label>
          <textarea
            id="question"
            value={formData.question}
            onChange={(e) => setFormData({ ...formData, question: e.target.value })}
            required
            rows={4}
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
            placeholder="e.g., Explain the implementation of a stack using arrays and discuss its time complexity"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          style={{
            backgroundColor: loading ? '#ccc' : '#28a745',
            color: 'white',
            padding: '10px 20px',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Evaluating...' : 'Evaluate Question'}
        </button>
      </form>

      {error && (
        <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#f8d7da', border: '1px solid #f5c6cb', borderRadius: '4px' }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f8f9fa', border: '1px solid #dee2e6', borderRadius: '4px' }}>
          <h3>Evaluation Results</h3>
          
          {result.out_of_syllabus ? (
            <div style={{ padding: '15px', backgroundColor: '#fff3cd', border: '1px solid #ffeaa7', borderRadius: '4px' }}>
              <div style={{ marginBottom: '10px' }}>
                <strong>Scope Check:</strong> Out of syllabus
              </div>
              <div style={{ marginBottom: '10px', color: '#856404' }}>
                {result.reason}
              </div>
            </div>
          ) : (
            <>
              <div style={{ marginBottom: '15px', padding: '10px', backgroundColor: '#d4edda', border: '1px solid #c3e6cb', borderRadius: '4px' }}>
                <div style={{ marginBottom: '5px' }}>
                  <strong>Scope Check:</strong> In syllabus
                </div>
              </div>

              <div style={{ marginBottom: '15px' }}>
                <strong>FAISS Similarity Score:</strong> {result.similarity_score !== undefined ? result.similarity_score : 'N/A'}
              </div>

              <div style={{ marginBottom: '15px' }}>
                <strong>Predicted Course Outcome:</strong>
                <div style={{ marginTop: '5px', padding: '12px', backgroundColor: '#d1ecf1', borderRadius: '4px', fontSize: '16px' }}>
                  {result.predicted_co}
                </div>
              </div>

              <div style={{ marginBottom: '15px' }}>
                <strong>Matched Syllabus Unit:</strong>
                <div style={{ marginTop: '5px', padding: '10px', backgroundColor: '#fff3cd', borderRadius: '4px' }}>
                  {result.matched_unit}
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default QuestionForm;