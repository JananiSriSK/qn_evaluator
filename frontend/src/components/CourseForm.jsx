import { useState } from 'react';
import { ingestCourse } from '../services/api';

/**
 * Form component for direct course ingestion
 * Processes syllabus directly into atomic subtopics without user review
 */
const CourseForm = () => {
  const [formData, setFormData] = useState({
    courseName: '',
    syllabus: '',
    courseOutcomes: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setError('');

    try {
      // Parse syllabus and course outcomes
      const syllabusLines = formData.syllabus.trim().split('\n\n');
      const syllabus = syllabusLines.map((unit, index) => {
        const lines = unit.split('\n');
        const title = lines[0] || `Unit ${index + 1}`;
        const content = lines.slice(1).join(' ') || lines[0];
        
        return {
          unit_number: index + 1,
          title: title.replace(/^Unit \d+:\s*/, ''),
          content: content
        };
      });

      const courseOutcomes = formData.courseOutcomes
        .trim()
        .split('\n')
        .filter(co => co.trim())
        .map((co, index) => ({
          id: `CO${index + 1}`,
          description: co.trim()
        }));

      const courseData = {
        course_name: formData.courseName,
        syllabus: syllabus,
        course_outcomes: courseOutcomes
      };

      const result = await ingestCourse(courseData);
      setMessage(`${result.message}. Units processed: ${result.units_processed}, Embeddings stored: ${result.embeddings_stored}`);
      
      // Clear form on success
      setFormData({ courseName: '', syllabus: '', courseOutcomes: '' });
      
    } catch (err) {
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h2>Course Ingestion</h2>
      <p>Upload course data for automatic atomic subtopic processing and CO mapping.</p>
      
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
          <label htmlFor="syllabus" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Syllabus (Unit-wise, separate units with double line breaks):
          </label>
          <textarea
            id="syllabus"
            value={formData.syllabus}
            onChange={(e) => setFormData({ ...formData, syllabus: e.target.value })}
            required
            rows={8}
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
            placeholder="Arrays and Linked Lists
Introduction to arrays, dynamic arrays, singly linked lists, doubly linked lists

Stacks and Queues
Stack operations, queue operations, circular queues, priority queues"
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label htmlFor="courseOutcomes" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Course Outcomes (one per line):
          </label>
          <textarea
            id="courseOutcomes"
            value={formData.courseOutcomes}
            onChange={(e) => setFormData({ ...formData, courseOutcomes: e.target.value })}
            required
            rows={4}
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
            placeholder="Understand fundamental data structures and their operations
Implement and analyze linear data structures
Apply appropriate data structures to solve problems"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          style={{
            backgroundColor: loading ? '#ccc' : '#007bff',
            color: 'white',
            padding: '10px 20px',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Processing...' : 'Process Course'}
        </button>
      </form>

      {message && (
        <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#d4edda', border: '1px solid #c3e6cb', borderRadius: '4px' }}>
          {message}
        </div>
      )}

      {error && (
        <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#f8d7da', border: '1px solid #f5c6cb', borderRadius: '4px' }}>
          {error}
        </div>
      )}
    </div>
  );
};

export default CourseForm;