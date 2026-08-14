"""
Professional PDF/DOCX Export — A4 Research Report Generator.

Features:
  - Professional A4 layout with proper margins (22mm)
  - UTF-8 safe text handling (no latin-1 corruption)
  - Page header with title + report date
  - Numbered footer on every page
  - Metadata section (session, export date, message count)
  - Markdown-aware text rendering (headings, bullets, code, paragraphs)
  - Source/citation blocks for research responses
  - Automatic text wrapping — no overflow
  - Code block detection and distinct formatting
  - Proper section hierarchy with visual spacing
  - Long URLs handled safely
"""
import json
import os
import re
import tempfile
from datetime import datetime
from typing import List, Optional

# pyrefly: ignore [missing-import]
from fpdf import FPDF, XPos, YPos
# pyrefly: ignore [missing-import]
from docx import Document
# pyrefly: ignore [missing-import]
from docx.shared import Pt, RGBColor
from app.db.models import Message

# Generated reports use only the instance temp directory before upload to
# Supabase Storage; no persistent local directory is required on Render.
EXPORT_DIR = tempfile.gettempdir()

# ── Design Tokens ─────────────────────────────────────────────────────────────
PAGE_W = 210   # A4 width mm
PAGE_H = 297   # A4 height mm
MARGIN = 22    # Left/right/top margin mm
USABLE_W = PAGE_W - 2 * MARGIN   # 166mm

# Colour palette (R, G, B)
COLOR_ACCENT    = (99, 102, 241)   # indigo-500
COLOR_DARK      = (17, 24, 39)     # gray-900
COLOR_MID       = (75, 85, 99)     # gray-600
COLOR_LIGHT     = (243, 244, 246)  # gray-100
COLOR_WHITE     = (255, 255, 255)
COLOR_USER_BG   = (239, 246, 255)  # blue-50
COLOR_AI_BG     = (245, 243, 255)  # violet-50
COLOR_DIVIDER   = (209, 213, 219)  # gray-300
COLOR_MUTED     = (107, 114, 128)  # gray-500
COLOR_CODE_BG   = (245, 245, 245)  # near-white code bg
COLOR_SOURCE_BG = (240, 253, 244)  # green-50


def _strip_markdown(text: str) -> str:
    """Convert common Markdown to plain text for PDF rendering."""
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    return text


def _inline_strip(text: str) -> str:
    """Strip only inline markdown (bold, italic, inline code, links)."""
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    return text


def _safe(text: str) -> str:
    """Sanitize text for PDF rendering: replace known problematic unicode
    symbols with ASCII equivalents. Keeps UTF-8 encoding — does NOT
    convert to latin-1 (which corrupts non-latin characters)."""
    replacements = {
        '\u2019': "'", '\u2018': "'",
        '\u201c': '"', '\u201d': '"',
        '\u2014': '-', '\u2013': '-',
        '\u2026': '...',
        '\u2022': '*',
        '\u00a0': ' ',
        '\u2192': '->',
        '\u2190': '<-',
        '\u00b7': '*',
        '\u2713': '[OK]',
        '\u2714': '[OK]',
        '\u2717': '[X]',
        '\u2718': '[X]',
        '\u25b6': '>',
        '\u25ba': '>',
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    # Round-trip through UTF-8 to drop any lone surrogates or invalid bytes
    return text.encode('utf-8', 'replace').decode('utf-8')


def _parse_sources(sources_raw: Optional[str]) -> list:
    """Parse the JSON sources string from a Message into a list of dicts."""
    if not sources_raw:
        return []
    try:
        parsed = json.loads(sources_raw)
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def _split_into_blocks(text: str) -> list:
    """
    Split message content into typed blocks for structured PDF rendering.
    Block types: heading, code, bullet, paragraph, rule
    """
    blocks = []
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]

        # Fenced code block (``` ... ```)
        if line.strip().startswith('```'):
            lang = line.strip()[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            blocks.append({'type': 'code', 'lang': lang, 'text': '\n'.join(code_lines)})
            i += 1
            continue

        # ATX Heading
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            level = len(m.group(1))
            blocks.append({'type': 'heading', 'level': level, 'text': m.group(2).strip()})
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^[-*_]{3,}\s*$', line.strip()):
            blocks.append({'type': 'rule'})
            i += 1
            continue

        # Unordered bullet
        m = re.match(r'^[\-\*\+]\s+(.*)', line)
        if m:
            blocks.append({'type': 'bullet', 'text': m.group(1).strip()})
            i += 1
            continue

        # Ordered list
        m = re.match(r'^\d+[.)]\s+(.*)', line)
        if m:
            blocks.append({'type': 'bullet', 'text': m.group(1).strip()})
            i += 1
            continue

        # Empty line — skip
        if not line.strip():
            i += 1
            continue

        # Paragraph — collect consecutive non-special lines
        para_lines = []
        while i < len(lines):
            l = lines[i]
            if not l.strip():
                break
            if re.match(r'^#{1,6}\s', l):
                break
            if l.strip().startswith('```'):
                break
            if re.match(r'^[-*_]{3,}\s*$', l.strip()):
                break
            if re.match(r'^[\-\*\+]\s', l):
                break
            if re.match(r'^\d+[.)]\s', l):
                break
            para_lines.append(l)
            i += 1
        if para_lines:
            blocks.append({'type': 'paragraph', 'text': ' '.join(para_lines)})

    return blocks


class ResearchPDF(FPDF):
    """
    Professional A4 research report PDF with:
    - Branded header (accent bar + title)
    - Page numbers in footer
    - Styled user/AI message sections
    - Markdown block rendering
    """

    def __init__(self, report_title: str, session_id: int, msg_count: int):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.report_title = _safe(report_title[:80])
        self.session_id = session_id
        self.msg_count = msg_count
        self.export_date = datetime.now().strftime("%B %d, %Y at %H:%M")
        self.set_margins(MARGIN, MARGIN, MARGIN)
        self.set_auto_page_break(auto=True, margin=20)
        # UTF-8 for core fonts (Helvetica/Courier)
        self.core_fonts_encoding = 'utf-8'

    # ── Header ────────────────────────────────────────────────────────────────
    def header(self):
        # Top accent bar
        self.set_fill_color(*COLOR_ACCENT)
        self.rect(0, 0, PAGE_W, 9, style='F')

        self.set_y(11)
        self.set_x(MARGIN)
        self.set_font('Helvetica', 'B', 8.5)
        self.set_text_color(*COLOR_ACCENT)
        self.cell(70, 5, 'AI Research Copilot', new_x=XPos.RIGHT, new_y=YPos.TOP)

        title_disp = self.report_title if len(self.report_title) <= 55 else self.report_title[:52] + '...'
        self.set_font('Helvetica', '', 7.5)
        self.set_text_color(*COLOR_MUTED)
        self.cell(USABLE_W - 70, 5, title_disp, align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Divider
        self.set_draw_color(*COLOR_DIVIDER)
        self.set_line_width(0.25)
        self.line(MARGIN, 18, PAGE_W - MARGIN, 18)
        self.ln(4)

    # ── Footer ────────────────────────────────────────────────────────────────
    def footer(self):
        self.set_y(-15)
        self.set_draw_color(*COLOR_DIVIDER)
        self.set_line_width(0.25)
        self.line(MARGIN, self.get_y(), PAGE_W - MARGIN, self.get_y())
        self.ln(1.5)
        self.set_font('Helvetica', '', 7)
        self.set_text_color(*COLOR_MUTED)
        self.set_x(MARGIN)
        self.cell(USABLE_W / 2, 5, f'Exported {self.export_date}', align='L')
        self.cell(USABLE_W / 2, 5, f'Page {self.page_no()}', align='R',
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ── Cover Section ─────────────────────────────────────────────────────────
    def add_cover(self):
        """Title + metadata box at top of first page."""
        # Main title
        self.set_font('Helvetica', 'B', 19)
        self.set_text_color(*COLOR_DARK)
        self.multi_cell(USABLE_W, 9, self.report_title, align='L')
        self.ln(2)

        self.set_font('Helvetica', '', 9.5)
        self.set_text_color(*COLOR_MID)
        self.multi_cell(USABLE_W, 5.5, 'AI Research Copilot - Research Export Report', align='L')
        self.ln(5)

        # Metadata row (light background box)
        box_y = self.get_y()
        self.set_fill_color(*COLOR_LIGHT)
        self.set_draw_color(*COLOR_DIVIDER)
        self.set_line_width(0.25)
        # Draw box
        self.rect(MARGIN, box_y, USABLE_W, 18, style='FD')

        self.set_xy(MARGIN + 5, box_y + 4)
        self.set_font('Helvetica', 'B', 7.5)
        self.set_text_color(*COLOR_MUTED)
        self.cell(30, 4.5, 'Session ID:', new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_font('Helvetica', '', 7.5)
        self.set_text_color(*COLOR_DARK)
        self.cell(30, 4.5, str(self.session_id))

        self.set_xy(MARGIN + 80, box_y + 4)
        self.set_font('Helvetica', 'B', 7.5)
        self.set_text_color(*COLOR_MUTED)
        self.cell(30, 4.5, 'Messages:', new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_font('Helvetica', '', 7.5)
        self.set_text_color(*COLOR_DARK)
        self.cell(30, 4.5, str(self.msg_count))

        self.set_xy(MARGIN + 5, box_y + 10)
        self.set_font('Helvetica', 'B', 7.5)
        self.set_text_color(*COLOR_MUTED)
        self.cell(30, 4.5, 'Exported:', new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_font('Helvetica', '', 7.5)
        self.set_text_color(*COLOR_DARK)
        self.cell(80, 4.5, self.export_date)

        self.set_y(box_y + 21)
        self.ln(5)

        # Accent divider
        self.set_draw_color(*COLOR_ACCENT)
        self.set_line_width(0.7)
        self.line(MARGIN, self.get_y(), PAGE_W - MARGIN, self.get_y())
        self.ln(7)

    # ── Message Renderers ─────────────────────────────────────────────────────
    def render_user_turn(self, content: str):
        """Render a user message with blue accent left border."""
        y0 = self.get_y()

        # Role badge
        self.set_font('Helvetica', 'B', 7.5)
        self.set_text_color(*COLOR_ACCENT)
        self.set_fill_color(*COLOR_USER_BG)
        self.set_draw_color(*COLOR_ACCENT)
        self.set_line_width(0.5)
        self.set_x(MARGIN)
        self.cell(16, 5.5, 'USER', fill=True, border='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

        # Content (plain text, no markdown)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(*COLOR_DARK)
        self.set_x(MARGIN)
        self.multi_cell(USABLE_W, 5.5, _safe(_strip_markdown(content)), align='L')
        self.ln(5)

    def render_ai_turn(self, content: str, sources: Optional[list] = None):
        """Render an AI response with structured block formatting and optional sources."""
        # Role badge
        self.set_font('Helvetica', 'B', 7.5)
        self.set_text_color(139, 92, 246)  # violet
        self.set_fill_color(*COLOR_AI_BG)
        self.set_draw_color(139, 92, 246)
        self.set_line_width(0.5)
        self.set_x(MARGIN)
        self.cell(24, 5.5, 'AI COPILOT', fill=True, border='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

        # Render each content block
        blocks = _split_into_blocks(content)
        for block in blocks:
            self._render_block(block)

        # Render source citations if available
        if sources:
            self._render_sources(sources)

        self.ln(3)

        # Message separator
        self.set_draw_color(*COLOR_DIVIDER)
        self.set_line_width(0.2)
        self.line(MARGIN, self.get_y(), PAGE_W - MARGIN, self.get_y())
        self.ln(6)

    def _render_sources(self, sources: list):
        """Render a collapsible source citation block below the AI response."""
        if not sources:
            return

        self.ln(2)
        # Section label
        self.set_font('Helvetica', 'B', 7.5)
        self.set_text_color(22, 163, 74)  # green-600
        self.set_x(MARGIN)
        self.cell(USABLE_W, 4.5, f'Sources ({len(sources)})', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

        for i, src in enumerate(sources, 1):
            title = src.get('title') or src.get('name') or f'Source {i}'
            url   = src.get('url') or src.get('link') or ''
            snippet = src.get('snippet') or src.get('text') or src.get('content') or ''

            # Source title
            self.set_font('Helvetica', 'B', 8)
            self.set_text_color(*COLOR_DARK)
            self.set_x(MARGIN + 3)
            self.multi_cell(USABLE_W - 6, 4.5, _safe(f'{i}. {title}'), align='L')

            # URL
            if url:
                self.set_font('Helvetica', 'I', 7)
                self.set_text_color(59, 130, 246)  # blue-500
                self.set_x(MARGIN + 6)
                url_display = url[:90] + '...' if len(url) > 90 else url
                self.multi_cell(USABLE_W - 9, 4, _safe(url_display), align='L')

            # Snippet
            if snippet:
                self.set_font('Helvetica', '', 7.5)
                self.set_text_color(*COLOR_MID)
                self.set_x(MARGIN + 6)
                snippet_clean = _safe(_strip_markdown(snippet[:300]))
                if len(snippet) > 300:
                    snippet_clean += '...'
                self.multi_cell(USABLE_W - 9, 4, snippet_clean, align='L')

            self.ln(1.5)

    def _render_block(self, block: dict):
        btype = block.get('type', '')

        if btype == 'heading':
            level = block.get('level', 2)
            text = _safe(_inline_strip(block.get('text', '')))
            sizes = {1: 14, 2: 12, 3: 10.5, 4: 10, 5: 9, 6: 9}
            sz = sizes.get(level, 10)
            self.ln(3)
            self.set_font('Helvetica', 'B', sz)
            self.set_text_color(*COLOR_DARK)
            self.set_x(MARGIN)
            self.multi_cell(USABLE_W, sz * 0.55, text, align='L')
            if level <= 2:
                self.set_draw_color(*COLOR_DIVIDER)
                self.set_line_width(0.2)
                self.line(MARGIN, self.get_y(), MARGIN + USABLE_W * 0.55, self.get_y())
            self.ln(2)

        elif btype == 'paragraph':
            text = _safe(_inline_strip(block.get('text', '')))
            if not text.strip():
                return
            self.set_font('Helvetica', '', 10)
            self.set_text_color(*COLOR_DARK)
            self.set_x(MARGIN)
            self.multi_cell(USABLE_W, 5.5, text, align='L')
            self.ln(2)

        elif btype == 'bullet':
            text = _safe(_inline_strip(block.get('text', '')))
            if not text.strip():
                return
            self.set_font('Helvetica', '', 10)
            self.set_text_color(*COLOR_DARK)
            # Render as "- text" with indent
            self.set_x(MARGIN + 3)
            # Write bullet + text in one multi_cell with left indent
            self.multi_cell(USABLE_W - 6, 5.5, f'* {text}', align='L')
            self.ln(0.5)

        elif btype == 'code':
            code_text = _safe(block.get('text', ''))
            lang = block.get('lang', '')
            if not code_text.strip():
                return
            self.ln(2)

            # Language label
            if lang:
                self.set_font('Helvetica', 'I', 7.5)
                self.set_text_color(*COLOR_MUTED)
                self.set_x(MARGIN + 2)
                self.cell(USABLE_W - 4, 4.5, lang, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # Draw code background first, then write text on top
            code_lines = code_text.split('\n')
            line_h = 4.2
            box_h = len(code_lines) * line_h + 6
            x0, y0 = MARGIN, self.get_y()

            # Check if we need a page break
            if y0 + box_h > PAGE_H - 25:
                self.add_page()
                x0, y0 = MARGIN, self.get_y()

            # Draw background rectangle
            self.set_fill_color(*COLOR_CODE_BG)
            self.set_draw_color(*COLOR_DIVIDER)
            self.set_line_width(0.25)
            self.rect(x0, y0, USABLE_W, min(box_h, PAGE_H - y0 - 22), style='FD')

            # Write code lines
            self.set_y(y0 + 3)
            self.set_font('Courier', '', 8)
            self.set_text_color(40, 40, 40)
            for code_line in code_lines:
                self.set_x(MARGIN + 4)
                self.multi_cell(USABLE_W - 8, line_h, code_line if code_line else ' ', align='L')

            self.ln(3)

        elif btype == 'rule':
            self.ln(2)
            self.set_draw_color(*COLOR_DIVIDER)
            self.set_line_width(0.4)
            self.line(MARGIN, self.get_y(), PAGE_W - MARGIN, self.get_y())
            self.ln(4)


# ── Public API ────────────────────────────────────────────────────────────────

def generate_pdf_report(session_title: str, messages: List[Message], session_id: int) -> str:
    """
    Generate a professional A4 PDF research report.

    Layout:
      - Cover section: title + metadata box
      - Per-message sections with role labels
      - Markdown block rendering (headings, bullets, code, paragraphs)
      - Page header + numbered footer on every page
      - UTF-8 safe text handling
    """
    ai_msgs = [m for m in messages if m.role in ("user", "assistant")]

    pdf = ResearchPDF(
        report_title=session_title,
        session_id=session_id,
        msg_count=len(ai_msgs),
    )
    pdf.add_page()
    pdf.add_cover()

    for msg in messages:
        if msg.role == "user":
            pdf.render_user_turn(msg.content)
        elif msg.role == "assistant":
            sources = _parse_sources(msg.sources)
            pdf.render_ai_turn(msg.content, sources=sources)

    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    safe_title = re.sub(r'[^\w\s-]', '', session_title)[:40].strip().replace(' ', '_')
    file_path = os.path.join(EXPORT_DIR, f"report_{safe_title}_{session_id}_{ts}.pdf")
    pdf.output(file_path)
    return file_path


def _docx_set_code_style(paragraph):
    """Apply monospace code style to a DOCX paragraph safely."""
    try:
        paragraph.style = 'No Spacing'
    except Exception:
        pass  # Style doesn't exist in all templates; fall back gracefully
    for run in paragraph.runs:
        run.font.name = 'Courier New'
        run.font.size = Pt(9)


def generate_docx_report(session_title: str, messages: List[Message], session_id: int) -> str:
    """
    Generate a DOCX research report with:
    - Title and metadata
    - User/AI message sections
    - Structured markdown (headings, bullets, code, paragraphs)
    - Source citation sections for research responses
    """
    doc = Document()
    doc.add_heading(f"AI Research Report: {session_title}", 0)

    meta = doc.add_paragraph()
    meta.add_run(
        f"Session ID: {session_id}  |  "
        f"Exported: {datetime.now().strftime('%B %d, %Y %H:%M')}  |  "
        f"Messages: {len(messages)}"
    )
    doc.add_paragraph()

    for msg in messages:
        if msg.role == "user":
            doc.add_heading('User', level=2)
            doc.add_paragraph(_strip_markdown(msg.content))

        elif msg.role == "assistant":
            doc.add_heading('AI Copilot', level=2)
            blocks = _split_into_blocks(msg.content)
            for block in blocks:
                btype = block.get('type', '')
                if btype == 'heading':
                    lvl = min(block['level'] + 2, 6)
                    doc.add_heading(block['text'], level=lvl)
                elif btype == 'code':
                    p = doc.add_paragraph(block['text'])
                    _docx_set_code_style(p)
                elif btype == 'bullet':
                    doc.add_paragraph(block['text'], style='List Bullet')
                elif btype == 'paragraph':
                    doc.add_paragraph(_inline_strip(block.get('text', '')))

            # Add source citations if available
            sources = _parse_sources(msg.sources)
            if sources:
                doc.add_heading(f'Sources ({len(sources)})', level=3)
                for i, src in enumerate(sources, 1):
                    title   = src.get('title') or src.get('name') or f'Source {i}'
                    url     = src.get('url') or src.get('link') or ''
                    snippet = src.get('snippet') or src.get('text') or src.get('content') or ''

                    src_para = doc.add_paragraph()
                    run_num = src_para.add_run(f'{i}. ')
                    run_num.bold = True
                    run_title = src_para.add_run(title)
                    run_title.bold = True

                    if url:
                        url_para = doc.add_paragraph()
                        url_para.paragraph_format.left_indent = Pt(18)
                        url_run = url_para.add_run(url)
                        url_run.font.color.rgb = RGBColor(59, 130, 246)
                        url_run.italic = True

                    if snippet:
                        snip_para = doc.add_paragraph(_strip_markdown(snippet[:400]))
                        snip_para.paragraph_format.left_indent = Pt(18)

    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    safe_title = re.sub(r'[^\w\s-]', '', session_title)[:40].strip().replace(' ', '_')
    file_path = os.path.join(EXPORT_DIR, f"report_{safe_title}_{session_id}_{ts}.docx")
    doc.save(file_path)
    return file_path
