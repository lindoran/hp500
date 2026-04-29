# HP DeskJet 500 Print Emulator

A nostalgic print emulator that converts ASCII / PCL text files into PDF output that looks like it came off an HP DeskJet 500 series inkjet printer over a parallel port in DOS — aged paper, ink bleed, and optional period artifacts.

Supports the full 8-bit CP437 character set (box drawing, block elements, Greek, math symbols, Latin extended), HP PCL3 escape codes, Near Letter Quality and Draft rendering modes, and period-accurate page artifacts.

---

## Why not GhostPCL?

GhostPCL is a full PCL5/PCL XL language interpreter. It is feature-complete across a wide range of professional printers, produces geometrically perfect output, and is the right tool when the goal is faithful, device-neutral rendering of a PCL stream. While GhostPCL produces "better than life" archival copies and can work with a text stream, it is more broadly aimed at all data streams a printer would have encountered.

hp500 is something different: a hardware simulator for one specific printer. It implements the PCL3 subset the HP DeskJet 500 actually responded to over its Centronics parallel port — no more, no less — and targets the CP437 character set that DOS software sent to it. Output is intentionally imperfect in the way that printer was imperfect: ink bleed, aged paper, draft banding, and period artifacts are features, not defects. An archival (ideal) mode is available when clean output is wanted, but the default render is what the page looked like coming out of the tray, not what the data said it should look like.

hp500 focuses exclusively on text-based files generated for DOS environments with embedded PCL3 control codes — the kind commonly found in hobbyist manuals, infamous online video game walkthroughs, and similar material built around the CP437 character set.

Furthermore, it automatically applies an invisible character-level text layer to the PDF, allowing content to be copied and searched from any viewer that expects Unicode. This effectively brings 1980s and 1990s-era documentation into the modern computing experience in a format that is simpler and more accessible for consumption and research.

Lastly, hp500 is well suited for properly formatting forms built in ASCII environments like MS-DOS Edit. Rather than treating each character as an isolated glyph, the renderer connects underscore sequences into solid fill lines and joins CP437 box-drawing characters into seamless borders — so form fields and tables that were carefully drawn in a DOS text editor arrive on the page looking the way their author intended, not as a jumble of disconnected symbols. Additionally, the margin spacing is handled with a granular integer-based algorithm that preserves the column-exact layout those environments depended on.

In other words: this is a fanservice, printer-centric documentation archival tool.

---

## Requirements

Ubuntu flavors / Linux Mint / Debian and derivatives, 20.04 LTS onwards.

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

To install the `hp500` command to your home directory instead of `/usr/local/bin`:

```bash
make install INSTALL_DIR=~/.local/bin
```

The standalone installer does the same dependency checks and installs the same `hp500` command:

```bash
./install.sh
./install.sh ~/.local/bin
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

To write the built-in demo to a specific PDF:

```bash
hp500 --demo -o demo.pdf
```

### Quality modes

| Command | Mode | Description |
|---|---|---|
| `hp500 in.txt out.pdf` | **NLQ** | Near Letter Quality. Warm near-black ink, subtle ink bleed, aged paper fiber texture. |
| `hp500 in.txt out.pdf --draft` | **Draft** | Lighter ink with stronger blur; add `--banding` for pass-line artifacts. |
| `hp500 in.txt out.pdf --ideal` | **Ideal** | Pure black on white, zero jitter, no blur, no artifacts. For archiving or diffing documents. |
| `hp500 in.txt out.pdf --no-artifacts` | **NLQ clean** | NLQ ink rendering, plain white paper, no blur or aging. |

### Artifact controls

Defaults are intentionally restrained: NLQ, aged paper, and ink bleed are on; jitter, dot variation, banding, and creases are off.

```bash
hp500 in.txt out.pdf --white-paper
hp500 in.txt out.pdf --no-ink-bleed
hp500 in.txt out.pdf --jitter
hp500 in.txt out.pdf --dot-variation
hp500 in.txt out.pdf --draft --banding
hp500 in.txt out.pdf --crease
```

| Option | Effect |
|---|---|
| `--aged-paper` / `--white-paper` | Toggle paper texture |
| `--ink-bleed` / `--no-ink-bleed` | Toggle Gaussian ink blur |
| `--jitter` | Add per-character position wobble |
| `--dot-variation` | Add subtle per-character ink color variation |
| `--banding` | Add draft-mode pass-line banding |
| `--crease` | Occasionally add a faint page crease |
| `--no-artifacts` | Compatibility shortcut for white paper, no blur, no optional artifacts |

### Searchable PDFs

Generated PDFs include an invisible text layer by default. The visible page remains the 300 DPI bitmap render, but PDF viewers can search and copy text from the printed character cells.

```bash
hp500 manual.txt manual.pdf
hp500 manual.txt image-only.pdf --no-text-layer
```

The text layer is recorded by the same renderer that draws the bitmap page. PCL and control codes do not get text cells; printable CP437 bytes do, after clipping, cursor movement, page breaks, and `--auto-margins` trimming have been applied. It is intended for search/copy, not as the visible document layout.

### Paper and pitch options

```bash
hp500 input.txt output.pdf --paper a4
hp500 input.txt output.pdf --paper legal
hp500 input.txt output.pdf --landscape
hp500 input.txt output.pdf --cpi 17        # compressed (17 chars/inch)
hp500 input.txt output.pdf --lpi 8         # tighter line spacing
```

### Margins

Margins can be adjusted from the command line in character cells and row heights:

```bash
hp500 input.txt output.pdf --left-margin-chars 3 --right-margin-chars 3
hp500 input.txt output.pdf --top-margin-rows 1 --bottom-margin-rows 1
```

For preformatted files that carry their own left padding, `--auto-margins` scans the full document before rendering. If every nonblank line starts three spaces in, it applies a three-character left margin, a three-character right margin, and trims those shared leading spaces while rendering so the output does not shift right twice.

```bash
hp500 report.txt report.pdf --auto-margins
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
  -o, --output-file  Output PDF path  [overrides positional output]
  --demo       Print the built-in demo document
  --paper       letter | a4 | legal | executive
  --landscape   Landscape orientation
  --draft       Draft quality mode
  --ideal       Ideal copy mode: pure black, white paper, zero jitter
  --white-paper  Use plain white paper
  --no-ink-bleed  Disable ink blur
  --jitter      Enable per-character position jitter
  --dot-variation  Enable subtle ink color variation
  --banding     Enable draft-mode pass-line banding
  --crease      Enable occasional page crease artifact
  --no-artifacts  Disable all paper/ink artifacts
  --left-margin-chars N
  --right-margin-chars N
  --top-margin-rows N
  --bottom-margin-rows N
  --auto-margins
  --no-text-layer
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
make run INPUT=myfile.txt EXTRA="--auto-margins --jitter"
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

At 10 CPI with 0.25 inch left/right margins on letter paper:

```
Page width    = 8.5"
Left margin   = 0.25"  →  right margin = 0.25"
Printable     = 8.0" × 10 CPI = 80 characters maximum per line
```

Lines longer than 80 characters are clipped at the right margin — the same behaviour as the real printer (characters past the margin hit the platen and don't print). There is no word wrap.

At 17 CPI (compressed): `8.0" × 17 = 136 characters` per line.

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
compose_page()      Composites ink onto paper
    │               Default: aged paper + Gaussian ink bleed
    │               Optional: jitter, dot variation, draft banding, page crease
    ▼
build_pdf()         Embeds each page as JPEG into a ReportLab PDF
                    Adds an invisible searchable text layer by default
                    Physical page dimensions set exactly in points (1/72 inch)
```

Resolution is fixed at **300 × 300 DPI**, the HP DeskJet 500's native print resolution.

---

## File layout

```
hp500_emulator.py   Main script — installed as the hp500 command
install.sh          Standalone installer (alternative to make install)
Makefile            Build, install, test, and render targets
README.md           This file
```

---

## Compatibility

| OS | Release | python3-pil | python3-reportlab | python3-numpy |
|---|---|---|---|---|
| Ubuntu flavors | 20.04 LTS Focal | 8.1.2 | 3.5.34 | 1.19.5 |
| Ubuntu flavors | 22.04 LTS Jammy | 9.0.1 | 3.6.8 | 1.21.5 |
| Ubuntu  | 24.04 LTS Noble | 10.2.x | 4.1.0 ¹ | 1.26.4 |
| Ubuntu  | 24.10 Oracular | ✓ | 4.2.2 ¹ | ✓ |
| Ubuntu  | 25.04 Plucky | ✓ | 4.3.1 ¹ | ✓ |
| Linux Mint | 21.x | same as Ubuntu 22.04 Jammy | same as Ubuntu 22.04 Jammy | same as Ubuntu 22.04 Jammy |
| Linux Mint | 22.x | same as Ubuntu 24.04 Noble | same as Ubuntu 24.04 Noble ¹ | same as Ubuntu 24.04 Noble |
| LMDE | 6 | same as Debian 12 Bookworm | same as Debian 12 Bookworm | same as Debian 12 Bookworm |

¹ In universe repository — enabled automatically by `make install` and `install.sh`.

Linux Mint reports `ID=linuxmint` in `/etc/os-release`; `install.sh` accepts that ID directly. Standard Linux Mint uses Ubuntu package bases, while LMDE uses Debian package bases, so the apt package names used by the build chain are unchanged.

Kubuntu, Xubuntu, Lubuntu, and other Ubuntu flavors use the same Ubuntu package repositories for these dependencies; only the desktop environment differs for this project. Ubuntu under WSL (Windows Subsystem for Linux) and other Linux distributions with compatible package managers should work as well. The script itself is vanilla Python — it will run on any interpreter that has access to the required modules, regardless of platform. However, the install subsystem expects a pseudo-standard modicum of Linux and package management to install cleanly.

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
