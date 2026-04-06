const API_BASE_URL = 'http://localhost:8002';

export const api = {
  // Domain Management
  createDomain: async (userId, domainName) => {
    const res = await fetch(`${API_BASE_URL}/domains/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, domain_name: domainName })
    });
    if (!res.ok) throw new Error((await res.json()).error);
    return res.json();
  },

  getDomains: async (userId) => {
    const res = await fetch(`${API_BASE_URL}/domains/${userId}`);
    if (!res.ok) throw new Error((await res.json()).error);
    return res.json();
  },

  deleteDomain: async (userId, domainName) => {
    const res = await fetch(`${API_BASE_URL}/domains/${userId}/${domainName}`, {
      method: 'DELETE'
    });
    if (!res.ok) throw new Error((await res.json()).error);
    return res.json();
  },

  // Syllabus & Books
  uploadSyllabus: async (userId, domainName, file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE_URL}/domains/${userId}/${domainName}/syllabus`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error((await res.json()).error);
    return res.json();
  },

  uploadBooks: async (userId, domainName, files) => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    const res = await fetch(`${API_BASE_URL}/domains/${userId}/${domainName}/books`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error((await res.json()).error);
    return res.json();
  },

  getDomainStatus: async (userId, domainName) => {
    const res = await fetch(`${API_BASE_URL}/domains/${userId}/${domainName}/status`);
    if (!res.ok) throw new Error((await res.json()).error);
    return res.json();
  },

  // Evaluation
  evaluateQuestion: async (userId, domainName, question) => {
    const res = await fetch(`${API_BASE_URL}/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, domain_name: domainName, question })
    });
    if (!res.ok) throw new Error((await res.json()).error);
    return res.json();
  },

  evaluatePdf: async (userId, domainName, file) => {
    const formData = new FormData();
    formData.append('user_id', userId);
    formData.append('domain_name', domainName);
    formData.append('file', file);
    const res = await fetch(`${API_BASE_URL}/evaluate/pdf`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error((await res.json()).error);
    return res.json();
  },

  // History
  getHistory: async (userId) => {
    const res = await fetch(`${API_BASE_URL}/history/${userId}`);
    if (!res.ok) throw new Error((await res.json()).error);
    return res.json();
  },

  deleteSingleQuestion: async (userId, questionId) => {
    const res = await fetch(`${API_BASE_URL}/history/${userId}/single/${questionId}`, {
      method: 'DELETE'
    });
    if (!res.ok) throw new Error((await res.json()).error);
    return res.json();
  },

  deletePdfEvaluation: async (userId, evalId) => {
    const res = await fetch(`${API_BASE_URL}/history/${userId}/pdf/${evalId}`, {
      method: 'DELETE'
    });
    if (!res.ok) throw new Error((await res.json()).error);
    return res.json();
  },

  clearAllHistory: async (userId) => {
    const res = await fetch(`${API_BASE_URL}/history/${userId}/clear`, {
      method: 'DELETE'
    });
    if (!res.ok) throw new Error((await res.json()).error);
    return res.json();
  },

  getPdfEvaluationResults: async (userId, evalId) => {
    const res = await fetch(`${API_BASE_URL}/history/${userId}/pdf/${evalId}`);
    if (!res.ok) throw new Error((await res.json()).error);
    return res.json();
  },

  runMetrics: async (userId, domainName, labeledData) => {
    const res = await fetch(`${API_BASE_URL}/metrics/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, domain_name: domainName, labeled_data: labeledData })
    });
    if (!res.ok) throw new Error((await res.json()).error);
    return res.json();
  },

  generateAdaptive: async (userId, domainName, results) => {
    const res = await fetch(`${API_BASE_URL}/adaptive/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, domain_name: domainName, results })
    });
    if (!res.ok) throw new Error((await res.json()).error);
    return res.json();
  }
};
