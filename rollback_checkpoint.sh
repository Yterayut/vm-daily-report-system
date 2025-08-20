#!/bin/bash
# rollback_checkpoint.sh - Rollback system to a specific checkpoint
# Usage: ./rollback_checkpoint.sh [checkpoint_name]

set -e

# Configuration
PROJECT_DIR="/home/one-climate/project_vm_daily_report_2"
CHECKPOINT_DIR="$PROJECT_DIR/checkpoints"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to show usage
show_usage() {
    echo -e "${BLUE}🔄 VM Daily Report System - Checkpoint Rollback${NC}"
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0 [checkpoint_name]"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0                           # Interactive mode - choose from list"
    echo "  $0 checkpoint_20250624_143022   # Rollback to specific checkpoint"
    echo "  $0 stable_v1.0               # Rollback to named checkpoint"
    echo ""
}

# Function to list available checkpoints
list_checkpoints() {
    echo -e "${BLUE}📋 Available Checkpoints:${NC}"
    echo ""
    
    if [ ! -d "$CHECKPOINT_DIR" ] || [ -z "$(ls -A $CHECKPOINT_DIR 2>/dev/null)" ]; then
        echo -e "${RED}❌ No checkpoints found!${NC}"
        echo -e "${YELLOW}💡 Create a checkpoint first: ./create_checkpoint.sh${NC}"
        exit 1
    fi
    
    local counter=1
    for checkpoint in $(find "$CHECKPOINT_DIR" -mindepth 1 -maxdepth 1 -type d | sort -r); do
        local checkpoint_name=$(basename "$checkpoint")
        local info_file="$checkpoint/checkpoint_info.json"
        
        if [ -f "$info_file" ]; then
            local created_at=$(jq -r '.created_at' "$info_file" 2>/dev/null || echo "Unknown")
            local description=$(jq -r '.description' "$info_file" 2>/dev/null || echo "No description")
            local size=$(jq -r '.total_size' "$info_file" 2>/dev/null || du -sh "$checkpoint" | cut -f1)
        else
            local created_at=$(stat -c %y "$checkpoint" | cut -d' ' -f1,2 | cut -d'.' -f1)
            local description="Legacy checkpoint"
            local size=$(du -sh "$checkpoint" | cut -f1)
        fi
        
        echo -e "${GREEN}[$counter]${NC} ${YELLOW}$checkpoint_name${NC}"
        echo -e "    📅 Created: $created_at"
        echo -e "    📝 $description"
        echo -e "    💾 Size: $size"
        echo ""
        
        checkpoint_array[$counter]="$checkpoint_name"
        ((counter++))
    done
    
    return $((counter-1))
}

# Function to confirm rollback
confirm_rollback() {
    local checkpoint_name="$1"
    local checkpoint_path="$CHECKPOINT_DIR/$checkpoint_name"
    
    echo -e "${YELLOW}⚠️  ROLLBACK CONFIRMATION${NC}"
    echo -e "${YELLOW}═══════════════════════════${NC}"
    echo -e "${RED}This will OVERWRITE current system files!${NC}"
    echo ""
    echo -e "Target checkpoint: ${GREEN}$checkpoint_name${NC}"
    echo -e "Checkpoint path: $checkpoint_path"
    echo ""
    
    if [ -f "$checkpoint_path/checkpoint_info.json" ]; then
        local created_at=$(jq -r '.created_at' "$checkpoint_path/checkpoint_info.json" 2>/dev/null)
        local description=$(jq -r '.description' "$checkpoint_path/checkpoint_info.json" 2>/dev/null)
        echo -e "Created: $created_at"
        echo -e "Description: $description"
        echo ""
    fi
    
    echo -e "${YELLOW}Current system will be backed up as 'pre_rollback_$(date +%Y%m%d_%H%M%S)'${NC}"
    echo ""
    echo -e "${RED}Continue with rollback? (yes/no):${NC} "
    read -r response
    
    if [[ ! "$response" == "yes" ]]; then
        echo -e "${YELLOW}❌ Rollback cancelled by user${NC}"
        exit 0
    fi
}

# Function to create pre-rollback backup
create_pre_rollback_backup() {
    echo -e "${BLUE}📦 Creating pre-rollback backup...${NC}"
    
    local backup_name="pre_rollback_$(date +%Y%m%d_%H%M%S)"
    local backup_path="$CHECKPOINT_DIR/$backup_name"
    
    mkdir -p "$backup_path"
    
    # Backup current state
    local files_to_backup=(
        "daily_report.py"
        "fetch_zabbix_data.py" 
        "generate_report.py"
        "enhanced_alert_system.py"
        "mobile_api.py"
        "load_env.py"
        "vm_state_tracker.py"
        "ultimate_final_system.py"
        "requirements.txt"
        ".env"
    )
    
    for file in "${files_to_backup[@]}"; do
        if [ -f "$PROJECT_DIR/$file" ]; then
            cp "$PROJECT_DIR/$file" "$backup_path/" 2>/dev/null || true
        fi
    done
    
    # Create backup info
    cat > "$backup_path/checkpoint_info.json" << EOF
{
    "checkpoint_name": "$backup_name",
    "description": "Automatic backup before rollback",
    "created_at": "$(date -Iseconds)",
    "created_by": "$(whoami)",
    "backup_type": "pre_rollback",
    "rollback_target": "$1"
}
EOF
    
    echo -e "  ✅ Pre-rollback backup created: $backup_name"
}

# Function to stop services safely
stop_services() {
    echo -e "${BLUE}🛑 Stopping services...${NC}"
    
    # Stop systemd services
    if systemctl is-active --quiet vm-monitoring.service 2>/dev/null; then
        echo -e "  🔴 Stopping vm-monitoring.service..."
        sudo systemctl stop vm-monitoring.service || true
    fi
    
    # Stop mobile API processes
    local mobile_pids=$(pgrep -f "mobile_api.py" 2>/dev/null || true)
    if [ ! -z "$mobile_pids" ]; then
        echo -e "  🔴 Stopping mobile_api.py processes..."
        pkill -f mobile_api.py 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        mobile_pids=$(pgrep -f "mobile_api.py" 2>/dev/null || true)
        if [ ! -z "$mobile_pids" ]; then
            echo -e "  💀 Force killing mobile_api.py..."
            pkill -9 -f mobile_api.py 2>/dev/null || true
        fi
    fi
    
    echo -e "  ✅ Services stopped"
}

# Function to restore files from checkpoint
restore_files() {
    local checkpoint_path="$1"
    
    echo -e "${BLUE}📁 Restoring files from checkpoint...${NC}"
    
    # Restore Python files
    for file in "$checkpoint_path"/*.py; do
        if [ -f "$file" ]; then
            local filename=$(basename "$file")
            cp "$file" "$PROJECT_DIR/$filename"
            echo -e "  ✅ $filename"
        fi
    done
    
    # Restore configuration files
    for file in "$checkpoint_path"/.env "$checkpoint_path"/requirements.txt; do
        if [ -f "$file" ]; then
            local filename=$(basename "$file")
            cp "$file" "$PROJECT_DIR/$filename"
            echo -e "  ✅ $filename"
        fi
    done
    
    # Restore service files
    for file in "$checkpoint_path"/*.service; do
        if [ -f "$file" ]; then
            local filename=$(basename "$file")
            cp "$file" "$PROJECT_DIR/$filename"
            echo -e "  ✅ $filename"
        fi
    done
    
    # Restore directories
    for dir in templates static; do
        if [ -d "$checkpoint_path/$dir" ]; then
            rm -rf "$PROJECT_DIR/$dir" 2>/dev/null || true
            cp -r "$checkpoint_path/$dir" "$PROJECT_DIR/"
            echo -e "  ✅ $dir/"
        fi
    done
}

# Function to start services
start_services() {
    echo -e "${BLUE}🚀 Starting services...${NC}"
    
    cd "$PROJECT_DIR"
    
    # Reload systemd and start vm-monitoring service
    if [ -f "vm-monitoring.service" ]; then
        echo -e "  🔄 Reloading systemd daemon..."
        sudo systemctl daemon-reload
        
        echo -e "  🟢 Starting vm-monitoring.service..."
        sudo systemctl start vm-monitoring.service || echo -e "  ⚠️  vm-monitoring.service failed to start"
    fi
    
    # Start mobile API
    if [ -f "mobile_api.py" ]; then
        echo -e "  🟢 Starting mobile_api.py..."
        nohup python3 mobile_api.py > /dev/null 2>&1 &
        sleep 2
        
        if pgrep -f "mobile_api.py" > /dev/null; then
            echo -e "  ✅ mobile_api.py started (PID: $(pgrep -f mobile_api.py))"
        else
            echo -e "  ⚠️  mobile_api.py failed to start"
        fi
    fi
}

# Function to verify rollback
verify_rollback() {
    local checkpoint_name="$1"
    
    echo -e "${BLUE}🔍 Verifying rollback...${NC}"
    
    # Check if core files exist
    local core_files=("daily_report.py" "mobile_api.py" ".env")
    for file in "${core_files[@]}"; do
        if [ -f "$PROJECT_DIR/$file" ]; then
            echo -e "  ✅ $file"
        else
            echo -e "  ❌ $file (missing)"
        fi
    done
    
    # Check services
    sleep 3
    if systemctl is-active --quiet vm-monitoring.service 2>/dev/null; then
        echo -e "  ✅ vm-monitoring.service (active)"
    else
        echo -e "  ⚠️  vm-monitoring.service (inactive)"
    fi
    
    if pgrep -f "mobile_api.py" > /dev/null; then
        echo -e "  ✅ mobile_api.py (running)"
    else
        echo -e "  ⚠️  mobile_api.py (not running)"
    fi
}

# Main execution
main() {
    clear
    echo -e "${BLUE}🔄 VM Daily Report System - Checkpoint Rollback${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
    echo ""
    
    # Check if checkpoint directory exists
    if [ ! -d "$CHECKPOINT_DIR" ]; then
        echo -e "${RED}❌ Checkpoint directory not found: $CHECKPOINT_DIR${NC}"
        echo -e "${YELLOW}💡 Create a checkpoint first: ./create_checkpoint.sh${NC}"
        exit 1
    fi
    
    local checkpoint_name="$1"
    
    # If no checkpoint specified, show interactive selection
    if [ -z "$checkpoint_name" ]; then
        declare -A checkpoint_array
        list_checkpoints
        local checkpoint_count=$?
        
        if [ $checkpoint_count -eq 0 ]; then
            exit 1
        fi
        
        echo -e "${YELLOW}Select checkpoint number (1-$checkpoint_count) or 'q' to quit:${NC} "
        read -r selection
        
        if [ "$selection" = "q" ] || [ "$selection" = "Q" ]; then
            echo -e "${YELLOW}❌ Rollback cancelled${NC}"
            exit 0
        fi
        
        if [[ ! "$selection" =~ ^[0-9]+$ ]] || [ "$selection" -lt 1 ] || [ "$selection" -gt $checkpoint_count ]; then
            echo -e "${RED}❌ Invalid selection${NC}"
            exit 1
        fi
        
        checkpoint_name="${checkpoint_array[$selection]}"
    fi
    
    # Validate checkpoint exists
    local checkpoint_path="$CHECKPOINT_DIR/$checkpoint_name"
    if [ ! -d "$checkpoint_path" ]; then
        echo -e "${RED}❌ Checkpoint not found: $checkpoint_name${NC}"
        echo ""
        declare -A checkpoint_array
        list_checkpoints
        exit 1
    fi
    
    # Confirm rollback
    confirm_rollback "$checkpoint_name"
    
    echo ""
    echo -e "${BLUE}🔄 Starting rollback process...${NC}"
    echo ""
    
    # Create pre-rollback backup
    create_pre_rollback_backup "$checkpoint_name"
    
    # Stop services
    stop_services
    
    # Restore files
    restore_files "$checkpoint_path"
    
    # Start services
    start_services
    
    # Verify rollback
    verify_rollback "$checkpoint_name"
    
    echo ""
    echo -e "${GREEN}✅ Rollback completed successfully!${NC}"
    echo -e "${GREEN}📂 Restored from: $checkpoint_name${NC}"
    echo ""
    echo -e "${YELLOW}📋 Check system status:${NC}"
    echo -e "${YELLOW}   systemctl status vm-monitoring.service${NC}"
    echo -e "${YELLOW}   ps aux | grep mobile_api.py${NC}"
    echo ""
    echo -e "${YELLOW}📊 Monitor logs:${NC}"
    echo -e "${YELLOW}   tail -f alerts.log${NC}"
    echo ""
}

# Check if help requested
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_usage
    exit 0
fi

# Run main function
main "$@"