import re
import fitz
import logging

logger = logging.getLogger(__name__)


class PDFQuestionParser:
    """Parse questions from PDF files"""
    
    @staticmethod
    def clean_question(text):
        """Remove noise from question text"""
        raw_text = text
        
        # Remove Part headers
        text = re.sub(r'Part\s+[A-Z]\b', '', text, flags=re.IGNORECASE)
        
        # Remove marks patterns
        text = re.sub(r'\(\d+\s*[×x]\s*\d+\s*=\s*\d+\s*Marks?\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\d+\s*Marks?\b', '', text, flags=re.IGNORECASE)
        
        # Remove section headers
        text = re.sub(r'Section\s+[A-Z]\b', '', text, flags=re.IGNORECASE)
        
        # Remove page numbers
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        
        # Remove excess whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        logger.info(f"[PDF_PARSER] RAW: '{raw_text[:100]}'")
        logger.info(f"[PDF_PARSER] CLEANED: '{text[:100]}'")
        
        return text
    
    @staticmethod
    def detect_part(text, question_number):
        """Detect which part (A, B, C) the question belongs to - ONLY from explicit markers"""
        # Check for explicit Part markers
        if re.search(r'Part\s+A\b', text, re.IGNORECASE):
            return 'Part A'
        if re.search(r'Part\s+B\b', text, re.IGNORECASE):
            return 'Part B'
        if re.search(r'Part\s+C\b', text, re.IGNORECASE):
            return 'Part C'
        
        # No explicit marker found - do not guess
        return None
    
    @staticmethod
    def split_or_questions(question_text, question_number):
        """Split questions containing OR into separate questions"""
        # Check for OR patterns
        has_or = False
        
        # Pattern 1: " OR " or "\nOR\n"
        if re.search(r'\s+OR\s+|\nOR\n', question_text, re.IGNORECASE):
            has_or = True
        
        # Pattern 2: (a) ... (b) pattern
        if re.search(r'\(a\).*?\(b\)', question_text, re.IGNORECASE | re.DOTALL):
            has_or = True
        
        if not has_or:
            return [{'number': question_number, 'text': question_text}]
        
        # Split by OR
        parts = re.split(r'\s+OR\s+|\nOR\n', question_text, flags=re.IGNORECASE)
        
        # If no split happened, try (a) (b) pattern
        if len(parts) == 1:
            match = re.search(r'\(a\)(.*?)\(b\)(.*)', question_text, re.IGNORECASE | re.DOTALL)
            if match:
                parts = [match.group(1).strip(), match.group(2).strip()]
        
        if len(parts) < 2:
            return [{'number': question_number, 'text': question_text}]
        
        # Create sub-questions
        sub_questions = []
        for i, part in enumerate(parts):
            if part.strip():
                sub_num = f"{question_number}({'abcdefgh'[i]})"
                sub_questions.append({'number': sub_num, 'text': part.strip()})
        
        return sub_questions if sub_questions else [{'number': question_number, 'text': question_text}]
    
    @staticmethod
    def extract_text_from_pdf(pdf_bytes):
        """Extract text from PDF bytes"""
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    
    @staticmethod
    def split_questions(text):
        """Split text into individual questions with proper Part detection between questions"""
        lines = text.split('\n')
        questions = []
        current_part = "Part A"  # Default
        current_question = None
        current_number = None
        pending_part_change = None  # Track part changes between questions
        
        # Part header: Must be standalone line with "Marks" keyword
        part_pattern = re.compile(r'^\s*Part\s+([ABC])\s*[:\-–—].*Marks', re.IGNORECASE)
        question_pattern = re.compile(r'^\s*(\d+)\.\s+')
        or_pattern = re.compile(r'^\s*(\d+)\s*\(([a-z])\)', re.IGNORECASE)
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Check for Part header
            part_match = part_pattern.match(line_stripped)
            if part_match:
                pending_part_change = f"Part {part_match.group(1).upper()}"
                logger.info(f"[PART DETECTED] {pending_part_change} from: {line_stripped[:80]}")
                continue
            
            # Check for question number
            q_match = question_pattern.match(line_stripped)
            or_match = or_pattern.match(line_stripped)
            
            if q_match or or_match:
                # Save previous question
                if current_question and current_number:
                    questions.append({
                        "number": current_number,
                        "text": current_question.strip(),
                        "part": current_part
                    })
                    logger.info(f"[SAVED] Q{current_number} → {current_part}")
                
                # Apply pending part change NOW (before starting new question)
                if pending_part_change:
                    current_part = pending_part_change
                    logger.info(f"[PART SWITCH] Now in {current_part}")
                    pending_part_change = None
                
                # Start new question
                if or_match:
                    current_number = f"{or_match.group(1)}({or_match.group(2)})"
                    current_question = re.sub(r'^\s*\d+\s*\([a-z]\)\s*', '', line_stripped, flags=re.IGNORECASE)
                else:
                    current_number = q_match.group(1)
                    current_question = re.sub(r'^\s*\d+\.\s+', '', line_stripped)
                
                logger.info(f"[NEW Q] Q{current_number} started in {current_part}")
            else:
                # Continuation of current question
                if current_question is not None:
                    current_question += " " + line_stripped
        
        # Save last question
        if current_question and current_number:
            questions.append({
                "number": current_number,
                "text": current_question.strip(),
                "part": current_part
            })
            logger.info(f"[SAVED] Q{current_number} → {current_part}")
        
        logger.info(f"[TOTAL] Extracted {len(questions)} questions")
        return questions
