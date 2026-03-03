# Single vs Batch Evaluation Consistency Fix

## Problem
Questions evaluated in **single mode** vs **PDF batch mode** produced different results:
- Single: "Define paging and segmentation." → Unit IV (Paging)
- Batch: "3. Define paging and segmentation." → OUT OF SYLLABUS

## Root Cause
**Inconsistent text preprocessing** between the two evaluation paths:
1. Single mode: Question passed directly to `evaluate_question()`
2. Batch mode: PDF extraction added numbering ("3. "), but cleaning regex was too aggressive

The regex pattern `r'^\s*(?:Q\.?\s*)?\d+\s*[\.)\(]?\s*[a-z]?[\)]?\s*'` was removing the first letter after the number because it didn't require whitespace after the pattern.

Example:
- Input: "3. Define paging..."
- Buggy output: "efine paging..." (removed "D")
- Fixed output: "Define paging..."

## Solution

### 1. Added Unified Preprocessing Method
```python
@staticmethod
def clean_question_text(question: str) -> str:
    """Unified preprocessing for both single and batch evaluation"""
    # Normalize Unicode
    question = unicodedata.normalize('NFKC', question)
    
    # Remove leading numbering (FIXED: requires whitespace after pattern)
    question = re.sub(r'^\s*(?:Q\.?\s*)?\d+\s*[\.)\(]?\s*[a-z]?[\)]?\s+', '', question, flags=re.IGNORECASE)
    
    # Remove bullets
    question = re.sub(r'^\s*[•●○■□▪▫]\s+', '', question)
    
    # Remove marks patterns
    question = re.sub(r'\(\d+\s*[×x]\s*\d+\s*=\s*\d+\s*Marks?\)', '', question, flags=re.IGNORECASE)
    question = re.sub(r'\d+\s*Marks?\b', '', question, flags=re.IGNORECASE)
    
    # Strip extra whitespace
    question = re.sub(r'\s+', ' ', question).strip()
    
    return question
```

### 2. Applied to Both Evaluation Paths
- **Single mode**: `evaluate_question()` calls `clean_question_text()` first
- **Batch mode**: `evaluate_question()` calls `clean_question_text()` first (same path)

### 3. Enhanced Logging
Added detailed logging to track:
- Cleaned question text
- Cross-encoder scores for all candidates
- Best match selection
- Threshold comparison
- Accept/reject decision

## Test Results

### Before Fix
```
Original: 'Define paging and segmentation.'
Cleaned:  'Define paging and segmentation.'
PDF extracted: '3. Define paging and segmentation.'
Cleaned:       'efine paging and segmentation.'  ❌ WRONG
Match: False
```

### After Fix
```
Original: 'Define paging and segmentation.'
Cleaned:  'Define paging and segmentation.'
PDF extracted: '3. Define paging and segmentation.'
Cleaned:       'Define paging and segmentation.'  ✓ CORRECT
Match: True
```

## Files Modified

1. **backend/services/evaluation_service.py**
   - Added `clean_question_text()` static method
   - Applied cleaning at start of `evaluate_question()`
   - Enhanced logging in `select_best_topic_global()`

2. **backend/main_v2.py**
   - Added logging for PDF extraction count
   - Clarified that unified cleaning is applied

3. **backend/test_consistency.py** (new)
   - Test script to verify single vs batch consistency

## Key Changes

### Regex Fix
Changed from:
```python
r'^\s*(?:Q\.?\s*)?\d+\s*[\.)\(]?\s*[a-z]?[\)]?\s*'
```

To:
```python
r'^\s*(?:Q\.?\s*)?\d+\s*[\.)\(]?\s*[a-z]?[\)]?\s+'
```

The key difference: `\s+` (one or more spaces) instead of `\s*` (zero or more spaces) at the end.

This ensures the pattern only matches when there's actual whitespace after the numbering, preventing it from consuming the first letter of the question.

## Verification

Run the consistency test:
```bash
cd backend
python test_consistency.py
```

Expected output:
```
✓ CONSISTENCY TEST PASSED
```

## Impact

- ✅ Single and batch evaluation now produce identical results
- ✅ PDF-extracted questions properly cleaned
- ✅ No false "OUT OF SYLLABUS" classifications due to preprocessing
- ✅ Detailed logging for debugging
- ✅ No architecture changes required
