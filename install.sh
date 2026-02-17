#!/bin/bash
set -euo pipefail

# ============================================================================
# Entryway Installer
# Claude Code starter kit: settings, hooks, status line, notifications
# ============================================================================

# --- Colors (Rich-inspired palette) ---
readonly CYAN='\033[0;36m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[0;33m'
readonly RED='\033[0;31m'
readonly DIM='\033[2m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'

# --- Configuration ---
readonly REPO_URL="https://github.com/daviguides/entryway.git"
readonly INSTALL_DIR="$HOME/.local/share/entryway"
readonly CLAUDE_DIR="$HOME/.claude"
readonly SETTINGS_FILE="$CLAUDE_DIR/settings.json"
readonly VERSION="0.1.0"

# --- Box width (53 chars between borders) ---
readonly W=53

# --- UI Helpers ---
box_top() {
  printf "${CYAN}╭"
  printf '─%.0s' $(seq 1 $W)
  printf "╮${NC}\n"
}

box_bottom() {
  printf "${CYAN}╰"
  printf '─%.0s' $(seq 1 $W)
  printf "╯${NC}\n"
}

box_empty() {
  printf "${CYAN}│${NC}%${W}s${CYAN}│${NC}\n" ""
}

box_separator() {
  printf "${CYAN}│${DIM}"
  printf '─%.0s' $(seq 1 $W)
  printf "${NC}${CYAN}│${NC}\n"
}

box_text() {
  local text="$1"
  local len=${#text}
  local pad=$((W - 2 - len))
  printf "${CYAN}│${NC}  %s%${pad}s${CYAN}│${NC}\n" "$text" ""
}

status_line() {
  local icon="$1"
  local color="$2"
  local text="$3"
  local len=${#text}
  local pad=$((W - 4 - len))
  printf "${CYAN}│${NC}  ${color}%s${NC} %s%${pad}s${CYAN}│${NC}\n" "$icon" "$text" ""
}

status_ok() { status_line "✓" "$GREEN" "$1"; }
status_warn() { status_line "⚠" "$YELLOW" "$1"; }
status_error() { status_line "✗" "$RED" "$1"; }
status_info() { status_line "→" "$DIM" "$1"; }

spinner() {
  local pid=$1
  local msg="$2"
  local len=${#msg}
  local pad=$((W - 4 - len))
  local spin='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
  local i=0
  while kill -0 "$pid" 2>/dev/null; do
    printf "\r${CYAN}│${NC}  ${CYAN}%s${NC} %s%${pad}s${CYAN}│${NC}" "${spin:i++%10:1}" "$msg" ""
    sleep 0.1
  done
  printf "\r%*s\r" 60 ""
}

# --- Cleanup on error ---
cleanup_on_error() {
  if [ "${INSTALL_FAILED:-}" = "1" ] && [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
  fi
}
trap cleanup_on_error EXIT

# ============================================================================
# Functions
# ============================================================================

print_header() {
  printf "\n"
  box_top
  box_empty
  printf "${CYAN}│${NC}   ${BOLD}entryway${NC}   Claude Code Starter Kit                ${CYAN}│${NC}\n"
  printf "${CYAN}│${NC}              v${VERSION}                                 ${CYAN}│${NC}\n"
  box_empty
  box_separator
}

check_dependencies() {
  local missing=0

  if ! command -v gh >/dev/null 2>&1; then
    status_error "gh (GitHub CLI) is not installed"
    box_text "Install: https://cli.github.com"
    missing=1
  elif ! gh auth status >/dev/null 2>&1; then
    status_error "gh is not authenticated"
    box_text "Run: gh auth login"
    missing=1
  else
    status_ok "gh authenticated"
  fi

  if ! command -v git >/dev/null 2>&1; then
    status_error "git is not installed"
    box_text "Install: https://git-scm.com/downloads"
    missing=1
  else
    status_ok "git found"
  fi

  if ! command -v uv >/dev/null 2>&1; then
    status_error "uv is not installed"
    box_text "Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
    missing=1
  else
    status_ok "uv found"
  fi

  if [ "$missing" -eq 1 ]; then
    box_empty
    box_bottom
    printf "\n"
    exit 1
  fi
}

clone_repository() {
  if [ -d "$INSTALL_DIR" ]; then
    status_info "Updating existing installation..."
    git -C "$INSTALL_DIR" pull --quiet 2>/dev/null &
    local pid=$!
    spinner $pid "Pulling latest changes..."
    wait $pid || {
      status_warn "Pull failed, re-cloning..."
      rm -rf "$INSTALL_DIR"
      clone_fresh
      return
    }
    status_ok "Repository updated"
  else
    clone_fresh
  fi
}

clone_fresh() {
  INSTALL_FAILED=1
  mkdir -p "$(dirname "$INSTALL_DIR")"
  git clone --quiet "$REPO_URL" "$INSTALL_DIR" 2>/dev/null &
  local pid=$!
  spinner $pid "Cloning repository..."
  wait $pid || {
    status_error "Failed to clone repository"
    box_empty
    box_bottom
    printf "\n"
    exit 1
  }
  INSTALL_FAILED=0
  status_ok "Repository cloned"
}

validate_structure() {
  if [ ! -f "$INSTALL_DIR/pyproject.toml" ]; then
    status_error "Invalid repository structure"
    INSTALL_FAILED=1
    exit 1
  fi
}

install_tool() {
  uv tool install -e "$INSTALL_DIR" 2>/dev/null &
  local pid=$!
  spinner $pid "Installing entryway via uv tool..."
  wait $pid || {
    uv tool install --force -e "$INSTALL_DIR" 2>/dev/null &
    pid=$!
    spinner $pid "Reinstalling entryway..."
    wait $pid || {
      status_error "Failed to install entryway"
      box_empty
      box_bottom
      printf "\n"
      exit 1
    }
  }
  status_ok "CLIs installed (status_line, slash_command, ...)"
}

verify_install() {
  if command -v status_line >/dev/null 2>&1; then
    status_ok "status_line command available"
  else
    status_warn "CLIs not in PATH"
    box_text "Add to your shell profile:"
    box_text "  export PATH=\"\$HOME/.local/bin:\$PATH\""
  fi
}

make_scripts_executable() {
  chmod +x "$INSTALL_DIR/scripts/"*.sh 2>/dev/null || true
  status_ok "Scripts ready"
}

setup_settings() {
  mkdir -p "$CLAUDE_DIR"

  entryway-setup --template "$INSTALL_DIR/settings.json" >/dev/null 2>&1 &
  local pid=$!
  spinner $pid "Merging settings..."
  wait $pid || {
    status_warn "Settings merge failed, copying template"
    if [ -f "$SETTINGS_FILE" ]; then
      local backup="$SETTINGS_FILE.backup.$(date +%Y%m%d%H%M%S)"
      cp "$SETTINGS_FILE" "$backup"
      status_info "Backup: ${backup##*/}"
    fi
    cp "$INSTALL_DIR/settings.json" "$SETTINGS_FILE"
  }
  status_ok "Settings configured"
}

install_plugins() {
  box_empty
  box_separator
  printf "${CYAN}│${NC}  ${BOLD}Plugins${NC}                                            ${CYAN}│${NC}\n"
  box_separator

  # Get plugin list from entryway-setup (reads plugins.yaml + extras)
  local plugin_list
  plugin_list=$(entryway-setup --list-installers 2>/dev/null) || {
    status_warn "Could not read plugin list"
    return
  }

  # Check if extras were found (stderr message)
  if entryway-setup --list-installers 2>&1 >/dev/null | grep -q "#extra:"; then
    status_info "Extra plugins detected"
  fi

  # Install each plugin via gh api (works for private and public repos)
  while IFS='|' read -r name repo; do
    [ -z "$name" ] && continue
    bash -c "$(gh api "repos/${repo}/contents/install.sh" --jq '.content' | base64 -d)" >/dev/null 2>&1 &
    local pid=$!
    spinner $pid "Installing ${name}..."
    wait $pid && status_ok "${name} installed" || status_warn "${name}: install manually"
  done <<< "$plugin_list"
}

print_complete() {
  box_empty
  box_separator
  printf "${CYAN}│${NC}  ${GREEN}${BOLD}Installation Complete${NC}                              ${CYAN}│${NC}\n"
  box_separator
  box_empty
  printf "${CYAN}│${NC}  ${BOLD}What was installed${NC}                                 ${CYAN}│${NC}\n"
  box_text "Settings    ~/.claude/settings.json"
  box_text "CLIs        status_line, slash_command,"
  box_text "            claude_notifier"
  box_text "Plugins     arche, zazen, shodo"
  box_text "Hooks       session-start, notifications,"
  box_text "            slash command dedup"
  box_empty
  printf "${CYAN}│${NC}  ${BOLD}Test${NC}                                               ${CYAN}│${NC}\n"
  box_text "status_line --echo    # Test status line"
  box_text "claude_notifier -e Stop -d  # Test notifier"
  box_empty
  printf "${CYAN}│${NC}  ${BOLD}Update${NC}                                             ${CYAN}│${NC}\n"
  box_text "Re-run this installer or:"
  box_text "cd ~/.local/share/entryway && git pull"
  box_empty
  box_bottom
  printf "\n"
}

# ============================================================================
# Main
# ============================================================================

main() {
  print_header
  check_dependencies
  clone_repository
  validate_structure
  install_tool
  verify_install
  make_scripts_executable
  setup_settings
  install_plugins
  print_complete
}

main
