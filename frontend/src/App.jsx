import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import EvaluateV2 from './pages/EvaluateV2';
import History from './pages/History';
import PdfResults from './pages/PdfResults';
import ManageSubjects from './pages/ManageSubjects';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/evaluate" element={<EvaluateV2 />} />
        <Route path="/history" element={<History userId={localStorage.getItem('user_id')} />} />
        <Route path="/manage" element={<ManageSubjects />} />
        <Route path="/results/:evalId" element={<PdfResults />} />
        <Route path="/" element={<Navigate to="/evaluate" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
