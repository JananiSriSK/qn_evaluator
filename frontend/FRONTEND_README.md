# Question Intelligence System - Frontend

React + Vite frontend for the Question Intelligence System.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

The app will run on `http://localhost:5173`

## Features

- **Login**: Simple user ID-based login (stored in localStorage)
- **Dashboard**: Domain management with sidebar navigation
- **Domain Setup**: Upload syllabus and books with progress tracking
- **Evaluation**: Single question or PDF batch evaluation
- **Results Display**: Clean academic layout with Bloom taxonomy visualization

## Workflow

1. Login with user ID
2. Create or select domain
3. Upload syllabus (PDF/TXT)
4. Upload books (multiple PDFs)
5. Wait for indexing to complete
6. Navigate to evaluation page
7. Evaluate questions and view results

## API Integration

Backend must be running on `http://localhost:8002`

See `src/services/api-v2.js` for all API endpoints.

## Project Structure

```
src/
├── components/
│   ├── DomainSetup.jsx       # Domain setup with status tracking
│   ├── EvaluationResult.jsx  # Result display component
│   └── FileUpload.jsx        # Reusable file upload component
├── pages/
│   ├── Login.jsx             # Login page
│   ├── Dashboard.jsx         # Main dashboard with domain list
│   └── Evaluate.jsx          # Evaluation page (single/PDF)
├── services/
│   └── api-v2.js             # API service layer
├── App.jsx                   # Main app with routing
└── main.jsx                  # Entry point
```

## Build for Production

```bash
npm run build
```

Output will be in `dist/` directory.
