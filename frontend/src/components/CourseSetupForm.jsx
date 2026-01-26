import { useState } from 'react';
import { ingestCourse } from '../services/api';

/**
 * Combined Course Setup Form
 * Handles book upload first, then syllabus ingestion for optimal densification
 */
const CourseSetupForm = () => {
  const [step, setStep] = useState(1); // 1: Book Upload, 2: Syllabus Input
  const [courseName, setCourseName] = useState('');
  
  // Book upload state
  const [bookData, setBookData] = useState({
    bookName: ''
  });
  const [selectedFile, setSelectedFile] = useState(null);
  const [bookUploaded, setBookUploaded] = useState(false);
  
  // Syllabus state
  const [syllabusData, setSyllabusData] = useState({
    syllabus: '',
    courseOutcomes: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setError('');
    } else {
      setSelectedFile(null);
      setError('Please select a PDF file');
    }
  };

  const handleBookUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile || !courseName || !bookData.bookName) {
      setError('Please fill all fields and select a PDF file');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('file', selectedFile);
      formDataToSend.append('course_name', courseName);
      formDataToSend.append('book_name', bookData.bookName);

      const response = await fetch('http://localhost:8001/process-book', {
        method: 'POST',
        body: formDataToSend,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to process book');
      }

      const result = await response.json();
      setMessage(`Book uploaded successfully! Processed ${result.chunks_processed} chunks.`);
      setBookUploaded(true);
      setStep(2); // Move to syllabus step
      
    } catch (err) {
      setError(`Book upload error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSyllabusSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Parse syllabus and course outcomes
      const syllabusLines = syllabusData.syllabus.trim().split('\n\n');
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

      const courseOutcomes = syllabusData.courseOutcomes
        .trim()
        .split('\n')
        .filter(co => co.trim())
        .map((co, index) => ({
          id: `CO${index + 1}`,
          description: co.trim()
        }));

      const courseData = {
        course_name: courseName,
        syllabus: syllabus,
        course_outcomes: courseOutcomes
      };

      const result = await ingestCourse(courseData);
      setMessage(`Course setup completed! Units processed: ${result.units_processed}, Embeddings stored: ${result.embeddings_stored}. ${bookUploaded ? 'Book-enhanced densification applied.' : ''}`);
      
      // Reset form
      setStep(1);
      setCourseName('');
      setBookData({ bookName: '' });
      setSelectedFile(null);
      setBookUploaded(false);
      setSyllabusData({ syllabus: '', courseOutcomes: '' });
      
    } catch (err) {
      setError(`Syllabus processing error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const skipBookUpload = () => {
    setStep(2);
    setMessage('Proceeding with syllabus-only processing (no book densification)');
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h2>Course Setup</h2>
      <p>Set up your course with optimal book-enhanced densification. Upload reference book first, then add syllabus.</p>
      
      {/* Progress Indicator */}
      <div style={{ marginBottom: '30px', display: 'flex', alignItems: 'center' }}>
        <div style={{ 
          padding: '8px 16px', 
          backgroundColor: step >= 1 ? '#007bff' : '#e9ecef', 
          color: step >= 1 ? 'white' : '#6c757d',
          borderRadius: '20px',
          marginRight: '10px'
        }}>
          1. Reference Book {bookUploaded && 'DONE'}
        </div>
        <div style={{ width: '30px', height: '2px', backgroundColor: '#e9ecef', marginRight: '10px' }}></div>
        <div style={{ 
          padding: '8px 16px', 
          backgroundColor: step >= 2 ? '#007bff' : '#e9ecef', 
          color: step >= 2 ? 'white' : '#6c757d',
          borderRadius: '20px'
        }}>
          2. Syllabus & COs
        </div>
      </div>

      {/* Step 1: Book Upload */}
      {step === 1 && (
        <div>
          <h3>Step 1: Upload Reference Book (Recommended)</h3>
          <p>Upload a PDF reference book to enhance syllabus understanding through densification.</p>
          
          <form onSubmit={handleBookUpload}>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Course Name:
              </label>
              <input
                type="text"
                value={courseName}
                onChange={(e) => setCourseName(e.target.value)}
                required
                style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
                placeholder="e.g., INTRODUCTION TO OPERATING SYSTEM"
              />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Book Name:
              </label>
              <input
                type="text"
                value={bookData.bookName}
                onChange={(e) => setBookData({ ...bookData, bookName: e.target.value })}
                required
                style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
                placeholder="e.g., Operating System Concepts 9th Edition"
              />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                PDF File:
              </label>
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                required
                style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
              />
              {selectedFile && (
                <div style={{ marginTop: '5px', fontSize: '14px', color: '#666' }}>
                  Selected: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                </div>
              )}
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                type="submit"
                disabled={loading || !selectedFile}
                style={{
                  backgroundColor: loading || !selectedFile ? '#ccc' : '#007bff',
                  color: 'white',
                  padding: '10px 20px',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: loading || !selectedFile ? 'not-allowed' : 'pointer'
                }}
              >
                {loading ? 'Uploading...' : 'Upload Book & Continue'}
              </button>
              
              <button
                type="button"
                onClick={skipBookUpload}
                style={{
                  backgroundColor: '#6c757d',
                  color: 'white',
                  padding: '10px 20px',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Skip Book (Syllabus Only)
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Step 2: Syllabus Input */}
      {step === 2 && (
        <div>
          <h3>Step 2: Add Syllabus & Course Outcomes</h3>
          <p>
            Course: <strong>{courseName}</strong>
            {bookUploaded && <span style={{ color: '#28a745', marginLeft: '10px' }}>Book-enhanced processing enabled</span>}
          </p>
          
          <form onSubmit={handleSyllabusSubmit}>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Syllabus (Unit-wise, separate units with double line breaks):
              </label>
              <textarea
                value={syllabusData.syllabus}
                onChange={(e) => setSyllabusData({ ...syllabusData, syllabus: e.target.value })}
                required
                rows={8}
                style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
                placeholder="UNIT I: INTRODUCTION TO OPERATING SYSTEM
Operating System Definition, Functions, Types of Operating Systems

UNIT II: PROCESS MANAGEMENT  
Process Concept, Process States, Process Control Block"
              />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Course Outcomes (one per line):
              </label>
              <textarea
                value={syllabusData.courseOutcomes}
                onChange={(e) => setSyllabusData({ ...syllabusData, courseOutcomes: e.target.value })}
                required
                rows={4}
                style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
                placeholder="Understand the fundamental concepts of operating systems
Analyze process management and synchronization techniques
Design and implement memory management schemes"
              />
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
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
                {loading ? 'Processing...' : 'Complete Course Setup'}
              </button>
              
              <button
                type="button"
                onClick={() => setStep(1)}
                style={{
                  backgroundColor: '#6c757d',
                  color: 'white',
                  padding: '10px 20px',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Back to Book Upload
              </button>
            </div>
          </form>
        </div>
      )}

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

export default CourseSetupForm;