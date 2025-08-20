#!/bin/bash
# =========================================================================
# Context Update Script - Maintains project state documentation
# Run this after major changes to update context for future sessions
# =========================================================================

set -e

PROJECT_DIR="$(pwd)"
CONTEXT_FILE="$PROJECT_DIR/PROJECT_CONTEXT.md"
CLAUDE_FILE="$PROJECT_DIR/CLAUDE.md"
DATE=$(date '+%Y-%m-%d %H:%M')

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[UPDATE]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Update PROJECT_CONTEXT.md with current status
update_project_context() {
    log "Updating PROJECT_CONTEXT.md with current status..."
    
    # Get current checkpoint status
    local local_checkpoints=""
    local server_checkpoints=""
    
    if [ -d "./checkpoints" ]; then
        local_checkpoints=$(find ./checkpoints -maxdepth 1 -type d -name "*" ! -name "checkpoints" | wc -l | tr -d ' ')
    fi
    
    if command -v ssh >/dev/null 2>&1; then
        server_checkpoints=$(ssh one-climate@192.168.20.10 "find ~/project_vm_daily_report_2/checkpoints -maxdepth 1 -type d -name '*' ! -name 'checkpoints' 2>/dev/null | wc -l" 2>/dev/null || echo "0")
    fi
    
    # Get latest checkpoint
    local latest_checkpoint="unknown"
    if [ -f "./checkpoints/checkpoint_index.txt" ]; then
        latest_checkpoint=$(tail -1 ./checkpoints/checkpoint_index.txt | cut -d'|' -f2 | tr -d ' ' 2>/dev/null || echo "unknown")
    fi
    
    # Update timestamp in context file
    if [ -f "$CONTEXT_FILE" ]; then
        sed -i.bak "s/\*Last Updated: .*\*/\*Last Updated: $DATE\*/" "$CONTEXT_FILE"
        sed -i.bak "s/- \*\*Local Checkpoints\*\*: .* total/- **Local Checkpoints**: $local_checkpoints total/" "$CONTEXT_FILE"
        sed -i.bak "s/- \*\*Server Checkpoints\*\*: .* total/- **Server Checkpoints**: $server_checkpoints total/" "$CONTEXT_FILE"
        sed -i.bak "s/- \*\*Latest\*\*: .*/- **Latest**: $latest_checkpoint/" "$CONTEXT_FILE"
        rm -f "$CONTEXT_FILE.bak"
    fi
}

# Update CLAUDE.md with recent changes
update_claude_context() {
    log "Updating CLAUDE.md..."
    
    if [ -f "$CLAUDE_FILE" ]; then
        # Update date in recent changes section
        sed -i.bak "s/## 🔧 Recent Major Changes (Last Session)/## 🔧 Recent Major Changes (Updated: $DATE)/" "$CLAUDE_FILE"
        rm -f "$CLAUDE_FILE.bak"
    fi
}

# Add new change to context (if provided)
add_change_to_context() {
    local change="$1"
    if [ -n "$change" ]; then
        log "Adding change to context: $change"
        
        # Add to PROJECT_CONTEXT.md recent achievements
        if [ -f "$CONTEXT_FILE" ]; then
            sed -i.bak "/## 🚀 Recent Achievements/a\\
- [$(date '+%Y-%m-%d')] $change" "$CONTEXT_FILE"
            rm -f "$CONTEXT_FILE.bak"
        fi
        
        # Add to CLAUDE.md recent changes
        if [ -f "$CLAUDE_FILE" ]; then
            sed -i.bak "/## 🔧 Recent Major Changes/a\\
- ✅ **$(date '+%m-%d')**: $change" "$CLAUDE_FILE"
            rm -f "$CLAUDE_FILE.bak"
        fi
    fi
}

# Sync context files to server
sync_context_to_server() {
    log "Syncing context files to server..."
    
    if command -v scp >/dev/null 2>&1; then
        scp "$CONTEXT_FILE" "$CLAUDE_FILE" one-climate@192.168.20.10:~/project_vm_daily_report_2/ 2>/dev/null && \
        success "✅ Context files synced to server" || \
        echo "⚠️ Could not sync to server (manual sync may be needed)"
    fi
}

# Generate quick status report
generate_status_report() {
    log "Generating current status report..."
    
    cat << EOF

📊 Current Project Status Report
================================
Updated: $DATE

📂 Checkpoints:
   Local: $local_checkpoints | Server: $server_checkpoints
   Latest: $latest_checkpoint

🔧 Key Scripts:
$(ls -1 *.sh 2>/dev/null | head -5 | sed 's/^/   /')

📝 Recent Files:
$(ls -lt | head -5 | tail -4 | awk '{print "   " $9 " (" $6 " " $7 ")"}')

🚀 System Health:
$(python3 -c "print('   ✅ Python ready')" 2>/dev/null || echo "   ❌ Python issues")
$([ -f ".env" ] && echo "   ✅ Configuration ready" || echo "   ❌ .env missing")
$([ -d "checkpoints" ] && echo "   ✅ Checkpoints ready" || echo "   ❌ Checkpoints missing")

EOF
}

# Help function
show_help() {
    cat << 'EOF'
Context Update Script
====================

Usage: ./update_context.sh [options] ["change description"]

Options:
  --sync-only    - Only sync existing context to server
  --status       - Show current status report
  --help         - Show this help

Examples:
  ./update_context.sh "Added new feature X"
  ./update_context.sh --status
  ./update_context.sh --sync-only

This script maintains project documentation for context continuity
across Claude Code sessions.

EOF
}

# Main function
main() {
    case "$1" in
        "--sync-only")
            sync_context_to_server
            ;;
        "--status")
            generate_status_report
            ;;
        "--help"|"-h")
            show_help
            ;;
        "")
            # Standard update
            update_project_context
            update_claude_context
            sync_context_to_server
            success "✅ Context updated successfully"
            ;;
        *)
            # Update with change description
            update_project_context
            update_claude_context
            add_change_to_context "$1"
            sync_context_to_server
            success "✅ Context updated with: $1"
            ;;
    esac
}

# Run main function
main "$@"