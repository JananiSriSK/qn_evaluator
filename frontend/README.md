# Question Intelligence System - Frontend

Minimal React frontend for the Agent-based Question Intelligence System.

## Features

- **Course Ingestion**: Upload course data (name, syllabus, course outcomes)
- **Question Evaluation**: Evaluate questions against course content to predict Course Outcomes
- **Clean UI**: Academic-friendly interface with clear functionality
- **Real-time Results**: Displays CO predictions, relevance scores, and explainability data

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

3. Open browser to `http://localhost:3000`

## Usage

### Course Ingestion Tab
1. Enter course name
2. Add syllabus content (unit-wise, separate units with double line breaks)
3. Add course outcomes (one per line)
4. Click "Ingest Course" to process

### Question Evaluation Tab
1. Enter course name (must match ingested course)
2. Enter question text
3. Click "Evaluate Question" to get CO prediction
4. View results including:
   - Predicted Course Outcome
   - Relevance Score
   - Matched Syllabus Unit
   - Matched Context
   - Top semantic matches (explainability)

## Architecture

```
src/
├── pages/           # Main page components
├── components/      # Reusable UI components
├── services/        # API communication
├── App.jsx         # Main application with navigation
└── main.jsx        # Entry point
```

## Backend Integration

- Connects to backend API at `http://localhost:8001`
- Uses `/ingest-course` and `/evaluate-question` endpoints
- Handles loading states and error messages

## Academic Notes

- Minimal styling for clarity during evaluation
- Clean component structure for code review
- Clear separation of concerns (UI vs API logic)
- No complex state management - suitable for academic demonstration