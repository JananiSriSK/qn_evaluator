import re
import logging
from typing import List
from models.schemas import SyllabusUnit

logger = logging.getLogger(__name__)

class SyllabusPreprocessor:
    """Canonical syllabus preprocessing to normalize all input formats"""
    
    def normalize_syllabus(self, syllabus_text: str) -> List[SyllabusUnit]:
        """
        Normalize ANY syllabus format into List[SyllabusUnit]
        
        Rules:
        - If contains "UNIT I/II/III" → parse explicitly
        - Else → split by blank lines, treat each paragraph as unit
        """
        if self._has_explicit_units(syllabus_text):
            return self._parse_explicit_units(syllabus_text)
        else:
            return self._parse_paragraph_units(syllabus_text)
    
    def _has_explicit_units(self, text: str) -> bool:
        """Check if syllabus has explicit UNIT markers"""
        unit_pattern = r'\bUNIT\s+[IVX1-9]+\b'
        return bool(re.search(unit_pattern, text, re.IGNORECASE))
    
    def _parse_explicit_units(self, text: str) -> List[SyllabusUnit]:
        """Parse syllabus with explicit UNIT I, II, III markers"""
        units = []
        unit_pattern = r'\bUNIT\s+([IVX1-9]+)\b'
        
        # Split by unit markers
        parts = re.split(unit_pattern, text, flags=re.IGNORECASE)
        
        for i in range(1, len(parts), 2):  # Skip first empty part, then take pairs
            if i + 1 < len(parts):
                unit_marker = parts[i].strip()
                unit_content = parts[i + 1].strip()
                
                if unit_content:
                    # Convert roman/text to number
                    unit_number = self._convert_to_number(unit_marker)
                    
                    # Extract title from first line/phrase
                    title = self._extract_unit_title(unit_content)
                    
                    units.append(SyllabusUnit(
                        unit_number=unit_number,
                        title=title,
                        content=unit_content
                    ))
        
        return units
    
    def _parse_paragraph_units(self, text: str) -> List[SyllabusUnit]:
        """Parse syllabus by splitting paragraphs (no explicit units)"""
        units = []
        
        # Split by double newlines (blank lines)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        for i, paragraph in enumerate(paragraphs, 1):
            title = self._extract_unit_title(paragraph)
            
            units.append(SyllabusUnit(
                unit_number=i,
                title=title,
                content=paragraph
            ))
        
        return units
    
    def _convert_to_number(self, unit_marker: str) -> int:
        """Convert UNIT marker to number"""
        roman_map = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8}
        
        unit_marker = unit_marker.upper().strip()
        
        if unit_marker in roman_map:
            return roman_map[unit_marker]
        elif unit_marker.isdigit():
            return int(unit_marker)
        else:
            return 1  # Fallback
    
    def _extract_unit_title(self, content: str) -> str:
        """Extract unit title from first major phrase"""
        # Take first line or first sentence up to 100 chars
        first_line = content.split('\n')[0].strip()
        
        if len(first_line) <= 100:
            return first_line
        else:
            # Take first sentence or first 100 chars
            sentences = first_line.split('.')
            if len(sentences[0]) <= 100:
                return sentences[0].strip()
            else:
                return first_line[:100].strip() + "..."