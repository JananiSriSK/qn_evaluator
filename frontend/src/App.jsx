import { useState } from 'react';
import IngestCourse from './pages/IngestCourse';
import EvaluateQuestion from './pages/EvaluateQuestion';
import BookUploadForm from './components/BookUploadForm';

/**
 * Main Application Component
 * Provides tab-based navigation between course ingestion and question evaluation
 */
function App() {
  const [activeTab, setActiveTab] = useState('ingest');

  const tabStyle = (isActive) => ({
    padding: '10px 20px',
    margin: '0 5px',
    border: 'none',
    borderRadius: '4px 4px 0 0',
    backgroundColor: isActive ? '#007bff' : '#f8f9fa',
    color: isActive ? 'white' : '#333',
    cursor: 'pointer',
    fontSize: '16px'
  });

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
      {/* Header */}
      <header style={{ 
        backgroundColor: '#343a40', 
        color: 'white', 
        padding: '20px 0', 
        textAlign: 'center',
        marginBottom: '0'
      }}>
        <h1 style={{ margin: '0', fontSize: '28px' }}>Question Intelligence System</h1>
        <p style={{ margin: '5px 0 0 0', fontSize: '16px', opacity: '0.8' }}>
          Agent-based system for syllabus-aware Course Outcome mapping
        </p>
      </header>

      {/* Navigation Tabs */}
      <nav style={{ 
        backgroundColor: 'white', 
        padding: '0 20px',
        borderBottom: '1px solid #dee2e6'
      }}>
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
          <button
            onClick={() => setActiveTab('ingest')}
            style={tabStyle(activeTab === 'ingest')}
          >
            Course Ingestion
          </button>
          <button
            onClick={() => setActiveTab('evaluate')}
            style={tabStyle(activeTab === 'evaluate')}
          >
            Question Evaluation
          </button>
          <button
            onClick={() => setActiveTab('books')}
            style={tabStyle(activeTab === 'books')}
          >
            Reference Books
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <main style={{ backgroundColor: 'white', minHeight: 'calc(100vh - 140px)' }}>
        {activeTab === 'ingest' && <IngestCourse />}
        {activeTab === 'evaluate' && <EvaluateQuestion />}
        {activeTab === 'books' && <BookUploadForm />}
      </main>

      {/* Footer */}
      <footer style={{ 
        backgroundColor: '#f8f9fa', 
        textAlign: 'center', 
        padding: '15px',
        borderTop: '1px solid #dee2e6',
        fontSize: '14px',
        color: '#6c757d'
      }}>
        Academic Project - Agent-based Question Intelligence System
      </footer>
    </div>
  );
}

export default App;