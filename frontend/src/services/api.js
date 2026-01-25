// API service for communicating with the Question Intelligence System backend

const API_BASE_URL = 'http://localhost:8001';

/**
 * Ingest course data into the system
 * @param {Object} courseData - Course data with name, syllabus, and outcomes
 * @returns {Promise} API response
 */
export const ingestCourse = async (courseData) => {
  const response = await fetch(`${API_BASE_URL}/ingest-course`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(courseData),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to ingest course');
  }
  
  return response.json();
};

/**
 * Evaluate a question against course content
 * @param {Object} questionData - Question data with course name and question
 * @returns {Promise} API response with CO prediction
 */
export const evaluateQuestion = async (questionData) => {
  const response = await fetch(`${API_BASE_URL}/evaluate-question`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(questionData),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to evaluate question');
  }
  
  return response.json();
};

/**
 * Suggest subtopics for a syllabus unit
 * @param {Object} unitData - Unit data with course name, title, and content
 * @returns {Promise} API response with suggested subtopics
 */
export const suggestSubtopics = async (unitData) => {
  const response = await fetch(`${API_BASE_URL}/suggest-subtopics`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(unitData),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to suggest subtopics');
  }
  
  return response.json();
};

/**
 * Confirm subtopics and process with CO mapping
 * @param {Object} confirmationData - Confirmation data with final subtopics and COs
 * @returns {Promise} API response
 */
export const confirmSubtopics = async (confirmationData) => {
  const response = await fetch(`${API_BASE_URL}/confirm-subtopics`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(confirmationData),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to confirm subtopics');
  }
  
  return response.json();
};