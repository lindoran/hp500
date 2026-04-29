# =============================================================================
# Makefile — HP DeskJet 500 Print Emulator
# =============================================================================
#
# Targets:
#   make install      Install apt dependencies + install hp500 command to PATH
#   make uninstall    Remove hp500 from PATH
#   make demo         Render built-in demo in NLQ, Draft, and Ideal modes
#   make run          Render INPUT file  (e.g. make run INPUT=myfile.txt)
#   make test         Verify imports, fonts, and render all three modes
#   make check        Verify dependencies only (no install, no rendering)
#   make clean        Remove generated PDF files
#   make help         Show this message
#
# Variables (override on the command line):
#   INSTALL_DIR=/usr/local/bin    Where to install the hp500 command
#   PAPER=letter                  Paper size: letter | a4 | legal | executive
#   CPI=10                        Characters per inch
#   LPI=6                         Lines per inch
#   INPUT=                        Input file (omit to use built-in demo)
#   OUTPUT=output.pdf             Output PDF path
#   EXTRA=                        Additional hp500 flags
#
# Examples:
#   make run INPUT=invoice.txt
#   make run INPUT=form.txt OUTPUT=form.pdf
#   make run-ideal INPUT=manual.txt OUTPUT=manual.pdf
#   make demo PAPER=a4
#   make install INSTALL_DIR=~/.local/bin
# =============================================================================

SCRIPT      := hp500_emulator.py
CMD         := hp500
INSTALL_DIR := /usr/local/bin
INSTALL_CMD := $(INSTALL_DIR)/$(CMD)

PAPER   := letter
CPI     := 10
LPI     := 6
INPUT   :=
OUTPUT  := output.pdf

# ── Colours ──────────────────────────────────────────────────────────────────
BOLD    := \033[1m
GREEN   := \033[0;32m
CYAN    := \033[0;36m
YELLOW  := \033[1;33m
RESET   := \033[0m

ok   = @printf "$(GREEN)[OK]$(RESET)    %s\n" "$(1)"
info = @printf "$(CYAN)[INFO]$(RESET)  %s\n" "$(1)"
warn = @printf "$(YELLOW)[WARN]$(RESET)  %s\n" "$(1)"

# ── Default target ────────────────────────────────────────────────────────────
.DEFAULT_GOAL := help

.PHONY: help
help:
	@printf "\n$(BOLD)HP DeskJet 500 Print Emulator$(RESET)\n"
	@printf "==============================\n\n"
	@printf "  $(BOLD)make install$(RESET)               Install dependencies + hp500 command\n"
	@printf "  $(BOLD)make uninstall$(RESET)             Remove $(INSTALL_CMD)\n"
	@printf "  $(BOLD)make demo$(RESET)                  Render built-in demo (NLQ + Draft + Ideal)\n"
	@printf "  $(BOLD)make run$(RESET) INPUT=file.txt    Render a file in NLQ mode\n"
	@printf "  $(BOLD)make run-draft$(RESET) INPUT=...   Render in Draft mode\n"
	@printf "  $(BOLD)make run-ideal$(RESET) INPUT=...   Render in Ideal (flat) mode\n"
	@printf "  $(BOLD)make test$(RESET)                  Full dependency + render test\n"
	@printf "  $(BOLD)make check$(RESET)                 Verify imports and fonts only\n"
	@printf "  $(BOLD)make clean$(RESET)                 Remove generated PDFs\n\n"
	@printf "  Defaults: PAPER=$(PAPER)  CPI=$(CPI)  LPI=$(LPI)  OUTPUT=$(OUTPUT)\n"
	@printf "            INSTALL_DIR=$(INSTALL_DIR)\n\n"

# ── Prerequisite: apt must exist ─────────────────────────────────────────────
.PHONY: _require_apt
_require_apt:
	@command -v apt-get >/dev/null 2>&1 || \
		{ printf "$(YELLOW)[WARN]$(RESET)  apt-get not found — manual install required.\n"; exit 1; }

# ── Install ───────────────────────────────────────────────────────────────────
.PHONY: install
install: _require_apt _install_packages _install_cmd

.PHONY: _install_packages
_install_packages:
	@printf "\n$(BOLD)Installing system packages...$(RESET)\n"
	@printf "$(CYAN)──────────────────────────────────────$(RESET)\n"
	sudo apt-get update -qq
	@if ! apt-cache show python3-reportlab >/dev/null 2>&1; then \
	    printf "$(CYAN)[INFO]$(RESET)  Enabling universe repository...\n"; \
	    sudo add-apt-repository -y universe; \
	    sudo apt-get update -qq; \
	fi
	sudo apt-get install -y \
	    python3 \
	    python3-pil \
	    python3-reportlab \
	    python3-numpy \
	    fonts-dejavu-mono
	$(call ok,Packages installed)

.PHONY: _install_cmd
_install_cmd:
	@printf "\n$(BOLD)Installing hp500 command to $(INSTALL_DIR)...$(RESET)\n"
	@printf "$(CYAN)──────────────────────────────────────$(RESET)\n"
	@if [ -w "$(INSTALL_DIR)" ] || mkdir -p "$(INSTALL_DIR)" 2>/dev/null; then \
	    install -Dm755 $(SCRIPT) $(INSTALL_CMD); \
	else \
	    sudo install -Dm755 $(SCRIPT) $(INSTALL_CMD); \
	fi
	$(call ok,Installed: $(INSTALL_CMD))
	@printf "\n  You can now run:\n"
	@printf "    $(BOLD)hp500 input.txt output.pdf$(RESET)\n"
	@printf "    $(BOLD)hp500 input.txt output.pdf --draft$(RESET)\n"
	@printf "    $(BOLD)hp500 input.txt output.pdf --ideal$(RESET)\n"
	@printf "    $(BOLD)hp500 --help$(RESET)\n\n"

# ── Uninstall ─────────────────────────────────────────────────────────────────
.PHONY: uninstall
uninstall:
	@if [ -f "$(INSTALL_CMD)" ]; then \
	    sudo rm -v "$(INSTALL_CMD)"; \
	    printf "$(GREEN)[OK]$(RESET)    Removed $(INSTALL_CMD)\n"; \
	else \
	    printf "$(CYAN)[INFO]$(RESET)  $(INSTALL_CMD) not found, nothing to remove.\n"; \
	fi

# ── Check imports + fonts (no install) ───────────────────────────────────────
.PHONY: check
check:
	@printf "\n$(BOLD)Python imports$(RESET)\n"
	@printf "$(CYAN)──────────────────────────────────────$(RESET)\n"
	@python3 -c "import PIL;       print('  PIL       ', PIL.__version__)"
	@python3 -c "import reportlab; print('  reportlab ', reportlab.Version)"
	@python3 -c "import numpy;     print('  numpy     ', numpy.__version__)"
	$(call ok,All imports OK)
	@printf "\n$(BOLD)Font files$(RESET)\n"
	@printf "$(CYAN)──────────────────────────────────────$(RESET)\n"
	@for f in \
	    DejaVuSansMono.ttf \
	    DejaVuSansMono-Bold.ttf \
	    DejaVuSansMono-Oblique.ttf \
	    DejaVuSansMono-BoldOblique.ttf; do \
	    p="/usr/share/fonts/truetype/dejavu/$$f"; \
	    if [ -f "$$p" ]; then \
	        printf "  $(GREEN)✓$(RESET)  $$f\n"; \
	    else \
	        printf "  $(YELLOW)~$(RESET)  $$f  (Liberation Mono fallback)\n"; \
	    fi; \
	done
	@printf "\n"

# ── Render targets ────────────────────────────────────────────────────────────
_FLAGS = --paper $(PAPER) --cpi $(CPI) --lpi $(LPI) $(EXTRA)

.PHONY: run
run:
	$(call info,Rendering NLQ → $(OUTPUT))
	@python3 $(SCRIPT) $(INPUT) $(OUTPUT) $(_FLAGS)
	$(call ok,Written: $(OUTPUT))

.PHONY: run-draft
run-draft:
	$(call info,Rendering Draft → $(OUTPUT))
	@python3 $(SCRIPT) $(INPUT) $(OUTPUT) $(_FLAGS) --draft
	$(call ok,Written: $(OUTPUT))

.PHONY: run-ideal
run-ideal:
	$(call info,Rendering Ideal → $(OUTPUT))
	@python3 $(SCRIPT) $(INPUT) $(OUTPUT) $(_FLAGS) --ideal
	$(call ok,Written: $(OUTPUT))

# ── Demo: all three modes ─────────────────────────────────────────────────────
.PHONY: demo
demo: demo_nlq.pdf demo_draft.pdf demo_ideal.pdf
	@printf "\n$(BOLD)Demo output$(RESET)\n"
	@printf "$(CYAN)──────────────────────────────────────$(RESET)\n"
	@ls -lh demo_nlq.pdf demo_draft.pdf demo_ideal.pdf
	@printf "\n"

demo_nlq.pdf: $(SCRIPT)
	$(call info,NLQ   → $@)
	@python3 $(SCRIPT) --demo -o $@ $(_FLAGS)

demo_draft.pdf: $(SCRIPT)
	$(call info,Draft → $@)
	@python3 $(SCRIPT) --demo -o $@ $(_FLAGS) --draft

demo_ideal.pdf: $(SCRIPT)
	$(call info,Ideal → $@)
	@python3 $(SCRIPT) --demo -o $@ $(_FLAGS) --ideal

# ── Test ──────────────────────────────────────────────────────────────────────
.PHONY: test
test: check demo
	@printf "$(BOLD)Verifying output files$(RESET)\n"
	@printf "$(CYAN)──────────────────────────────────────$(RESET)\n"
	@fail=0; \
	for f in demo_nlq.pdf demo_draft.pdf demo_ideal.pdf; do \
	    if [ -f "$$f" ] && [ -s "$$f" ]; then \
	        size=$$(du -h "$$f" | cut -f1); \
	        printf "  $(GREEN)✓$(RESET)  $$f  ($$size)\n"; \
	    else \
	        printf "  $(YELLOW)✗$(RESET)  $$f  MISSING or empty\n"; \
	        fail=1; \
	    fi; \
	done; \
	[ $$fail -eq 0 ] || exit 1
	@printf "\n"
	$(call ok,All tests passed)
	@printf "\n"

# ── Clean ─────────────────────────────────────────────────────────────────────
.PHONY: clean
clean:
	$(call info,Removing generated PDFs...)
	@rm -fv demo_nlq.pdf demo_draft.pdf demo_ideal.pdf output.pdf 2>/dev/null || true
	$(call ok,Clean)
