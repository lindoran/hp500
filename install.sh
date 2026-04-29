#!/usr/bin/env bash
# =============================================================================
# install.sh — HP DeskJet 500 Emulator dependency installer
# Supports Ubuntu / Xubuntu / Debian-based systems (all LTS and non-LTS)
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${1:-/usr/local/bin}"

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
ok()      { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*" >&2; }
section() { echo -e "\n${BOLD}$*${RESET}"; echo "$(printf '─%.0s' {1..60})"; }

# ── Root check ────────────────────────────────────────────────────────────────
need_sudo() {
    if [[ $EUID -ne 0 ]]; then
        if command -v sudo &>/dev/null; then
            SUDO="sudo"
        else
            error "This script needs root privileges. Run as root or install sudo."
            exit 1
        fi
    else
        SUDO=""
    fi
}

# ── Distro detection ─────────────────────────────────────────────────────────
detect_distro() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        DISTRO_ID="${ID}"
        DISTRO_NAME="${PRETTY_NAME}"
        DISTRO_VERSION="${VERSION_ID:-unknown}"
        DISTRO_CODENAME="${VERSION_CODENAME:-unknown}"
    else
        error "Cannot detect OS. /etc/os-release not found."
        exit 1
    fi

    case "${DISTRO_ID}" in
        ubuntu|debian|linuxmint|xubuntu|kubuntu|lubuntu|pop|elementary)
            PKG_MANAGER="apt"
            ;;
        *)
            error "Unsupported distro: ${DISTRO_ID}"
            error "This installer supports Ubuntu, Xubuntu, Debian, and derivatives."
            exit 1
            ;;
    esac
}

# ── Universe repo (needed on Ubuntu 24.04+ for python3-reportlab) ─────────────
enable_universe() {
    if [[ "${DISTRO_ID}" == "ubuntu" ]] || \
       [[ "${DISTRO_ID}" == "xubuntu" ]] || \
       [[ "${DISTRO_ID}" =~ ^(kubuntu|lubuntu)$ ]]; then

        # Check if universe is already enabled
        if apt-cache policy 2>/dev/null | grep -q "ubuntu.*/universe"; then
            info "Universe repository already enabled."
        else
            info "Enabling universe repository..."
            $SUDO add-apt-repository -y universe
            NEED_UPDATE=1
        fi
    fi
}

# ── Package installation ──────────────────────────────────────────────────────
PACKAGES=(
    python3
    python3-pil
    python3-reportlab
    python3-numpy
    fonts-dejavu-mono
)

install_packages() {
    section "Installing system packages"

    info "Updating package lists..."
    $SUDO apt-get update -qq

    info "Installing: ${PACKAGES[*]}"
    $SUDO apt-get install -y "${PACKAGES[@]}"

    ok "All packages installed."
}

# ── Verify Python imports ────────────────────────────────────────────────────
verify_imports() {
    section "Verifying Python imports"

    local failed=0
    for mod in PIL reportlab numpy; do
        if python3 -c "import ${mod}" 2>/dev/null; then
            VER=$(python3 -c "import ${mod}; print(getattr(${mod},'__version__','ok'))" 2>/dev/null)
            ok "${mod} ${VER}"
        else
            error "${mod} import failed"
            failed=1
        fi
    done

    # Check font files exist
    FONT_PATHS=(
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Oblique.ttf"
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-BoldOblique.ttf"
    )
    for f in "${FONT_PATHS[@]}"; do
        if [[ -f "$f" ]]; then
            ok "Font: $(basename "$f")"
        else
            warn "Missing font: $f  (Liberation Mono fallback will be used)"
        fi
    done

    if [[ $failed -ne 0 ]]; then
        error "One or more imports failed. Check the output above."
        exit 1
    fi
}

# ── Optional: install emulator to PATH ───────────────────────────────────────
install_script() {
    section "Installing hp500_emulator to ${INSTALL_DIR}"

    if [[ ! -f "${SCRIPT_DIR}/hp500_emulator.py" ]]; then
        warn "hp500_emulator.py not found in ${SCRIPT_DIR} — skipping PATH install."
        return
    fi

    $SUDO install -Dm755 "${SCRIPT_DIR}/hp500_emulator.py" \
        "${INSTALL_DIR}/hp500_emulator"

    ok "Installed to ${INSTALL_DIR}/hp500_emulator"
    info "Run with:  hp500_emulator input.txt output.pdf"
}

# ── Main ─────────────────────────────────────────────────────────────────────
main() {
    echo -e "${BOLD}"
    echo "  HP DeskJet 500 Emulator — Installer"
    echo "  ===================================="
    echo -e "${RESET}"

    detect_distro
    info "Detected: ${DISTRO_NAME} (${DISTRO_CODENAME})"

    need_sudo
    enable_universe
    install_packages
    verify_imports
    install_script

    section "Done"
    ok "Installation complete."
    echo
    echo -e "  ${CYAN}Usage:${RESET}"
    echo "    python3 hp500_emulator.py input.txt output.pdf"
    echo "    python3 hp500_emulator.py input.txt output.pdf --draft"
    echo "    python3 hp500_emulator.py input.txt output.pdf --ideal"
    echo "    python3 hp500_emulator.py input.txt output.pdf --paper a4"
    echo "    python3 hp500_emulator.py             # prints built-in demo"
    echo
}

main "$@"
