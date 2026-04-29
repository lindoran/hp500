#!/usr/bin/env python3
"""
HP DeskJet 500 Family Printer Emulator
========================================
Converts ASCII / HP PCL files to PDF with authentic 90s inkjet rendering.

Supports:
  • Full 8-bit CP437 character set (box drawing, blocks, international)
  • HP PCL escape sequences (paper, orientation, margins, fonts, cursor)
  • Near Letter Quality (NLQ) and Draft rendering modes
  • Period-accurate page artifacts: paper tone, ink bleed, dot variation
  • 300 DPI bitmap rendering  →  PDF assembly

Usage:
  python3 hp500_emulator.py input.txt output.pdf [options]
  python3 hp500_emulator.py input.txt output.pdf --draft
  python3 hp500_emulator.py input.txt output.pdf --paper a4
  python3 hp500_emulator.py input.txt output.pdf --no-artifacts
  python3 hp500_emulator.py input.txt output.pdf --cpi 17   (compressed)
"""

import sys, os, re, math, random, argparse, struct
from io import BytesIO
#from turtle import width # this is nologer used.
#from turtle import st  # This is nolonger used. 
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import letter as LETTER_SIZE, A4 as A4_SIZE
from reportlab.lib.utils import ImageReader

# ---------------------------------------------------------------------------
# CP437 → Unicode mapping (full 256 character set)
# ---------------------------------------------------------------------------
CP437 = {
    0x00: '\u0000', 0x01: '\u263A', 0x02: '\u263B', 0x03: '\u2665',
    0x04: '\u2666', 0x05: '\u2663', 0x06: '\u2660', 0x07: '\u2022',
    0x08: '\u25D8', 0x09: '\u25CB', 0x0A: '\u25D9', 0x0B: '\u2642',
    0x0C: '\u2640', 0x0D: '\u266A', 0x0E: '\u266B', 0x0F: '\u263C',
    0x10: '\u25BA', 0x11: '\u25C4', 0x12: '\u2195', 0x13: '\u203C',
    0x14: '\u00B6', 0x15: '\u00A7', 0x16: '\u25AC', 0x17: '\u21A8',
    0x18: '\u2191', 0x19: '\u2193', 0x1A: '\u2192', 0x1B: '\u2190',
    0x1C: '\u221F', 0x1D: '\u2194', 0x1E: '\u25B2', 0x1F: '\u25BC',
    0x20: ' ',      0x7F: '\u2302',
    # 0x21-0x7E: standard ASCII (filled in loop below)
    # Extended
    0x80: '\u00C7', 0x81: '\u00FC', 0x82: '\u00E9', 0x83: '\u00E2',
    0x84: '\u00E4', 0x85: '\u00E0', 0x86: '\u00E5', 0x87: '\u00E7',
    0x88: '\u00EA', 0x89: '\u00EB', 0x8A: '\u00E8', 0x8B: '\u00EF',
    0x8C: '\u00EE', 0x8D: '\u00EC', 0x8E: '\u00C4', 0x8F: '\u00C5',
    0x90: '\u00C9', 0x91: '\u00E6', 0x92: '\u00C6', 0x93: '\u00F4',
    0x94: '\u00F6', 0x95: '\u00F2', 0x96: '\u00FB', 0x97: '\u00F9',
    0x98: '\u00FF', 0x99: '\u00D6', 0x9A: '\u00DC', 0x9B: '\u00A2',
    0x9C: '\u00A3', 0x9D: '\u00A5', 0x9E: '\u20A7', 0x9F: '\u0192',
    0xA0: '\u00E1', 0xA1: '\u00ED', 0xA2: '\u00F3', 0xA3: '\u00FA',
    0xA4: '\u00F1', 0xA5: '\u00D1', 0xA6: '\u00AA', 0xA7: '\u00BA',
    0xA8: '\u00BF', 0xA9: '\u2310', 0xAA: '\u00AC', 0xAB: '\u00BD',
    0xAC: '\u00BC', 0xAD: '\u00A1', 0xAE: '\u00AB', 0xAF: '\u00BB',
    0xB0: '\u2591', 0xB1: '\u2592', 0xB2: '\u2593', 0xB3: '\u2502',
    0xB4: '\u2524', 0xB5: '\u2561', 0xB6: '\u2562', 0xB7: '\u2556',
    0xB8: '\u2555', 0xB9: '\u2563', 0xBA: '\u2551', 0xBB: '\u2557',
    0xBC: '\u255D', 0xBD: '\u255C', 0xBE: '\u255B', 0xBF: '\u2510',
    0xC0: '\u2514', 0xC1: '\u2534', 0xC2: '\u252C', 0xC3: '\u251C',
    0xC4: '\u2500', 0xC5: '\u253C', 0xC6: '\u255E', 0xC7: '\u255F',
    0xC8: '\u255A', 0xC9: '\u2554', 0xCA: '\u2569', 0xCB: '\u2566',
    0xCC: '\u2560', 0xCD: '\u2550', 0xCE: '\u256C', 0xCF: '\u2567',
    0xD0: '\u2568', 0xD1: '\u2564', 0xD2: '\u2565', 0xD3: '\u2559',
    0xD4: '\u2558', 0xD5: '\u2552', 0xD6: '\u2553', 0xD7: '\u256B',
    0xD8: '\u256A', 0xD9: '\u2518', 0xDA: '\u250C', 0xDB: '\u2588',
    0xDC: '\u2584', 0xDD: '\u258C', 0xDE: '\u2590', 0xDF: '\u2580',
    0xE0: '\u03B1', 0xE1: '\u00DF', 0xE2: '\u0393', 0xE3: '\u03C0',
    0xE4: '\u03A3', 0xE5: '\u03C3', 0xE6: '\u00B5', 0xE7: '\u03C4',
    0xE8: '\u03A6', 0xE9: '\u0398', 0xEA: '\u03A9', 0xEB: '\u03B4',
    0xEC: '\u221E', 0xED: '\u03C6', 0xEE: '\u03B5', 0xEF: '\u2229',
    0xF0: '\u2261', 0xF1: '\u00B1', 0xF2: '\u2265', 0xF3: '\u2264',
    0xF4: '\u2320', 0xF5: '\u2321', 0xF6: '\u00F7', 0xF7: '\u2248',
    0xF8: '\u00B0', 0xF9: '\u2219', 0xFA: '\u00B7', 0xFB: '\u221A',
    0xFC: '\u207F', 0xFD: '\u00B2', 0xFE: '\u25A0', 0xFF: '\u00A0',
}
for c in range(0x21, 0x7F):
    CP437[c] = chr(c)


# ---------------------------------------------------------------------------
# Paper definitions  (width, height in inches)
# ---------------------------------------------------------------------------
PAPER_SIZES = {
    'letter':  (8.5,  11.0),
    'legal':   (8.5,  14.0),
    'a4':      (8.267, 11.693),
    'executive': (7.25, 10.5),
}

DPI = 300  # render resolution

UNDERLINE_THICKNESS = 3  # pixels

FONT_REGULAR = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
FONT_BOLD    = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
FONT_ITALIC  = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Oblique.ttf'
FONT_BOLDITA = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-BoldOblique.ttf'

# Fallback to Liberation Mono if needed
if not os.path.exists(FONT_REGULAR):
    FONT_REGULAR = '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf'
    FONT_BOLD    = '/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf'
    FONT_ITALIC  = '/usr/share/fonts/truetype/liberation/LiberationMono-Italic.ttf'
    FONT_BOLDITA = '/usr/share/fonts/truetype/liberation/LiberationMono-BoldItalic.ttf'


# ---------------------------------------------------------------------------
# Font cache
# ---------------------------------------------------------------------------
_font_cache = {}

def get_font(pt_size: float, bold=False, italic=False) -> ImageFont.FreeTypeFont:
    """Return a cached PIL font at the given SCREEN point size."""
    # Convert from print points to PIL pixels (300 DPI / 72 DPI = 4.1667x)
    pil_size = max(6, round(pt_size * DPI / 72))
    key = (pil_size, bold, italic)
    if key not in _font_cache:
        path = (FONT_BOLDITA if bold and italic
                else FONT_BOLD   if bold
                else FONT_ITALIC if italic
                else FONT_REGULAR)
        _font_cache[key] = ImageFont.truetype(path, pil_size)
    return _font_cache[key]


# ---------------------------------------------------------------------------
# Printer State
# ---------------------------------------------------------------------------
class PrinterState:
    def __init__(self, paper='letter', orientation='portrait',
                 default_cpi=10.0, default_lpi=6.0, nlq=True):
        self.paper      = paper
        self.orientation = orientation
        self.nlq        = nlq           # Near Letter Quality mode

        # --- derived page dimensions (pixels) ---
        self._recalc_page_dims()

        # --- print area / margins (pixels) ---
        # HP DeskJet 500: min top/bottom = 0.5", left/right = 0.25"
        self.margin_left   = round(0.5  * DPI)
        self.margin_right  = self.page_w - round(0.5  * DPI)
        self.margin_top    = round(0.5  * DPI)
        self.margin_bottom = self.page_h - round(0.5  * DPI)

        # --- font / pitch ---
        self.cpi        = default_cpi   # characters per inch
        self.lpi        = default_lpi   # lines per inch
        self.point_size = 12.0          # nominal print point size
        self.bold       = False
        self.italic     = False
        self.underline  = False
        self.double_wide = False
        self.subscript  = False
        self.superscript = False
        self.condensed  = False         # 17 CPI mode

        # --- cursor (pixels from top-left of page) ---
        self.cursor_x   = self.margin_left
        self.cursor_y   = self.margin_top

        # --- tab stops: every 8 chars ---
        self._rebuild_tabs()

        # --- pages ---
        self.pages = []             # list of PIL Images (final, composed)
        self.current_layer = None   # PIL Image (ink layer, RGBA)
        self.current_draw  = None
        self._new_page()

    def _recalc_page_dims(self):
        w_in, h_in = PAPER_SIZES.get(self.paper, PAPER_SIZES['letter'])
        if self.orientation == 'landscape':
            w_in, h_in = h_in, w_in
        self.page_w = round(w_in * DPI)
        self.page_h = round(h_in * DPI)
        self.page_w_in = w_in
        self.page_h_in = h_in

    @property
    def char_w(self) -> int:
        """Character cell width in pixels."""
        cpi = self.cpi * (0.5 if self.double_wide else 1.0)
        return round(DPI / cpi)

    @property
    def line_h(self) -> int:
        """Line height in pixels."""
        return round(DPI / self.lpi)

    @property
    def pil_font_size(self) -> int:
        """Font size to pass to PIL (scaled for 300 DPI)."""
        return round(self.point_size * DPI / 72)

    def _rebuild_tabs(self):
        cw = round(DPI / 10.0)   # always base 10 CPI for tabs
        self.tab_stops = [self.margin_left + i * 8 * cw for i in range(200)]

    def _new_page(self):
        """Flush the current page and start a fresh one."""
        if self.current_layer is not None:
            self._flush_page()
        # RGBA ink layer (transparent background, black ink)
        self.current_layer = Image.new('RGBA', (self.page_w, self.page_h), (0, 0, 0, 0))
        self.current_draw  = ImageDraw.Draw(self.current_layer)
        self.cursor_x = self.margin_left
        self.cursor_y = self.margin_top

    def _flush_page(self):
        """Composite ink layer onto paper and append to pages list — skip blanks."""
        # Check if anything was drawn (any non-transparent pixel)
        extrema = self.current_layer.getextrema()
        # extrema is ((r_min,r_max),(g_min,g_max),(b_min,b_max),(a_min,a_max))
        if extrema[3][1] == 0:      # alpha channel max = 0 → completely blank
            return
        self.pages.append(self.current_layer)   # raw ink, composed later

    def finish(self):
        """Called at end of document — flush last page."""
        if self.current_layer is not None:
            self._flush_page()
            self.current_layer = None


# ---------------------------------------------------------------------------
# PCL Escape-sequence parser
# ---------------------------------------------------------------------------
# Parameterized PCL:  ESC [!-/] group_char  value  terminator
_PCL_PARAM_RE = re.compile(
    rb'\x1b'
    rb'([!-/])'          # parameterized character (group 1)
    rb'([ -~])'          # group character (group 2)
    rb'(-?\d*\.?\d*)'    # numeric value (group 3)
    rb'([A-Z])'          # termination character (group 4)
)

# Two-character ESC sequences:  ESC + one char
_PCL_2CHAR_RE = re.compile(rb'\x1b([^!-/&(*+])')


def parse_pcl_stream(data: bytes):
    """
    Yield tokens from a PCL/ASCII stream.
    Each token is one of:
      ('char',  int byte_value)
      ('cmd',   param_char, group_char, value, term)   # parameterized PCL
      ('esc2',  char)                                   # two-char ESC
      ('ctrl',  int byte_value)                         # CR LF FF BS HT VT
    """
    i = 0
    n = len(data)
    while i < n:
        b = data[i]

        # ── ESC ──
        if b == 0x1B and i + 1 < n:
            nxt = data[i+1]

            # Parameterized?  ESC [!-/] ...
            if 0x21 <= nxt <= 0x2F:
                # Read full sequence (can be combined: ESC ( s 3B 1I means 3B + 1I)
                j = i
                seq = bytearray()
                seq.append(data[j]);  j += 1   # ESC
                seq.append(data[j]);  j += 1   # param char
                seq.append(data[j]);  j += 1   # group char
                # collect numeric + letter, watching for combined seqs
                num_buf = b''
                while j < n:
                    c = data[j]; j += 1
                    if c == 0x2D or c == 0x2E or (0x30 <= c <= 0x39):
                        num_buf += bytes([c])
                    elif 0x41 <= c <= 0x5A:         # uppercase: terminator
                        yield ('cmd', chr(seq[1]), chr(seq[2]),
                               num_buf.decode('ascii', errors='replace'), chr(c))
                        num_buf = b''
                        # Check if combined (lowercase letter follows = another value)
                        if j < n and 0x61 <= data[j] <= 0x7A:
                            # Combined sequence: same ESC + param + group, new value+term
                            pass  # num_buf will accumulate next
                        else:
                            break
                    elif 0x61 <= c <= 0x7A:         # lowercase: combined
                        yield ('cmd', chr(seq[1]), chr(seq[2]),
                               num_buf.decode('ascii', errors='replace'),
                               chr(c - 0x20))       # capitalise the terminator
                        num_buf = b''
                    else:
                        break
                i = j
                continue

            # Two-character ESC (e.g., ESC E reset)
            yield ('esc2', chr(nxt))
            i += 2
            continue

        # ── Control characters ──
        if b in (0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D):
            yield ('ctrl', b)
            i += 1
            continue

        # ── Printable / CP437 extended ──
        if b >= 0x20 or b in (0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
                               0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x14,
                               0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1C,
                               0x1D, 0x1E, 0x1F, 0x7F):
            yield ('char', b)
        i += 1


# ---------------------------------------------------------------------------
# Rendering engine
# ---------------------------------------------------------------------------
class HP500Renderer:
    """Processes a PCL/ASCII token stream and renders to PrinterState pages."""

    # Ink color in NLQ: near-black with faint warm undertone
    INK_NLQ   = (18, 16, 22)
    # Draft ink: slightly lighter / less saturated
    INK_DRAFT = (40, 38, 45)
    # Ideal mode: pure black
    INK_IDEAL = (0, 0, 0)

    def __init__(self, state: PrinterState, artifacts=True, ideal=False):
        self.st = state
        self.artifacts = artifacts and not ideal
        self.ideal = ideal
        self._rng = random.Random(42)  # deterministic for reproducible output

    # ── public entry point ──────────────────────────────────────────────────

    def feed(self, data: bytes):
        st = self.st
        for tok in parse_pcl_stream(data):
            kind = tok[0]
            if kind == 'char':
                self._print_char(tok[1])
            elif kind == 'ctrl':
                self._handle_ctrl(tok[1])
            elif kind == 'esc2':
                self._handle_esc2(tok[1])
            elif kind == 'cmd':
                self._handle_cmd(*tok[1:])
        st.finish()

    # ── Control character handling ──────────────────────────────────────────

    def _handle_ctrl(self, b: int):
        st = self.st
        if b == 0x0D:   # CR
            st.cursor_x = st.margin_left
        elif b == 0x0A:  # LF
            st.cursor_y += st.line_h
            self._check_page_break()
        elif b == 0x0B:  # VT — vertical tab (treated as LF on DeskJet 500)
            st.cursor_y += st.line_h
            self._check_page_break()
        elif b == 0x0C:  # FF — form feed
            st._new_page()
        elif b == 0x08:  # BS — backspace
            st.cursor_x = max(st.margin_left, st.cursor_x - st.char_w)
        elif b == 0x09:  # HT — horizontal tab
            for stop in st.tab_stops:
                if stop > st.cursor_x + 2:
                    st.cursor_x = stop
                    break

    def _handle_esc2(self, ch: str):
        st = self.st
        if ch == 'E':   # ESC E — reset printer
            st.bold      = False
            st.italic    = False
            st.underline = False
            st.double_wide = False
            st.cpi       = 10.0
            st.lpi       = 6.0
            st.point_size = 12.0
        elif ch == '9':  # ESC 9 — clear margins
            st.margin_left  = round(0.5 * DPI)
            st.margin_right = st.page_w - round(0.5 * DPI)
        elif ch == '=':  # ESC = — half line feed up
            st.cursor_y -= st.line_h // 2

    def _handle_cmd(self, param: str, group: str, val_s: str, term: str):
        st = self.st
        try:
            val = float(val_s) if val_s else 0.0
        except ValueError:
            val = 0.0
        ival = int(val)

        # ── &l (lowercase L) — page formatting ──────────────────────────────
        if param == '&' and group == 'l':
            if term == 'A':   # paper size
                sizes = {1: 'executive', 2: 'letter', 3: 'legal', 26: 'a4', 27: 'a4'}
                st.paper = sizes.get(ival, st.paper)
                st._recalc_page_dims()
            elif term == 'O':  # orientation
                st.orientation = 'landscape' if ival == 1 else 'portrait'
                st._recalc_page_dims()
            elif term == 'C':  # VMI (1/48 inch units)
                if val > 0:
                    st.lpi = 48.0 / val
            elif term == 'D':  # LPI
                if val > 0:
                    st.lpi = val
            elif term == 'E':  # top margin (lines)
                st.margin_top = st.margin_top + round(ival * st.line_h)
            elif term == 'F':  # text length (lines)
                st.margin_bottom = st.margin_top + round(ival * st.line_h)
            elif term == 'H':  # paper source — ignore
                pass

        # ── &a — cursor / margin positioning ────────────────────────────────
        elif param == '&' and group == 'a':
            if term == 'L':   # left margin (columns)
                st.margin_left = round(ival * st.char_w)
                st._rebuild_tabs()
            elif term == 'M':  # right margin (columns)
                st.margin_right = round(ival * st.char_w)
            elif term == 'C':  # cursor column (decipoints)
                st.cursor_x = st.margin_left + round(val * DPI / 720)
            elif term == 'R':  # cursor row (decipoints)
                st.cursor_y = st.margin_top + round(val * DPI / 720)

        # ── &k — horizontal motion ───────────────────────────────────────────
        elif param == '&' and group == 'k':
            if term == 'H':   # HMI (1/120 inch)
                if val > 0:
                    st.cpi = 120.0 / val
            elif term == 'S':  # pitch mode
                if ival == 2:
                    st.cpi = 16.67   # compressed

        # ── (s — primary font (stroke weight / style / pitch / size) ─────────
        elif param == '(' and group == 's':
            if term == 'P':   # spacing (0=fixed, 1=proportional)
                pass  # we always render fixed-pitch
            elif term == 'H':  # pitch (CPI)
                if val > 0:
                    st.cpi = val
            elif term == 'V':  # point size
                if val > 0:
                    st.point_size = val
            elif term == 'B':  # stroke weight (3 or 4 = bold, 0 = normal)
                st.bold = (ival >= 3)
            elif term == 'I':  # style (1 = italic)
                st.italic = (ival == 1)
            elif term == 'U':  # underline
                st.underline = (ival == 1)
            elif term == 'S':  # symbol set style — ignore for now
                pass

        # ── (  — symbol set ──────────────────────────────────────────────────
        elif param == '(' and group == ' ':
            # e.g. ESC ( 10U = PC-8 (CP437)
            pass   # we always use CP437

        # ── *p — absolute cursor positioning ────────────────────────────────
        elif param == '*' and group == 'p':
            if term == 'X':   # X in decipoints (1/720 inch)
                st.cursor_x = round(val * DPI / 720)
            elif term == 'Y':
                st.cursor_y = round(val * DPI / 720)

        # ── *b — raster graphics  (skip data) ──────────────────────────────
        elif param == '*' and group == 'b':
            pass   # raster graphics not emulated

    # ── Character rendering ─────────────────────────────────────────────────

    def _print_char(self, byte_val: int):
        st = self.st
        # Map CP437 byte to Unicode glyph
        ch = CP437.get(byte_val, chr(byte_val))

        font = get_font(st.point_size, bold=st.bold, italic=st.italic)
        cw = st.char_w
        lh = st.line_h

        # HP DeskJet 500 does NOT word-wrap — it clips at the right margin.
        # Characters that fall past the margin simply don't print (they'd
        # fall off the paper onto the platen in real life).
        if st.cursor_x + cw > st.margin_right:
            return  # clip — advance nothing, discard glyph

        # Vertical centering of glyph within the character cell
        # Glyph ascent is font.getmetrics()[0]; we nudge so baseline looks right
        ascent, descent = font.getmetrics()
        # Render so baseline sits at cursor_y + lh - descent_margin
        baseline_y = st.cursor_y + max(0, lh - ascent - 2)

        # NLQ vs Draft vs Ideal ink color
        if self.ideal:
            ink_base = self.INK_IDEAL
        elif st.nlq:
            ink_base = self.INK_NLQ
        else:
            ink_base = self.INK_DRAFT

        # Add per-character ink variation (subtle) — disabled in ideal mode
        if self.artifacts and not self.ideal:
            r_jitter = self._rng.randint(-6, 6)
            b_jitter = self._rng.randint(-6, 6)
            ink = (
                max(0, min(255, ink_base[0] + r_jitter)),
                max(0, min(255, ink_base[1])),
                max(0, min(255, ink_base[2] + b_jitter)),
            )
            # slight position jitter (±1px) for inkjet nozzle wobble
            dx = self._rng.randint(-1, 1) if st.nlq else self._rng.randint(-2, 2)
            dy = self._rng.randint(-1, 1) if st.nlq else self._rng.randint(-2, 2)
        else:
            ink = ink_base
            dx, dy = 0, 0

        draw = st.current_draw

        # ── Draw character glyph ──
        draw.text(
            (st.cursor_x + dx, baseline_y + dy),
            ch,
            font=font,
            fill=ink + (255,)   # RGBA, fully opaque
        )

        # ── Underline ──
        if st.underline:
            ul_y = baseline_y + ascent + 2

            base_width = UNDERLINE_THICKNESS
            if self.artifacts:
                base_width += 1
            else:
                base_width += 2

            draw.line(
                [(st.cursor_x, ul_y), (st.cursor_x + cw - 1, ul_y)],
                fill=ink + (220,),
                width=base_width
            )

        # ── Draft mode banding: simulate inkjet pass lines ──
        if self.artifacts and not st.nlq:
            # Every ~8 pixels, slightly lighter stripe (pass boundary)
            pass_height = round(DPI / 37.5)   # 8 inkjet nozzles at 300 DPI
            # Draw a semi-transparent stripe if cursor_y falls on a pass boundary
            band_y = (baseline_y // pass_height) * pass_height
            if (band_y % (pass_height * 2)) == 0:
                # draw a 1px faint horizontal gap
                draw.line(
                    [(st.cursor_x, band_y), (st.cursor_x + cw, band_y)],
                    fill=(255, 255, 255, 30),
                    width=1
                )

        # ── Advance cursor ──
        st.cursor_x += cw

    def _check_page_break(self):
        st = self.st
        if st.cursor_y + st.line_h > st.margin_bottom:
            st._new_page()


# ---------------------------------------------------------------------------
# Page compositing & artifact application
# ---------------------------------------------------------------------------

def _make_paper_texture(w, h, rng, aged=True):
    """
    Create a realistic paper background:
    - Slightly warm off-white base (period paper)
    - Very subtle random fiber texture
    - Faint edge darkening (shadow from stack)
    """
    # Base paper color  (warm white, slightly yellowed)
    if aged:
        base_r, base_g, base_b = 245, 241, 230
    else:
        base_r, base_g, base_b = 252, 251, 248

    # Create as numpy array for fast ops — fall back to pure PIL if unavailable
    try:
        import numpy as np
        arr = np.full((h, w, 3), [base_r, base_g, base_b], dtype=np.uint8)
        # Paper fiber noise (very low amplitude)
        noise = rng.normal(0, 2.5, (h, w)).astype(np.int16)
        arr[..., 0] = np.clip(arr[..., 0] + noise, 0, 255)
        arr[..., 1] = np.clip(arr[..., 1] + noise, 0, 255)
        arr[..., 2] = np.clip(arr[..., 2] + noise // 2, 0, 255)

        # Vignette: darken edges very slightly
        yy, xx = np.mgrid[0:h, 0:w]
        cx, cy = w / 2, h / 2
        dist = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2)
        vign = np.clip(1.0 - dist * 0.04, 0.92, 1.0)
        arr = np.clip(arr * vign[..., np.newaxis], 0, 255).astype(np.uint8)

        paper = Image.fromarray(arr, 'RGB')
    except ImportError:
        paper = Image.new('RGB', (w, h), (base_r, base_g, base_b))

    return paper


def _apply_nlq_ink_bleed(ink_layer: Image.Image) -> Image.Image:
    """
    Simulate HP DeskJet 500 NLQ ink bleed:
    - Light Gaussian blur (ink soaks into paper)
    - Slight density boost to compensate for spread
    """
    # Separate alpha (ink mask) and color
    r, g, b, a = ink_layer.split()
    # Blur just the alpha to spread ink
    a_blurred = a.filter(ImageFilter.GaussianBlur(radius=0.7))
    result = Image.merge('RGBA', (r, g, b, a_blurred))
    return result


def _apply_draft_artifacts(ink_layer: Image.Image, rng) -> Image.Image:
    """
    Draft mode: simulate coarser inkjet dots and pass banding.
    """
    # Slightly more blur (nozzles less focused in draft)
    r, g, b, a = ink_layer.split()
    a_blurred = a.filter(ImageFilter.GaussianBlur(radius=1.2))
    # Add horizontal banding (every ~8px row, slight density drop)
    return Image.merge('RGBA', (r, g, b, a_blurred))


def _add_page_crease(paper: Image.Image, rng) -> Image.Image:
    """Very occasionally add a faint vertical or horizontal crease."""
    if rng.random() > 0.25:
        return paper
    w, h = paper.size
    draw = ImageDraw.Draw(paper)
    if rng.random() < 0.5:
        # horizontal crease
        y = rng.randint(h // 4, 3 * h // 4)
        draw.line([(0, y), (w, y)], fill=(220, 215, 200), width=1)
    else:
        # vertical crease (from folding)
        x = rng.randint(w // 4, 3 * w // 4)
        draw.line([(x, 0), (x, h)], fill=(220, 215, 200), width=1)
    return paper


def compose_page(ink_layer: Image.Image, nlq: bool, artifacts: bool,
                 rng, page_num: int, ideal: bool = False) -> Image.Image:
    """Composite ink onto paper with all post-processing."""
    w, h = ink_layer.size

    if ideal:
        # Perfect white paper, no processing
        paper = Image.new('RGB', (w, h), (255, 255, 255))
        ink_composite = ink_layer
    elif artifacts:
        import random as _r
        # Use a seeded per-page RNG
        try:
            import numpy as np
            np_rng = np.random.default_rng(page_num * 137 + 7)
            paper = _make_paper_texture(w, h, np_rng, aged=True)
        except ImportError:
            paper = Image.new('RGB', (w, h), (245, 241, 230))
        paper = _add_page_crease(paper, rng)

        if nlq:
            ink_composite = _apply_nlq_ink_bleed(ink_layer)
        else:
            ink_composite = _apply_draft_artifacts(ink_layer, rng)
    else:
        paper = Image.new('RGB', (w, h), (255, 255, 255))
        ink_composite = ink_layer

    # Alpha-composite ink onto paper
    paper_rgba = paper.convert('RGBA')
    result = Image.alpha_composite(paper_rgba, ink_composite)
    return result.convert('RGB')


# ---------------------------------------------------------------------------
# PDF assembly using ReportLab
# ---------------------------------------------------------------------------

def build_pdf(pages_rgb: list, output_path: str, paper: str, orientation: str):
    """Render list of PIL RGB images into a PDF at correct physical size."""
    w_in, h_in = PAPER_SIZES.get(paper, PAPER_SIZES['letter'])
    if orientation == 'landscape':
        w_in, h_in = h_in, w_in
    w_pt = w_in * 72   # points
    h_pt = h_in * 72

    c = rl_canvas.Canvas(output_path, pagesize=(w_pt, h_pt))
    c.setTitle('HP DeskJet 500 Emulator Output')
    c.setAuthor('HP DeskJet 500 Emulator')
    c.setSubject('Printed document — 300 DPI')

    for page_img in pages_rgb:
        buf = BytesIO()
        # Save as JPEG (quality 92) for authentic inkjet look + compact file size
        page_img.save(buf, format='JPEG', quality=92, subsampling=0, optimize=True)
        buf.seek(0)
        img_reader = ImageReader(buf)
        c.drawImage(
            img_reader, 0, 0, width=w_pt, height=h_pt,
            preserveAspectRatio=True, anchor='nw'
        )
        c.showPage()

    c.save()


# ---------------------------------------------------------------------------
# Convenience: generate a demo document
# ---------------------------------------------------------------------------

DEMO_DOC = b"""\
\x1bE\x1b(10U\x1b(s12.00V\x1b(s0B\x1b(s0I\
HP DeskJet 500 Emulator \x14 System Test\r\n\
\x1b(s3B================================================================================\x1b(s0B\r\n\
\r\n\
\x1b(s3BDocument Information:\x1b(s0B\r\n\
  Printer Model  : HP DeskJet 500 (internal font emulation)\r\n\
  Emulation Mode : PCL3 / HP-PCL\r\n\
  Symbol Set     : PC-8 (Code Page 437)\r\n\
  Resolution     : 300 x 300 DPI\r\n\
  Quality Mode   : Near Letter Quality (NLQ)\r\n\
\r\n\
\x1b(s3BExtended ASCII / CP437 Character Table:\x1b(s0B\r\n\
\r\n\
  Smileys & Symbols : \x01\x02\x03\x04\x05\x06\x07\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1c\x1d\x1e\x1f\r\n\
  Latin Extended   : \x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\r\n\
  Spanish/French   : \xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xaa\xab\xac\xad\xae\xaf\r\n\
  Math Symbols     : \xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\r\n\
  Block Elements   : \xb0\xb1\xb2\xdb\xdc\xdd\xde\xdf\r\n\
\r\n\
\x1b(s3BSingle-Line Box Drawing:\x1b(s0B\r\n\
\r\n\
  \xda\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc2\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xbf\r\n\
  \xb3  Column A        \xb3  Column B         \xb3\r\n\
  \xc3\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc5\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xb4\r\n\
  \xb3  Item One        \xb3  Value 001        \xb3\r\n\
  \xb3  Item Two        \xb3  Value 002        \xb3\r\n\
  \xb3  Item Three      \xb3  Value 003        \xb3\r\n\
  \xc0\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc1\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xc4\xd9\r\n\
\r\n\
\x1b(s3BDouble-Line Box Drawing:\x1b(s0B\r\n\
\r\n\
  \xc9\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcb\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xbb\r\n\
  \xba  INVOICE         \xba  NUMBER           \xba\r\n\
  \xcc\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xce\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xb9\r\n\
  \xba  Widget Type A   \xba  00042            \xba\r\n\
  \xba  Widget Type B   \xba  00099            \xba\r\n\
  \xc8\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xca\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xbc\r\n\
\r\n\
\x1b(s3BMixed Single/Double Box Drawing:\x1b(s0B\r\n\
\r\n\
  \xd5\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xd1\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xd1\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xb8\r\n\
  \xb3  Description     \xb3  Qty   \xb3  Price   \xb3\r\n\
  \xd4\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcf\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcf\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xcd\xbe\r\n\
\r\n\
\r\n\
\x1b(s3BItalic and Underline Modes:\x1b(s0B\r\n\
\r\n\
  Normal text  \x1b(s3B Bold text \x1b(s0B  \x1b(s1I Italic text \x1b(s0I \x1b(s1UUnderline text\x1b(s0U\r\n\
\r\n\
\r\n\
\x0c"""

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='HP DeskJet 500 Family Print Emulator')
    parser.add_argument('input',  nargs='?', default=None,
                        help='Input file (ASCII/PCL).  Omit to print demo doc.')
    parser.add_argument('output', nargs='?', default='output.pdf',
                        help='Output PDF path  [default: output.pdf]')
    parser.add_argument('--paper', choices=['letter','legal','a4','executive'],
                        default='letter', help='Paper size [default: letter]')
    parser.add_argument('--landscape', action='store_true',
                        help='Landscape orientation')
    parser.add_argument('--draft', action='store_true',
                        help='Draft (lower quality) rendering mode')
    parser.add_argument('--cpi', type=float, default=10.0,
                        help='Characters per inch [default: 10]')
    parser.add_argument('--lpi', type=float, default=6.0,
                        help='Lines per inch [default: 6]')
    parser.add_argument('--ideal', action='store_true',
                        help='Ideal copy mode: pure black ink, white paper, zero jitter/bleed')
    parser.add_argument('--no-artifacts', dest='artifacts', action='store_false',
                        help='Disable paper / ink aging artifacts')
    parser.set_defaults(artifacts=True)
    args = parser.parse_args()

    orientation = 'landscape' if args.landscape else 'portrait'
    nlq = not args.draft

    # ideal overrides artifacts and draft
    if args.ideal:
        nlq = True
        args.artifacts = False

    # ── Load input ────────────────────────────────────────────────────────
    if args.input is None:
        print('No input file specified — printing built-in demo document.')
        data = DEMO_DOC
    else:
        with open(args.input, 'rb') as f:
            data = f.read()

    quality_label = "Ideal (flat)" if getattr(args,'ideal',False) else ("NLQ" if nlq else "Draft")
    print(f'Paper     : {args.paper}  {orientation}')
    print(f'Quality   : {quality_label}')
    print(f'Pitch     : {args.cpi} CPI  /  {args.lpi} LPI')
    print(f'Artifacts : {"on" if args.artifacts else "off"}')
    print(f'Output    : {args.output}')
    print()

    # ── Set up printer state & renderer ──────────────────────────────────
    state = PrinterState(
        paper=args.paper,
        orientation=orientation,
        default_cpi=args.cpi,
        default_lpi=args.lpi,
        nlq=nlq,
    )
    renderer = HP500Renderer(state, artifacts=args.artifacts, ideal=getattr(args,'ideal',False))
    renderer.feed(data)

    total_pages = len(state.pages)
    print(f'Pages rendered: {total_pages}')

    # ── Compose pages (paper + ink + artifacts) ───────────────────────────
    import random as _pyrandom
    rng = _pyrandom.Random(999)
    composed = []
    for i, ink_layer in enumerate(state.pages):
        print(f'  Compositing page {i+1}/{total_pages}...', end='\r')
        page_rgb = compose_page(ink_layer, nlq, args.artifacts, rng, i, ideal=args.ideal)
        composed.append(page_rgb)
    print()

    # ── Build PDF ─────────────────────────────────────────────────────────
    print('Building PDF...')
    build_pdf(composed, args.output, args.paper, orientation)
    print(f'Done!  →  {args.output}')


if __name__ == '__main__':
    main()
