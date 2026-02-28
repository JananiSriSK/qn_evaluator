"""
Report generation service for PDF and DOCX formats
Detects Part A, B, C and generates separate tables
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from datetime import datetime
import tempfile
import re


class ReportGenerator:
    """Generate evaluation reports in PDF and DOCX formats"""
    
    @staticmethod
    def detect_parts(results):
        """Detect Part A, B, C from results"""
        parts = {}
        
        for r in results:
            part = r.get('part', 'Part A')
            if part not in parts:
                parts[part] = []
            parts[part].append(r)
        
        return parts
    
    @staticmethod
    def generate_pdf(domain_name, results, report_type="mapping"):
        """Generate PDF report with part-wise tables
        
        Args:
            domain_name: Subject name
            results: List of evaluation results
            report_type: 'mapping' (Q.No, CO, BL) or 'question_paper' (Q.No, Question, CO, BL)
        """
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        doc = SimpleDocTemplate(temp_file.name, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=20,
            alignment=1
        )
        elements.append(Paragraph("Question Paper CO-BL Mapping Report", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Metadata
        meta_style = styles['Normal']
        elements.append(Paragraph(f"<b>Subject:</b> {domain_name}", meta_style))
        elements.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}", meta_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Cell style for wrapping
        cell_style = ParagraphStyle(
            'CellStyle',
            parent=styles['Normal'],
            fontSize=9,
            leading=11,
            wordWrap='CJK'
        )
        
        # Detect parts
        parts = ReportGenerator.detect_parts(results)
        
        # Generate table for each part
        for part_name in ['Part A', 'Part B', 'Part C']:
            if part_name not in parts:
                continue
            
            part_results = parts[part_name]
            
            # Part heading
            part_style = ParagraphStyle(
                'PartHeading',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=10
            )
            elements.append(Paragraph(part_name, part_style))
            
            # Table data based on report type with Paragraph wrapping
            if report_type == "mapping":
                table_data = [[Paragraph('<b>Q.No</b>', cell_style), Paragraph('<b>CO</b>', cell_style), Paragraph('<b>BL</b>', cell_style)]]
                col_widths = [40, 60, 60]
            else:  # question_paper
                table_data = [[Paragraph('<b>Q.No</b>', cell_style), Paragraph('<b>Question</b>', cell_style), Paragraph('<b>CO</b>', cell_style), Paragraph('<b>BL</b>', cell_style)]]
                col_widths = [40, 250, 60, 60]
            
            for r in part_results:
                if report_type == "mapping":
                    table_data.append([
                        Paragraph(str(r.get('question_number', '-')), cell_style),
                        Paragraph(', '.join(r.get('course_outcomes', [])) or 'N/A', cell_style),
                        Paragraph(r.get('bloom_level', 'N/A'), cell_style)
                    ])
                else:  # question_paper
                    question_text = r.get('question', '')
                    table_data.append([
                        Paragraph(str(r.get('question_number', '-')), cell_style),
                        Paragraph(question_text, cell_style),
                        Paragraph(', '.join(r.get('course_outcomes', [])) or 'N/A', cell_style),
                        Paragraph(r.get('bloom_level', 'N/A'), cell_style)
                    ])
            
            # Create table
            table = Table(table_data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))
        
        doc.build(elements)
        return temp_file.name
    
    @staticmethod
    def generate_docx(domain_name, results, report_type="mapping"):
        """Generate DOCX report with part-wise tables
        
        Args:
            domain_name: Subject name
            results: List of evaluation results
            report_type: 'mapping' (Q.No, CO, BL) or 'question_paper' (Q.No, Question, CO, BL)
        """
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        doc = Document()
        
        # Title
        title = doc.add_heading('Question Paper CO-BL Mapping Report', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Metadata
        doc.add_paragraph(f"Subject: {domain_name}")
        doc.add_paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        doc.add_paragraph()
        
        # Detect parts
        parts = ReportGenerator.detect_parts(results)
        
        # Generate table for each part
        for part_name in ['Part A', 'Part B', 'Part C']:
            if part_name not in parts:
                continue
            
            part_results = parts[part_name]
            
            # Part heading
            doc.add_heading(part_name, level=2)
            
            # Table based on report type
            if report_type == "mapping":
                table = doc.add_table(rows=1, cols=3)
                headers = ['Q.No', 'CO', 'BL']
            else:  # question_paper
                table = doc.add_table(rows=1, cols=4)
                headers = ['Q.No', 'Question', 'CO', 'BL']
            
            table.style = 'Light Grid Accent 1'
            
            # Header
            header_cells = table.rows[0].cells
            for i, header in enumerate(headers):
                header_cells[i].text = header
                header_cells[i].paragraphs[0].runs[0].font.bold = True
            
            # Data rows
            for r in part_results:
                row_cells = table.add_row().cells
                if report_type == "mapping":
                    row_cells[0].text = str(r.get('question_number', '-'))
                    row_cells[1].text = ', '.join(r.get('course_outcomes', [])) or 'N/A'
                    row_cells[2].text = r.get('bloom_level', 'N/A')
                else:  # question_paper
                    row_cells[0].text = str(r.get('question_number', '-'))
                    row_cells[1].text = r.get('question', '')[:100] + '...' if len(r.get('question', '')) > 100 else r.get('question', '')
                    row_cells[2].text = ', '.join(r.get('course_outcomes', [])) or 'N/A'
                    row_cells[3].text = r.get('bloom_level', 'N/A')
            
            doc.add_paragraph()
        
        doc.save(temp_file.name)
        return temp_file.name
