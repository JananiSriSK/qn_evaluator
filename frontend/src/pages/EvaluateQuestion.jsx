import { useState, useEffect, useRef } from 'react';
import { api } from '../services/api-v2';
import ElicitLayout from '../components/ElicitLayout';

const EvaluateQuestion = () => {
  const [userId, setUserId] = useState('');
  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState('');
  const [question, setQuestion] = useState('');
  const [result, setResult] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const typingTimer = useRef(null);

  useEffect(() => {
    const id = localStorage.getItem('user_id');
    if (id) {
      setUserId(id);
      loadSubjects(id);
    }
  }, []);

  const loadSubjects = async (id) => {
    try {
      const data = await api.getDomains(id);
      setSubjects(data.domains);
      if (data.domains.length > 0) setSelectedSubject(data.domains[0]);
    } catch (err) {
      console.error('Failed to load subjects:', err);
    }
  };

  const handleQuestionChange = (e) => {
    const value = e.target.value;
    setQuestion(value);
    console.log("Question changed:", value);

    if (typingTimer.current) clearTimeout(typingTimer.current);

    if (value.length > 5 && selectedSubject && userId) {
      setPreviewLoading(true);
      console.log("Preview loading set to true");
      typingTimer.current = setTimeout(async () => {
        console.log("Preview API called");
        try {
          const response = await fetch('http://localhost:8002/evaluate/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              user_id: userId,
              domain_name: selectedSubject,
              question: value
            })
          });
          const data = await response.json();
          console.log("Preview data received:", data);
          setPreviewData(data);
          setPreviewLoading(false);
          console.log("Preview loading:", false);
          console.log("Preview data:", data);
        } catch (err) {
          console.error('Preview failed:', err);
          setPreviewLoading(false);
        }
      }, 400);
    } else {
      setPreviewData(null);
      setPreviewLoading(false);
    }
  };

  const handleKeyDown = async (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (question.length > 5 && selectedSubject && userId) {
        setPreviewLoading(false);
        try {
          const data = await api.evaluateQuestion(userId, selectedSubject, question);
          setResult(data);
        } catch (err) {
          console.error('Evaluation failed:', err);
        }
      }
    }
  };

  const getDifficultyColor = (score) => {
    if (score < 40) return '#10b981';
    if (score < 70) return '#f59e0b';
    return '#ef4444';
  };

  const getStrengthColor = (score) => {
    if (score <= 40) return '#9ca3af';
    if (score <= 70) return '#60a5fa';
    return '#1d4ed8';
  };

  const bloomColors = {
    BT1: '#6b7280', BT2: '#3b82f6', BT3: '#10b981',
    BT4: '#f59e0b', BT5: '#ef4444', BT6: '#8b5cf6'
  };

  const isOutOfSyllabus = result?.out_of_syllabus || result?.topic === 'Out of Syllabus';

  return (
    <ElicitLayout selectedSubject={selectedSubject} subjects={subjects} onSubjectChange={setSelectedSubject} userId={userId}>
      <div className="max-w-3xl mx-auto py-16 px-6">
        <textarea
          value={question}
          onChange={handleQuestionChange}
          onKeyDown={handleKeyDown}
          placeholder="Enter your question..."
          className="w-full h-40 p-4 text-base border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-400 focus:border-blue-400 resize-none"
        />
        
        <div className="text-xs text-gray-400 mt-2">
          Type a question to evaluate it automatically. Press Enter for full evaluation.
        </div>

        <div style={{ background: "yellow", padding: "10px", marginTop: "10px" }}>
          PREVIEW DEBUG ACTIVE
        </div>

        <pre style={{ marginTop: "10px", fontSize: "10px" }}>{JSON.stringify(previewData, null, 2)}</pre>

        {previewLoading && (
          <div className="mt-3 text-xs text-blue-500">
            Evaluating question strength...
          </div>
        )}

        {previewData && !result && (
          <div className="mt-4 flex items-center gap-6">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Difficulty</span>
              <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map((seg) => (
                  <div
                    key={seg}
                    className="w-4 h-2 rounded-sm"
                    style={{
                      backgroundColor: seg <= Math.ceil((previewData.difficulty_score / 100) * 5)
                        ? getDifficultyColor(previewData.difficulty_score)
                        : '#e5e7eb'
                    }}
                  />
                ))}
              </div>
              <span className="text-xs text-gray-600">{previewData.difficulty_score}</span>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Strength</span>
              <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full"
                  style={{
                    width: `${previewData.strength_score}%`,
                    backgroundColor: getStrengthColor(previewData.strength_score)
                  }}
                />
              </div>
              <span className="text-xs text-gray-600">{previewData.strength_score}</span>
            </div>
          </div>
        )}

        {result && (
          <div className="mt-12 space-y-6">
            <div>
              <div className="text-base font-semibold text-gray-900">{question}</div>
            </div>

            {!isOutOfSyllabus && result.bloom_level && (
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-500 w-28">Bloom Level</span>
                <span
                  className="px-3 py-1 rounded text-white text-sm font-medium"
                  style={{ backgroundColor: bloomColors[result.bloom_level] }}
                >
                  {result.bloom_level}
                </span>
                <span className="text-sm text-gray-500">
                  {(result.bloom_confidence * 100).toFixed(0)}%
                </span>
              </div>
            )}

            {(result.unit || result.topic) && (
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-500 w-28">Unit & Topic</span>
                <span className="text-sm text-gray-900">
                  {result.unit && `Unit ${result.unit}`}
                  {result.unit && result.topic && ' - '}
                  {result.topic}
                </span>
              </div>
            )}

            {result.course_outcomes && result.course_outcomes.length > 0 && (
              <div className="flex items-start gap-3">
                <span className="text-sm text-gray-500 w-28">Outcomes</span>
                <div className="flex gap-2 flex-wrap">
                  {result.course_outcomes.map(co => (
                    <span key={co} className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                      {co}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {isOutOfSyllabus && (
              <div className="mt-4 text-sm text-red-600">
                Question is outside syllabus scope.
              </div>
            )}
          </div>
        )}
      </div>
    </ElicitLayout>
  );
};

export default EvaluateQuestion;