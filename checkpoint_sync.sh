#!/bin/bash
# =========================================================================
# Checkpoint Auto-Sync System
# Automatically synchronizes checkpoints between local and remote server
# =========================================================================

set -e

# Configuration
LOCAL_PROJECT_DIR="/Users/teerayutyeerahem/project_vm_daily_report_2"
REMOTE_HOST="one-climate@192.168.20.10"
REMOTE_PROJECT_DIR="~/project_vm_daily_report_2"
SYNC_LOG="$LOCAL_PROJECT_DIR/logs/checkpoint_sync.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$SYNC_LOG"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    echo "[SUCCESS] $1" >> "$SYNC_LOG"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "[ERROR] $1" >> "$SYNC_LOG"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "[WARNING] $1" >> "$SYNC_LOG"
}

# Ensure log directory exists
mkdir -p "$(dirname "$SYNC_LOG")"

# Test SSH connection
test_ssh_connection() {
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$REMOTE_HOST" "echo 'SSH connection successful'" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Get checkpoint list from local
get_local_checkpoints() {
    if [ -d "$LOCAL_PROJECT_DIR/checkpoints" ]; then
        find "$LOCAL_PROJECT_DIR/checkpoints" -maxdepth 1 -type d -name "*" ! -name "checkpoints" -exec basename {} \; 2>/dev/null | sort
    fi
}

# Get checkpoint list from remote
get_remote_checkpoints() {
    if test_ssh_connection; then
        ssh "$REMOTE_HOST" "
            if [ -d \"$REMOTE_PROJECT_DIR/checkpoints\" ]; then
                find \"$REMOTE_PROJECT_DIR/checkpoints\" -maxdepth 1 -type d -name \"*\" ! -name \"checkpoints\" -exec basename {} \; 2>/dev/null | sort
            fi
        " 2>/dev/null || echo ""
    fi
}

# Compare checkpoint timestamps
get_checkpoint_timestamp() {
    local location="$1"  # "local" or "remote"
    local checkpoint="$2"
    
    if [ "$location" = "local" ]; then
        if [ -f "$LOCAL_PROJECT_DIR/checkpoints/$checkpoint/checkpoint_info.json" ]; then
            grep '"created_at"' "$LOCAL_PROJECT_DIR/checkpoints/$checkpoint/checkpoint_info.json" | sed 's/.*"created_at": "\([^"]*\)".*/\1/' 2>/dev/null || echo "1970-01-01T00:00:00"
        else
            echo "1970-01-01T00:00:00"
        fi
    else
        ssh "$REMOTE_HOST" "
            if [ -f \"$REMOTE_PROJECT_DIR/checkpoints/$checkpoint/checkpoint_info.json\" ]; then
                grep '\"created_at\"' \"$REMOTE_PROJECT_DIR/checkpoints/$checkpoint/checkpoint_info.json\" | sed 's/.*\"created_at\": \"\([^\"]*\)\".*/\1/' 2>/dev/null || echo \"1970-01-01T00:00:00\"
            else
                echo \"1970-01-01T00:00:00\"
            fi
        " 2>/dev/null || echo "1970-01-01T00:00:00"
    fi
}

# Sync checkpoint from local to remote
sync_local_to_remote() {
    local checkpoint="$1"
    log "📤 Syncing checkpoint '$checkpoint' from local to remote..."
    
    # Create remote checkpoint directory
    ssh "$REMOTE_HOST" "mkdir -p \"$REMOTE_PROJECT_DIR/checkpoints/$checkpoint\""
    
    # Sync checkpoint data
    rsync -avz --progress \
        "$LOCAL_PROJECT_DIR/checkpoints/$checkpoint/" \
        "$REMOTE_HOST:$REMOTE_PROJECT_DIR/checkpoints/$checkpoint/" \
        >> "$SYNC_LOG" 2>&1
    
    if [ $? -eq 0 ]; then
        success "✅ Checkpoint '$checkpoint' synced to remote"
        return 0
    else
        error "❌ Failed to sync checkpoint '$checkpoint' to remote"
        return 1
    fi
}

# Sync checkpoint from remote to local
sync_remote_to_local() {
    local checkpoint="$1"
    log "📥 Syncing checkpoint '$checkpoint' from remote to local..."
    
    # Create local checkpoint directory
    mkdir -p "$LOCAL_PROJECT_DIR/checkpoints/$checkpoint"
    
    # Sync checkpoint data
    rsync -avz --progress \
        "$REMOTE_HOST:$REMOTE_PROJECT_DIR/checkpoints/$checkpoint/" \
        "$LOCAL_PROJECT_DIR/checkpoints/$checkpoint/" \
        >> "$SYNC_LOG" 2>&1
    
    if [ $? -eq 0 ]; then
        success "✅ Checkpoint '$checkpoint' synced from remote"
        return 0
    else
        error "❌ Failed to sync checkpoint '$checkpoint' from remote"
        return 1
    fi
}

# Sync checkpoint index files
sync_checkpoint_index() {
    log "📋 Syncing checkpoint index files..."
    
    # Get newer index file
    local local_index="$LOCAL_PROJECT_DIR/checkpoints/checkpoint_index.txt"
    local local_time=0
    local remote_time=0
    
    if [ -f "$local_index" ]; then
        local_time=$(stat -f %m "$local_index" 2>/dev/null || echo 0)
    fi
    
    remote_time=$(ssh "$REMOTE_HOST" "
        if [ -f \"$REMOTE_PROJECT_DIR/checkpoints/checkpoint_index.txt\" ]; then
            stat -c %Y \"$REMOTE_PROJECT_DIR/checkpoints/checkpoint_index.txt\" 2>/dev/null || echo 0
        else
            echo 0
        fi
    " 2>/dev/null || echo 0)
    
    if [ "$local_time" -gt "$remote_time" ]; then
        log "📤 Local index is newer, syncing to remote..."
        rsync -avz "$local_index" "$REMOTE_HOST:$REMOTE_PROJECT_DIR/checkpoints/" >> "$SYNC_LOG" 2>&1
    elif [ "$remote_time" -gt "$local_time" ]; then
        log "📥 Remote index is newer, syncing to local..."
        rsync -avz "$REMOTE_HOST:$REMOTE_PROJECT_DIR/checkpoints/checkpoint_index.txt" "$LOCAL_PROJECT_DIR/checkpoints/" >> "$SYNC_LOG" 2>&1
    else
        log "📋 Index files are in sync"
    fi
}

# Main sync function
auto_sync_checkpoints() {
    log "🔄 Starting automatic checkpoint synchronization..."
    
    if ! test_ssh_connection; then
        error "❌ SSH connection failed - cannot sync checkpoints"
        return 1
    fi
    
    success "✅ SSH connection established"
    
    # Get checkpoint lists
    local local_checkpoints=$(get_local_checkpoints)
    local remote_checkpoints=$(get_remote_checkpoints)
    
    # Create arrays for processing
    local all_checkpoints=$(echo -e "$local_checkpoints\n$remote_checkpoints" | sort -u | grep -v '^$')
    
    local synced_count=0
    local skipped_count=0
    
    for checkpoint in $all_checkpoints; do
        if [ -z "$checkpoint" ]; then
            continue
        fi
        
        local has_local=$(echo "$local_checkpoints" | grep -x "$checkpoint" >/dev/null && echo "yes" || echo "no")
        local has_remote=$(echo "$remote_checkpoints" | grep -x "$checkpoint" >/dev/null && echo "yes" || echo "no")
        
        if [ "$has_local" = "yes" ] && [ "$has_remote" = "no" ]; then
            # Exists only locally - sync to remote
            if sync_local_to_remote "$checkpoint"; then
                synced_count=$((synced_count + 1))
            fi
        elif [ "$has_local" = "no" ] && [ "$has_remote" = "yes" ]; then
            # Exists only remotely - sync to local
            if sync_remote_to_local "$checkpoint"; then
                synced_count=$((synced_count + 1))
            fi
        elif [ "$has_local" = "yes" ] && [ "$has_remote" = "yes" ]; then
            # Exists on both - compare timestamps
            local local_timestamp=$(get_checkpoint_timestamp "local" "$checkpoint")
            local remote_timestamp=$(get_checkpoint_timestamp "remote" "$checkpoint")
            
            # Convert to epoch for comparison
            local local_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${local_timestamp%+*}" "+%s" 2>/dev/null || echo 0)
            local remote_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${remote_timestamp%+*}" "+%s" 2>/dev/null || echo 0)
            
            if [ "$local_epoch" -gt "$remote_epoch" ]; then
                log "📤 Local '$checkpoint' is newer ($local_timestamp vs $remote_timestamp)"
                if sync_local_to_remote "$checkpoint"; then
                    synced_count=$((synced_count + 1))
                fi
            elif [ "$remote_epoch" -gt "$local_epoch" ]; then
                log "📥 Remote '$checkpoint' is newer ($remote_timestamp vs $local_timestamp)"
                if sync_remote_to_local "$checkpoint"; then
                    synced_count=$((synced_count + 1))
                fi
            else
                log "✅ Checkpoint '$checkpoint' is in sync"
                skipped_count=$((skipped_count + 1))
            fi
        fi
    done
    
    # Sync index files
    sync_checkpoint_index
    
    success "🎉 Checkpoint synchronization completed!"
    log "📊 Summary: $synced_count synced, $skipped_count already in sync"
    
    return 0
}

# Force sync all from local to remote
force_sync_to_remote() {
    log "🚀 Force syncing all checkpoints from local to remote..."
    
    if ! test_ssh_connection; then
        error "❌ SSH connection failed"
        return 1
    fi
    
    local local_checkpoints=$(get_local_checkpoints)
    local synced_count=0
    
    for checkpoint in $local_checkpoints; do
        if [ -n "$checkpoint" ]; then
            if sync_local_to_remote "$checkpoint"; then
                synced_count=$((synced_count + 1))
            fi
        fi
    done
    
    sync_checkpoint_index
    success "🎉 Force sync completed! $synced_count checkpoints synced"
}

# Force sync all from remote to local
force_sync_to_local() {
    log "🚀 Force syncing all checkpoints from remote to local..."
    
    if ! test_ssh_connection; then
        error "❌ SSH connection failed"
        return 1
    fi
    
    local remote_checkpoints=$(get_remote_checkpoints)
    local synced_count=0
    
    for checkpoint in $remote_checkpoints; do
        if [ -n "$checkpoint" ]; then
            if sync_remote_to_local "$checkpoint"; then
                synced_count=$((synced_count + 1))
            fi
        fi
    done
    
    sync_checkpoint_index
    success "🎉 Force sync completed! $synced_count checkpoints synced"
}

# Show sync status
show_sync_status() {
    echo -e "${CYAN}📊 Checkpoint Sync Status${NC}"
    echo -e "${CYAN}=========================${NC}"
    
    if ! test_ssh_connection; then
        error "❌ SSH connection failed - cannot show remote status"
        return 1
    fi
    
    local local_checkpoints=$(get_local_checkpoints)
    local remote_checkpoints=$(get_remote_checkpoints)
    
    echo ""
    echo -e "${BLUE}Local Checkpoints:${NC}"
    if [ -n "$local_checkpoints" ]; then
        echo "$local_checkpoints" | while read checkpoint; do
            if [ -n "$checkpoint" ]; then
                local timestamp=$(get_checkpoint_timestamp "local" "$checkpoint")
                echo "  📂 $checkpoint ($timestamp)"
            fi
        done
    else
        echo "  (no checkpoints)"
    fi
    
    echo ""
    echo -e "${BLUE}Remote Checkpoints:${NC}"
    if [ -n "$remote_checkpoints" ]; then
        echo "$remote_checkpoints" | while read checkpoint; do
            if [ -n "$checkpoint" ]; then
                local timestamp=$(get_checkpoint_timestamp "remote" "$checkpoint")
                echo "  📂 $checkpoint ($timestamp)"
            fi
        done
    else
        echo "  (no checkpoints)"
    fi
    
    echo ""
    local total_local=$(echo "$local_checkpoints" | wc -w)
    local total_remote=$(echo "$remote_checkpoints" | wc -w)
    echo -e "${GREEN}Summary: Local=$total_local, Remote=$total_remote${NC}"
}

# Help function
show_help() {
    cat << 'EOF'
Checkpoint Auto-Sync System
===========================

Usage: ./checkpoint_sync.sh [command]

Commands:
  auto      - Auto-sync checkpoints (smart sync based on timestamps)
  status    - Show sync status between local and remote
  to-remote - Force sync all local checkpoints to remote
  to-local  - Force sync all remote checkpoints to local
  help      - Show this help

Examples:
  ./checkpoint_sync.sh auto         # Smart auto-sync
  ./checkpoint_sync.sh status       # Check status
  ./checkpoint_sync.sh to-remote    # Force push all to server
  ./checkpoint_sync.sh to-local     # Force pull all from server

Auto-sync logic:
- New checkpoints are synced to the missing location
- Existing checkpoints are compared by timestamp
- Newer checkpoints overwrite older ones
- Index files are automatically synced

Configuration:
- Local:  /Users/teerayutyeerahem/project_vm_daily_report_2
- Remote: one-climate@192.168.20.10:~/project_vm_daily_report_2
- Logs:   logs/checkpoint_sync.log

EOF
}

# Main function
main() {
    case "${1:-auto}" in
        "auto"|"sync")
            auto_sync_checkpoints
            ;;
        "status")
            show_sync_status
            ;;
        "to-remote"|"push")
            force_sync_to_remote
            ;;
        "to-local"|"pull")
            force_sync_to_local
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"