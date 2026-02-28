import re
import fitz
import logging

logger = logging.getLogger(__name__)


class PDFQuestionParser:
    """Parse questions from PDF files"""
    
    @staticmethod
    def clean_question(text):
        """Remove noise from question text"""
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
        
        return text
    
    @staticmethod
    def detect_part(text, question_number):
        """Detect which part (A, B, C) the question belongs to"""
        # Check for explicit Part markers
        if re.search(r'Part\s+A\b', text, re.IGNORECASE):
            return 'Part A'
        if re.search(r'Part\s+B\b', text, re.IGNORECASE):
            return 'Part B'
        if re.search(r'Part\s+C\b', text, re.IGNORECASE):
            return 'Part C'
        
        # Infer from question number
        if question_number.replace('(a)', '').replace('(b)', '').isdigit():
            num = int(question_number.replace('(a)', '').replace('(b)', ''))
            if num <= 10:
                return 'Part A'
            elif num <= 19:
                return 'Part B'
            else:
                return 'Part C'
        
        return 'Part A'
    
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
        """Split text into individual questions with part detection"""
        # Detect part boundaries
        part_markers = list(re.finditer(r'Part\s+([A-C])\b', text, re.IGNORECASE))
        current_part = 'Part A'
        
        # Common question patterns
        patterns = [
            r'\n\s*(\d+)\.?\s+',
            r'\n\s*Q(\d+)[:\.\)]\s+',
            r'\n\s*Question\s+(\d+)[:\.\)]\s+',
        ]
        
        questions = []
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            
            if len(matches) > 1:
                for i, match in enumerate(matches):
                    start = match.end()
                    end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                    question_text = text[start:end].strip()
                    
                    if question_text:
                        # Clean the question
                        cleaned = PDFQuestionParser.clean_question(question_text)
                        if cleaned:
                            # Detect part
                            part = PDFQuestionParser.detect_part(text[max(0, match.start()-100):match.end()+100], match.group(1))
                            
                            # Split OR questions
                            sub_questions = PDFQuestionParser.split_or_questions(cleaned, match.group(1))
                            
                            for sq in sub_questions:
                                sq['part'] = part
                                questions.append(sq)
                
                if questions:
                    break
        
        # If no pattern matched
        if not questions:
            cleaned = PDFQuestionParser.clean_question(text.strip())
            if cleaned:
                questions = [{'number': '1', 'text': cleaned, 'part': 'Part A'}]
        
        logger.info(f"Extracted {len(questions)} questions from PDF")
        return questions
