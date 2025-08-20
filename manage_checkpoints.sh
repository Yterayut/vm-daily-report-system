#!/bin/bash
# manage_checkpoints.sh - Comprehensive checkpoint management utility
# Usage: ./manage_checkpoints.sh [command] [options]

set -e

# Configuration - Auto-detect local vs remote
if [ -f "/home/one-climate/project_vm_daily_report_2/daily_report.py" ]; then
    PROJECT_DIR="/home/one-climate/project_vm_daily_report_2"
else
    PROJECT_DIR="$(pwd)"
fi
CHECKPOINT_DIR="$PROJECT_DIR/checkpoints"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to show usage
show_usage() {
    echo -e "${BLUE}🎯 VM Daily Report System - Checkpoint Management${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0 [command] [options]"
    echo ""
    echo -e "${YELLOW}Commands:${NC}"
    echo -e "  ${GREEN}list${NC}                    List all checkpoints"
    echo -e "  ${GREEN}info${NC} <checkpoint>       Show detailed checkpoint information"
    echo -e "  ${GREEN}compare${NC} <cp1> <cp2>      Compare two checkpoints"
    echo -e "  ${GREEN}cleanup${NC} [keep_count]    Clean up old checkpoints (default: keep 10)"
    echo -e "  ${GREEN}export${NC} <checkpoint>     Export checkpoint to tar.gz"
    echo -e "  ${GREEN}import${NC} <tar_file>       Import checkpoint from tar.gz"
    echo -e "  ${GREEN}verify${NC} <checkpoint>     Verify checkpoint integrity"
    echo -e "  ${GREEN}status${NC}                  Show system and checkpoint status"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0 list"
    echo "  $0 info checkpoint_20250624_143022"
    echo "  $0 compare stable_v1.0 checkpoint_20250624_143022"
    echo "  $0 cleanup 5"
    echo "  $0 export stable_v1.0"
    echo ""
}

# Function to list checkpoints
list_checkpoints() {
    echo -e "${BLUE}📋 Checkpoint Inventory${NC}"
    echo -e "${BLUE}═══════════════════════${NC}"
    echo ""
    
    if [ ! -d "$CHECKPOINT_DIR" ] || [ -z "$(ls -A $CHECKPOINT_DIR 2>/dev/null)" ]; then
        echo -e "${RED}❌ No checkpoints found!${NC}"
        echo -e "${YELLOW}💡 Create a checkpoint first: ./create_checkpoint.sh${NC}"
        return 1
    fi
    
    local total_size=0
    local count=0
    
    printf "%-3s %-25s %-20s %-10s %-50s\n" "ID" "NAME" "DATE" "SIZE" "DESCRIPTION"
    echo "────────────────────────────────────────────────────────────────────────────────────────────────────"
    
    for checkpoint in $(find "$CHECKPOINT_DIR" -mindepth 1 -maxdepth 1 -type d | sort -r); do
        ((count++))
        local checkpoint_name=$(basename "$checkpoint")
        local info_file="$checkpoint/checkpoint_info.json"
        
        if [ -f "$info_file" ]; then
            local created_at=$(jq -r '.created_at' "$info_file" 2>/dev/null | cut -d'T' -f1 || echo "Unknown")
            local description=$(jq -r '.description' "$info_file" 2>/dev/null | cut -c1-50 || echo "No description")
            local size=$(jq -r '.total_size' "$info_file" 2>/dev/null || du -sh "$checkpoint" | cut -f1)
        else
            local created_at=$(stat -c %y "$checkpoint" | cut -d' ' -f1)
            local description="Legacy checkpoint"
            local size=$(du -sh "$checkpoint" | cut -f1)
        fi
        
        # Extract numeric size for total calculation
        local size_num=$(echo "$size" | sed 's/[^0-9.]//g')
        local size_unit=$(echo "$size" | sed 's/[0-9.]//g')
        if [[ "$size_unit" == *"M"* ]]; then
            total_size=$((total_size + ${size_num%.*}))
        elif [[ "$size_unit" == *"G"* ]]; then
            total_size=$((total_size + ${size_num%.*} * 1024))
        fi
        
        printf "%-3s %-25s %-20s %-10s %-50s\n" "$count" "$checkpoint_name" "$created_at" "$size" "$description"
    done
    
    echo "────────────────────────────────────────────────────────────────────────────────────────────────────"
    echo -e "${GREEN}📊 Total: $count checkpoints, ~${total_size}MB storage used${NC}"
    echo ""
}

# Function to show checkpoint info
show_checkpoint_info() {
    local checkpoint_name="$1"
    local checkpoint_path="$CHECKPOINT_DIR/$checkpoint_name"
    
    if [ ! -d "$checkpoint_path" ]; then
        echo -e "${RED}❌ Checkpoint not found: $checkpoint_name${NC}"
        return 1
    fi
    
    echo -e "${BLUE}📋 Checkpoint Information${NC}"
    echo -e "${BLUE}═══════════════════════${NC}"
    echo ""
    
    local info_file="$checkpoint_path/checkpoint_info.json"
    if [ -f "$info_file" ]; then
        echo -e "${YELLOW}Name:${NC} $(jq -r '.checkpoint_name' "$info_file")"
        echo -e "${YELLOW}Created:${NC} $(jq -r '.created_at' "$info_file")"
        echo -e "${YELLOW}By:${NC} $(jq -r '.created_by' "$info_file")"
        echo -e "${YELLOW}Host:${NC} $(jq -r '.hostname' "$info_file")"
        echo -e "${YELLOW}Description:${NC} $(jq -r '.description' "$info_file")"
        echo -e "${YELLOW}Size:${NC} $(jq -r '.total_size' "$info_file")"
        echo -e "${YELLOW}Files:${NC} $(jq -r '.files_backed_up' "$info_file")"
        
        local git_commit=$(jq -r '.git_commit' "$info_file")
        if [ "$git_commit" != "No git repository" ] && [ "$git_commit" != "null" ]; then
            echo -e "${YELLOW}Git Commit:${NC} $git_commit"
        fi
        
        echo ""
        echo -e "${CYAN}System Status at Creation:${NC}"
        jq -r '.system_status | to_entries[] | "  \(.key): \(.value)"' "$info_file" 2>/dev/null || echo "  No system status available"
    else
        echo -e "${YELLOW}Name:${NC} $checkpoint_name"
        echo -e "${YELLOW}Created:${NC} $(stat -c %y "$checkpoint_path" | cut -d'.' -f1)"
        echo -e "${YELLOW}Type:${NC} Legacy checkpoint"
        echo -e "${YELLOW}Size:${NC} $(du -sh "$checkpoint_path" | cut -f1)"
    fi
    
    echo ""
    echo -e "${CYAN}Files in Checkpoint:${NC}"
    find "$checkpoint_path" -type f ! -name "checkpoint_info.json" ! -name "system_snapshot.txt" ! -name "restore.sh" | sort | while read file; do
        local filename=$(basename "$file")
        local filesize=$(ls -lh "$file" | awk '{print $5}')
        echo -e "  📄 $filename ($filesize)"
    done
    
    echo ""
    if [ -d "$checkpoint_path/templates" ]; then
        echo -e "  📁 templates/ ($(find "$checkpoint_path/templates" -type f | wc -l) files)"
    fi
    if [ -d "$checkpoint_path/static" ]; then
        echo -e "  📁 static/ ($(find "$checkpoint_path/static" -type f | wc -l) files)"
    fi
    if [ -d "$checkpoint_path/logs" ]; then
        echo -e "  📁 logs/ ($(find "$checkpoint_path/logs" -type f | wc -l) files)"
    fi
    
    echo ""
}

# Function to compare checkpoints
compare_checkpoints() {
    local cp1="$1"
    local cp2="$2"
    local cp1_path="$CHECKPOINT_DIR/$cp1"
    local cp2_path="$CHECKPOINT_DIR/$cp2"
    
    if [ ! -d "$cp1_path" ]; then
        echo -e "${RED}❌ Checkpoint not found: $cp1${NC}"
        return 1
    fi
    
    if [ ! -d "$cp2_path" ]; then
        echo -e "${RED}❌ Checkpoint not found: $cp2${NC}"
        return 1
    fi
    
    echo -e "${BLUE}🔍 Checkpoint Comparison${NC}"
    echo -e "${BLUE}═══════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}Comparing:${NC}"
    echo -e "  📦 $cp1"
    echo -e "  📦 $cp2"
    echo ""
    
    # Compare creation times
    if [ -f "$cp1_path/checkpoint_info.json" ] && [ -f "$cp2_path/checkpoint_info.json" ]; then
        local cp1_date=$(jq -r '.created_at' "$cp1_path/checkpoint_info.json")
        local cp2_date=$(jq -r '.created_at' "$cp2_path/checkpoint_info.json")
        echo -e "${CYAN}Creation Times:${NC}"
        echo -e "  $cp1: $cp1_date"
        echo -e "  $cp2: $cp2_date"
        echo ""
    fi
    
    # Compare file lists
    echo -e "${CYAN}File Differences:${NC}"
    local cp1_files=$(find "$cp1_path" -name "*.py" -o -name "*.txt" -o -name ".env" | sort)
    local cp2_files=$(find "$cp2_path" -name "*.py" -o -name "*.txt" -o -name ".env" | sort)
    
    # Files only in cp1
    local only_in_cp1=$(comm -23 <(echo "$cp1_files" | xargs -I {} basename {}) <(echo "$cp2_files" | xargs -I {} basename {}))
    if [ ! -z "$only_in_cp1" ]; then
        echo -e "  ${GREEN}Only in $cp1:${NC}"
        echo "$only_in_cp1" | while read file; do echo "    + $file"; done
        echo ""
    fi
    
    # Files only in cp2
    local only_in_cp2=$(comm -13 <(echo "$cp1_files" | xargs -I {} basename {}) <(echo "$cp2_files" | xargs -I {} basename {}))
    if [ ! -z "$only_in_cp2" ]; then
        echo -e "  ${RED}Only in $cp2:${NC}"
        echo "$only_in_cp2" | while read file; do echo "    - $file"; done
        echo ""
    fi
    
    # Compare common files
    echo -e "${CYAN}Content Differences:${NC}"
    local common_files=$(comm -12 <(echo "$cp1_files" | xargs -I {} basename {}) <(echo "$cp2_files" | xargs -I {} basename {}))
    echo "$common_files" | while read filename; do
        local file1=$(find "$cp1_path" -name "$filename" | head -1)
        local file2=$(find "$cp2_path" -name "$filename" | head -1)
        
        if [ -f "$file1" ] && [ -f "$file2" ]; then
            if ! diff -q "$file1" "$file2" >/dev/null 2>&1; then
                echo -e "  📝 $filename: ${YELLOW}Modified${NC}"
                local lines1=$(wc -l < "$file1")
                local lines2=$(wc -l < "$file2")
                echo -e "    Lines: $lines1 → $lines2 ($(($lines2 - $lines1)))"
            else
                echo -e "  📄 $filename: ${GREEN}Identical${NC}"
            fi
        fi
    done
    
    echo ""
}

# Function to cleanup old checkpoints
cleanup_checkpoints() {
    local keep_count=${1:-10}
    
    echo -e "${BLUE}🧹 Checkpoint Cleanup${NC}"
    echo -e "${BLUE}══════════════════════${NC}"
    echo ""
    
    if [ ! -d "$CHECKPOINT_DIR" ]; then
        echo -e "${RED}❌ Checkpoint directory not found${NC}"
        return 1
    fi
    
    local checkpoints=($(find "$CHECKPOINT_DIR" -mindepth 1 -maxdepth 1 -type d | sort -r))
    local total_count=${#checkpoints[@]}
    
    echo -e "${YELLOW}Current checkpoints: $total_count${NC}"
    echo -e "${YELLOW}Keeping newest: $keep_count${NC}"
    echo ""
    
    if [ $total_count -le $keep_count ]; then
        echo -e "${GREEN}✅ No cleanup needed${NC}"
        return 0
    fi
    
    local to_remove=$((total_count - keep_count))
    echo -e "${RED}Will remove $to_remove old checkpoints:${NC}"
    
    for ((i=keep_count; i<total_count; i++)); do
        local checkpoint=${checkpoints[$i]}
        local checkpoint_name=$(basename "$checkpoint")
        local size=$(du -sh "$checkpoint" | cut -f1)
        echo -e "  🗑️  $checkpoint_name ($size)"
    done
    
    echo ""
    echo -e "${YELLOW}Continue with cleanup? (y/N):${NC} "
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        local freed_space=0
        for ((i=keep_count; i<total_count; i++)); do
            local checkpoint=${checkpoints[$i]}
            local checkpoint_name=$(basename "$checkpoint")
            
            # Calculate size before removal
            local size_kb=$(du -sk "$checkpoint" | cut -f1)
            freed_space=$((freed_space + size_kb))
            
            rm -rf "$checkpoint"
            echo -e "  ✅ Removed: $checkpoint_name"
        done
        
        local freed_mb=$((freed_space / 1024))
        echo ""
        echo -e "${GREEN}🎉 Cleanup completed!${NC}"
        echo -e "${GREEN}📊 Freed space: ${freed_mb}MB${NC}"
        echo -e "${GREEN}📦 Remaining checkpoints: $keep_count${NC}"
    else
        echo -e "${YELLOW}❌ Cleanup cancelled${NC}"
    fi
    
    echo ""
}

# Function to export checkpoint
export_checkpoint() {
    local checkpoint_name="$1"
    local checkpoint_path="$CHECKPOINT_DIR/$checkpoint_name"
    
    if [ ! -d "$checkpoint_path" ]; then
        echo -e "${RED}❌ Checkpoint not found: $checkpoint_name${NC}"
        return 1
    fi
    
    local export_file="${checkpoint_name}.tar.gz"
    
    echo -e "${BLUE}📦 Exporting Checkpoint${NC}"
    echo -e "${BLUE}══════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}Source:${NC} $checkpoint_name"
    echo -e "${YELLOW}Target:${NC} $export_file"
    echo ""
    
    cd "$CHECKPOINT_DIR"
    tar -czf "$export_file" "$checkpoint_name"
    
    local export_size=$(du -sh "$export_file" | cut -f1)
    
    echo -e "${GREEN}✅ Export completed!${NC}"
    echo -e "${GREEN}📄 File: $CHECKPOINT_DIR/$export_file${NC}"
    echo -e "${GREEN}💾 Size: $export_size${NC}"
    echo ""
}

# Function to import checkpoint
import_checkpoint() {
    local tar_file="$1"
    
    if [ ! -f "$tar_file" ]; then
        echo -e "${RED}❌ File not found: $tar_file${NC}"
        return 1
    fi
    
    echo -e "${BLUE}📥 Importing Checkpoint${NC}"
    echo -e "${BLUE}══════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}Source:${NC} $tar_file"
    echo ""
    
    mkdir -p "$CHECKPOINT_DIR"
    cd "$CHECKPOINT_DIR"
    tar -tzf "$tar_file" | head -5
    echo ""
    
    echo -e "${YELLOW}Continue with import? (y/N):${NC} "
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        tar -xzf "$tar_file"
        echo -e "${GREEN}✅ Import completed!${NC}"
        
        # List imported checkpoint
        local imported_name=$(tar -tzf "$tar_file" | head -1 | cut -d'/' -f1)
        if [ -d "$imported_name" ]; then
            echo -e "${GREEN}📦 Imported: $imported_name${NC}"
        fi
    else
        echo -e "${YELLOW}❌ Import cancelled${NC}"
    fi
    
    echo ""
}

# Function to verify checkpoint
verify_checkpoint() {
    local checkpoint_name="$1"
    local checkpoint_path="$CHECKPOINT_DIR/$checkpoint_name"
    
    if [ ! -d "$checkpoint_path" ]; then
        echo -e "${RED}❌ Checkpoint not found: $checkpoint_name${NC}"
        return 1
    fi
    
    echo -e "${BLUE}🔍 Verifying Checkpoint${NC}"
    echo -e "${BLUE}═══════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}Checkpoint:${NC} $checkpoint_name"
    echo ""
    
    local errors=0
    
    # Check essential files
    local essential_files=("daily_report.py" "mobile_api.py")
    echo -e "${CYAN}Essential Files:${NC}"
    for file in "${essential_files[@]}"; do
        if [ -f "$checkpoint_path/$file" ]; then
            echo -e "  ✅ $file"
        else
            echo -e "  ❌ $file (missing)"
            ((errors++))
        fi
    done
    
    # Check file integrity
    echo ""
    echo -e "${CYAN}File Integrity:${NC}"
    find "$checkpoint_path" -name "*.py" | while read file; do
        if python3 -m py_compile "$file" 2>/dev/null; then
            echo -e "  ✅ $(basename "$file") (syntax OK)"
        else
            echo -e "  ❌ $(basename "$file") (syntax error)"
            ((errors++))
        fi
    done
    
    # Check JSON files
    find "$checkpoint_path" -name "*.json" | while read file; do
        if jq empty "$file" 2>/dev/null; then
            echo -e "  ✅ $(basename "$file") (valid JSON)"
        else
            echo -e "  ❌ $(basename "$file") (invalid JSON)"
            ((errors++))
        fi
    done
    
    echo ""
    if [ $errors -eq 0 ]; then
        echo -e "${GREEN}✅ Checkpoint verification passed!${NC}"
    else
        echo -e "${RED}❌ Checkpoint verification failed ($errors errors)${NC}"
    fi
    
    echo ""
}

# Function to show system status
show_status() {
    echo -e "${BLUE}📊 System & Checkpoint Status${NC}"
    echo -e "${BLUE}═════════════════════════════${NC}"
    echo ""
    
    # System status
    echo -e "${CYAN}System Status:${NC}"
    echo -e "  Hostname: $(hostname)"
    echo -e "  Uptime: $(uptime | cut -d',' -f1 | cut -d' ' -f4-)"
    echo -e "  Load: $(uptime | awk -F'load average:' '{print $2}')"
    
    # Service status
    echo ""
    echo -e "${CYAN}Service Status:${NC}"
    if systemctl is-active --quiet vm-monitoring.service 2>/dev/null; then
        echo -e "  ✅ vm-monitoring.service (active)"
    else
        echo -e "  ❌ vm-monitoring.service (inactive)"
    fi
    
    local mobile_pids=$(pgrep -f "mobile_api.py" 2>/dev/null || echo "")
    if [ ! -z "$mobile_pids" ]; then
        local mobile_count=$(echo "$mobile_pids" | wc -l)
        echo -e "  ✅ mobile_api.py ($mobile_count processes)"
    else
        echo -e "  ❌ mobile_api.py (not running)"
    fi
    
    # Disk usage
    echo ""
    echo -e "${CYAN}Storage:${NC}"
    echo -e "  Project: $(du -sh $PROJECT_DIR | cut -f1)"
    if [ -d "$CHECKPOINT_DIR" ]; then
        echo -e "  Checkpoints: $(du -sh $CHECKPOINT_DIR | cut -f1)"
        local checkpoint_count=$(find "$CHECKPOINT_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l)
        echo -e "  Count: $checkpoint_count checkpoints"
    else
        echo -e "  Checkpoints: Not initialized"
    fi
    
    # Recent activity
    echo ""
    echo -e "${CYAN}Recent Activity:${NC}"
    if [ -f "$PROJECT_DIR/alerts.log" ]; then
        echo -e "  Last alert: $(tail -1 $PROJECT_DIR/alerts.log | cut -d' ' -f1-2 2>/dev/null || echo 'None')"
    fi
    
    if [ -d "$PROJECT_DIR/output" ]; then
        local last_report=$(ls -t $PROJECT_DIR/output/*.pdf 2>/dev/null | head -1)
        if [ ! -z "$last_report" ]; then
            echo -e "  Last report: $(basename "$last_report")"
        else
            echo -e "  Last report: None found"
        fi
    fi
    
    echo ""
}

# Main execution
main() {
    local command="$1"
    
    case "$command" in
        "list"|"ls")
            list_checkpoints
            ;;
        "info"|"show")
            if [ -z "$2" ]; then
                echo -e "${RED}❌ Please specify checkpoint name${NC}"
                exit 1
            fi
            show_checkpoint_info "$2"
            ;;
        "compare"|"diff")
            if [ -z "$2" ] || [ -z "$3" ]; then
                echo -e "${RED}❌ Please specify two checkpoint names${NC}"
                exit 1
            fi
            compare_checkpoints "$2" "$3"
            ;;
        "cleanup"|"clean")
            cleanup_checkpoints "$2"
            ;;
        "export")
            if [ -z "$2" ]; then
                echo -e "${RED}❌ Please specify checkpoint name${NC}"
                exit 1
            fi
            export_checkpoint "$2"
            ;;
        "import")
            if [ -z "$2" ]; then
                echo -e "${RED}❌ Please specify tar file path${NC}"
                exit 1
            fi
            import_checkpoint "$2"
            ;;
        "verify"|"check")
            if [ -z "$2" ]; then
                echo -e "${RED}❌ Please specify checkpoint name${NC}"
                exit 1
            fi
            verify_checkpoint "$2"
            ;;
        "status"|"stat")
            show_status
            ;;
        "help"|"-h"|"--help"|"")
            show_usage
            ;;
        *)
            echo -e "${RED}❌ Unknown command: $command${NC}"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"