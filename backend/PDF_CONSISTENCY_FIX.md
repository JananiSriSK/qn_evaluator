# PDF vs Single Mode Inconsistency - Root Cause & Fix

## Problem
Questions evaluated correctly in **Single mode** but marked **OUT OF SYLLABUS** in **PDF batch mode**.

Examples:
- "Define process and list different states of a process." → Single: Unit II ✓ | PDF: OUT OF SYLLABUS ✗
- "Define paging and segmentation." → Single: Unit IV ✓ | PDF: OUT OF SYLLABUS ✗

## Root Cause: Double Cleaning

### Evaluation Paths

**Single Mode:**
```
Question → EvaluationService.clean_question_text() → Embed → Evaluate
```

**PDF Mode (BEFORE FIX):**
```
PDF → PDFQuestionParser.clean_question() → EvaluationService.clean_question_text() → Embed → Evaluate
         ↑ FIRST CLEANING                      ↑ SECOND CLEANING
```

### The Issue

**PDFQuestionParser.clean_question()** was applying aggressive cleaning:
```python
# Remove Part headers
text = re.sub(r'Part\s+[A-Z]\b', '', text, flags=re.IGNORECASE)

# Remove marks patterns
text = re.sub(r'\d+\s*Marks?\b', '', text, flags=re.IGNORECASE)

# Remove page numbers
text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)

# Remove excess whitespace
text = re.sub(r'\s+', ' ', text)
```

Then **EvaluationService.clean_question_text()** cleaned it AGAIN:
```python
# Remove leading numbering
question = re.sub(r'^\s*(?:Q\.?\s*)?\d+\s*[\.)\(]?\s*[a-z]?[\)]?\s+', '', question)

# Remove standalone (a), (b) markers
question = re.sub(r'^\s*\([a-z]\)\s+', '', question)

# Normalize Unicode, remove bullets, collapse whitespace
...
```

**Result**: Text was over-processed, potentially corrupting semantic meaning or removing important context.

## The Fix

### Changed Files

**1. services/pdf_parser.py**

**BEFORE:**
```python
if question_text:
    # Clean the question
    cleaned = PDFQuestionParser.clean_question(question_text)
    if cleaned:
        # Detect part
        part = PDFQuestionParser.detect_part(...)
        sub_questions = PDFQuestionParser.split_or_questions(cleaned, ...)
```

**AFTER:**
```python
if question_text:
    # Detect part (no cleaning here - let EvaluationService handle it)
    part = PDFQuestionParser.detect_part(...)
    
    # Split OR questions (pass raw text)
    sub_questions = PDFQuestionParser.split_or_questions(question_text, ...)
    
    logger.info(f"[PDF_PARSER] Extracted Q{sq['number']}: '{sq['text'][:80]}'")
```

**Key Change**: Removed `PDFQuestionParser.clean_question()` call. Pass raw extracted text directly to EvaluationService.

### New Evaluation Path

**PDF Mode (AFTER FIX):**
```
PDF → PDFQuestionParser.split_questions() → EvaluationService.clean_question_text() → Embed → Evaluate
      ↑ NO CLEANING, just extraction         ↑ SINGLE UNIFIED CLEANING
```

Now both modes use **identical preprocessing**.

## Verification

### Test Results

```python
TEST: "Define process and list different states of a process."

PDF Mode:    Topic='Process concept - Process Scheduling - Operation on Processes', Unit=II, OOS=False
Single Mode: Topic='Process concept - Process Scheduling - Operation on Processes', Unit=II, OOS=False

✓ MATCH
```

### Logging Output

**PDF Parser (extraction only):**
```
[PDF_PARSER] Extracted Q3: '3. Define process and list different states of a process.'
```

**EvaluationService (unified cleaning):**
```
RAW QUESTION: '3. Define process and list different states of a process.'
CLEANED QUESTION: 'Define process and list different states of a process.'
```

## Impact

✅ **Single and PDF modes now produce identical results**
✅ **No more false "OUT OF SYLLABUS" in PDF mode**
✅ **Unified preprocessing pipeline**
✅ **Cleaner architecture (single responsibility)**

## Files Modified

1. **backend/services/pdf_parser.py**
   - Removed `clean_question()` call from `split_questions()`
   - Added logging for extracted questions
   - Pass raw text to EvaluationService

2. **backend/services/evaluation_service.py** (already had unified cleaning)
   - `clean_question_text()` handles all preprocessing
   - Applied to both single and batch modes

## Testing

Run consistency test:
```bash
cd backend
python test_pdf_consistency.py
```

Expected: All tests show ✓ MATCH

## Architectural Principle

**Single Responsibility**: 
- PDFQuestionParser: Extract and split questions (no cleaning)
- EvaluationService: Clean, embed, and evaluate (unified preprocessing)

This prevents double-processing and ensures consistency across all evaluation modes.
