# HP DeskJet 500 Print Emulator

A nostalgic print emulator that converts ASCII / PCL text files into PDF output that looks exactly like it came off an HP DeskJet 500 series inkjet printer over a parallel port in DOS — aged paper, ink bleed, nozzle jitter and all.

Supports the full 8-bit CP437 character set (box drawing, block elements, Greek, math symbols, Latin extended), HP PCL3 escape codes, Near Letter Quality and Draft rendering modes, and period-accurate page artifacts.

---

## Requirements

Ubuntu / Xubuntu / Debian and derivatives, 20.04 LTS onwards.

| apt package | Purpose |
|---|---|
| `python3` | Runtime — pre-installed on all Ubuntu images |
| `python3-pil` | Bitmap rendering, font rasterization, JPEG output |
| `python3-reportlab` | PDF assembly |
| `python3-numpy` | Paper texture noise (optional — falls back gracefully) |
| `fonts-dejavu-mono` | Regular, Bold, Italic, Bold-Italic glyph variants |

> **Ubuntu 24.04 LTS and later:** `python3-reportlab` is in the **universe** repository.  
> `make install` and `install.sh` enable it automatically.

---

## Installation

### Quick start

```bash
git clone <repo>
cd hp500-emulator
make install
```

`make install` does three things:
1. Runs `apt-get install` for all dependencies
2. Enables the universe repo first if needed (24.04+)
3. Installs the `hp500` command to `/usr/local/bin` using `install -Dm755`

The `hp500` command is the Python script itself — it carries a `#!/usr/bin/env python3` shebang so the OS invokes the interpreter directly with no wrapper needed.

To install to your home directory instead (no sudo):

```bash
make install INSTALL_DIR=~/.local/bin
```

### Verify the install

```bash
make check
```

```
Python imports
──────────────────────────────────────
  PIL        10.2.0
  reportlab  4.1.0
  numpy      1.26.4
[OK]    All imports OK

Font files
──────────────────────────────────────
  ✓  DejaVuSansMono.ttf
  ✓  DejaVuSansMono-Bold.ttf
  ✓  DejaVuSansMono-Oblique.ttf
  ✓  DejaVuSansMono-BoldOblique.ttf
```

### Uninstall

```bash
make uninstall
```

---

## Usage

Once installed, the `hp500` command is on your PATH and called directly — no `python3` prefix required.

### Basic

```bash
hp500 input.txt output.pdf
```

Omit the input file to print the built-in two-page demo document:

```bash
hp500
```

### Quality modes

| Command | Mode | Description |
|---|---|---|
| `hp500 in.txt out.pdf` | **NLQ** | Near Letter Quality. Warm near-black ink, subtle ink bleed, paper fiber texture, per-character nozzle jitter. |
| `hp500 in.txt out.pdf --draft` | **Draft** | Coarser inkjet dots, pass-line banding, lighter ink. |
| `hp500 in.txt out.pdf --ideal` | **Ideal** | Pure black on white, zero jitter, no blur, no artifacts. For archiving or diffing documents. |
| `hp500 in.txt out.pdf --no-artifacts` | **NLQ clean** | NLQ ink rendering, plain white paper, no aging. |

### Paper and pitch options

```bash
hp500 input.txt output.pdf --paper a4
hp500 input.txt output.pdf --paper legal
hp500 input.txt output.pdf --landscape
hp500 input.txt output.pdf --cpi 17        # compressed (17 chars/inch)
hp500 input.txt output.pdf --lpi 8         # tighter line spacing
```

| Option | Values | Default |
|---|---|---|
| `--paper` | `letter` `a4` `legal` `executive` | `letter` |
| `--landscape` | flag | portrait |
| `--cpi` | float | `10` |
| `--lpi` | float | `6` |

### All options

```
hp500 --help

positional arguments:
  input         Input file (ASCII/PCL). Omit to print demo.
  output        Output PDF path  [default: output.pdf]

options:
  --paper       letter | a4 | legal | executive
  --landscape   Landscape orientation
  --draft       Draft quality mode
  --ideal       Ideal copy mode: pure black, white paper, zero jitter
  --no-artifacts  Disable paper and ink aging artifacts
  --cpi         Characters per inch  [default: 10]
  --lpi         Lines per inch  [default: 6]
```

---

## Make targets

```bash
make install                         # apt install + install hp500 to /usr/local/bin
make install INSTALL_DIR=~/.local/bin  # install to home dir (no sudo)
make uninstall                       # remove /usr/local/bin/hp500
make check                           # verify imports and fonts
make demo                            # render built-in demo: NLQ + Draft + Ideal
make demo PAPER=a4                   # demo on A4 paper
make run INPUT=myfile.txt            # NLQ render → output.pdf
make run INPUT=myfile.txt OUTPUT=myfile.pdf
make run-draft INPUT=myfile.txt OUTPUT=draft.pdf
make run-ideal INPUT=myfile.txt OUTPUT=clean.pdf
make test                            # check + demo + verify all outputs exist
make clean                           # remove generated PDFs
make help                            # show all targets and variables
```

---

## PCL escape codes supported

These are the same codes the HP DeskJet 500 responded to over its Centronics parallel port.

### Two-character sequences

| Sequence | Effect |
|---|---|
| `ESC E` | Reset printer to defaults |
| `ESC 9` | Clear left/right margins |
| `ESC =` | Half line feed (cursor up ½ line) |

### Font  `ESC ( s # X`

### Font Style

| Code         | Effect        |
|--------------|---------------|
| `ESC ( s 3B` | Bold on       |
| `ESC ( s 0B` | Bold off      |
| `ESC ( s 1I` | Italic on     |
| `ESC ( s 0I` | Italic off    |
| `ESC ( s 1U` | Underline on  |
| `ESC ( s 0U` | Underline off |

### Font Metrics

| Code          | Effect           |
|---------------|------------------|
| `ESC ( s 10H` | 10 CPI (default) |
| `ESC ( s 17H` | 17 CPI compressed|
| `ESC ( s 12V` | 12 point         |

### Page `ESC & l # X`

| Code | Effect |
|---|---|
| `ESC & l 2A` | Letter paper |
| `ESC & l 26A` | A4 paper |
| `ESC & l 0O` | Portrait |
| `ESC & l 1O` | Landscape |
| `ESC & l 6D` | 6 LPI |
| `ESC & l 8D` | 8 LPI |
| `ESC & l #E` | Top margin (lines) |
| `ESC & l #F` | Text length (lines) |

### Cursor `ESC & a # X` / `ESC * p # X`

| Code | Effect |
|---|---|
| `ESC & a 5L` | Left margin at column 5 |
| `ESC & a 75M` | Right margin at column 75 |
| `ESC * p 720X` | Absolute X position (decipoints, 1/720 inch) |
| `ESC * p 720Y` | Absolute Y position |

Control characters `CR` `LF` `FF` `BS` `HT` `VT` are all handled as the real printer handled them.

---

## CP437 quick reference

The full 256-character IBM Code Page 437 is rendered. All byte values print their CP437 glyph except `0x08`–`0x0D` which are interpreted as printer controls.

```
CP437 CHARACTER TABLE (00–FF)
Hex rows × columns (0–F)

     00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F
00 |    ☺  ☻  ♥  ♦  ♣  ♠  •  ◘  ○  ◙  ♂  ♀  ♪  ♫  ☼
10 | ►  ◄  ↕  ‼  ¶  §  ▬  ↨  ↑  ↓  →  ←  ∟  ↔  ▲  ▼
20 |    !  "  #  $  %  &  '  (  )  *  +  ,  -  .  /
30 | 0  1  2  3  4  5  6  7  8  9  :  ;  <  =  >  ?
40 | @  A  B  C  D  E  F  G  H  I  J  K  L  M  N  O
50 | P  Q  R  S  T  U  V  W  X  Y  Z  [  \  ]  ^  _
60 | `  a  b  c  d  e  f  g  h  i  j  k  l  m  n  o
70 | p  q  r  s  t  u  v  w  x  y  z  {  |  }  ~  ⌂
80 | Ç  ü  é  â  ä  à  å  ç  ê  ë  è  ï  î  ì  Ä  Å
90 | É  æ  Æ  ô  ö  ò  û  ù  ÿ  Ö  Ü  ¢  £  ¥  ₧  ƒ
A0 | á  í  ó  ú  ñ  Ñ  ª  º  ¿  ⌐  ¬  ½  ¼  ¡  «  »
B0 | ░  ▒  ▓  │  ┤  ╡  ╢  ╖  ╕  ╣  ║  ╗  ╝  ╜  ╛  ┐
C0 | └  ┴  ┬  ├  ─  ┼  ╞  ╟  ╚  ╔  ╩  ╦  ╠  ═  ╬  ╧
D0 | ╨  ╤  ╥  ╙  ╘  ╒  ╓  ╫  ╪  ┘  ┌  █  ▄  ▌  ▐  ▀
E0 | α  ß  Γ  π  Σ  σ  µ  τ  Φ  Θ  Ω  δ  ∞  φ  ε  ∩
F0 | ≡  ±  ≥  ≤  ⌠  ⌡  ÷  ≈  °  ∙  ·  √  ⁿ  ²  ■                
```

---

## Column geometry

At 10 CPI with 0.5 inch margins on letter paper:

```
Page width    = 8.5"
Left margin   = 0.5"  →  right margin = 0.5"
Printable     = 7.5" × 10 CPI = 75 characters maximum per line
```

Lines longer than 75 characters are clipped at the right margin — the same behaviour as the real printer (characters past the margin hit the platen and don't print). There is no word wrap.

At 17 CPI (compressed): `7.5" × 17 = 127 characters` per line.

---

## Rendering pipeline

```
Input file (bytes)
    │
    ▼
PCL parser          Tokenises escape sequences, control codes, CP437 chars
    │
    ▼
HP500Renderer       Maintains printer state (cursor, margins, font, mode)
    │               Renders each glyph onto a 300 DPI RGBA ink layer
    ▼
compose_page()      Composites ink onto aged paper (NumPy fiber noise + vignette)
    │               NLQ: Gaussian ink bleed    Draft: coarser blur + pass banding
    │               Optional: page crease artifact
    ▼
build_pdf()         Embeds each page as JPEG into a ReportLab PDF
                    Physical page dimensions set exactly in points (1/72 inch)
```

Resolution is fixed at **300 × 300 DPI**, the HP DeskJet 500's native print resolution.

---

## File layout

```
hp500_emulator.py   Main script — also the installed command (shebang executable)
install.sh          Standalone installer (alternative to make install)
Makefile            Build, install, test, and render targets
README.md           This file
```

---

## Compatibility

| OS | Release | python3-pil | python3-reportlab | python3-numpy |
|---|---|---|---|---|
| Xubuntu | 20.04 LTS Focal | 8.1.2 | 3.5.34 | 1.19.5 |
| Xubuntu | 22.04 LTS Jammy | 9.0.1 | 3.6.8 | 1.21.5 |
| Ubuntu  | 24.04 LTS Noble | 10.2.x | 4.1.0 ¹ | 1.26.4 |
| Ubuntu  | 24.10 Oracular | ✓ | 4.2.2 ¹ | ✓ |
| Ubuntu  | 25.04 Plucky | ✓ | 4.3.1 ¹ | ✓ |

¹ In universe repository — enabled automatically by `make install` and `install.sh`.

---

## License

MIT. Do whatever you like with it. If you use it to print (or email) an actual invoice from 1993, that would be excellent.

MIT License

Copyright (c) 2026 Dave Collins

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
