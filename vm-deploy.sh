#!/bin/bash
# =========================================================================
# VM Daily Report - Enhanced Deployment Script
# Support multiple deployment methods: SSH, SCP, local copy, and archive
# =========================================================================

# Configuration
LOCAL_PROJECT_DIR="/Users/teerayutyeerahem/project_vm_daily_report_2"
REMOTE_HOST="one-climate@192.168.20.10"
REMOTE_PROJECT_DIR="~/project_vm_daily_report_2"
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
ARCHIVE_NAME="vm_daily_report_$(date +%Y%m%d_%H%M%S).tar.gz"

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
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

# Check local directory
check_local_directory() {
    if [ ! -f "daily_report.py" ] || [ ! -f "enhanced_alert_system.py" ]; then
        error "Not in the correct project directory!"
        error "Please run this script from: $LOCAL_PROJECT_DIR"
        exit 1
    fi
    success "Local project directory verified"
}

# Get files to include in deployment
get_deployment_files() {
    cat > /tmp/deployment_files << 'EOF'
daily_report.py
ultimate_final_system.py
enhanced_alert_system.py
fetch_zabbix_data.py
generate_report.py
load_env.py
vm_state_tracker.py
mobile_api.py
update_log.py
.env.example
requirements.txt
vm-deploy.sh
start_dashboard.sh
vm-dashboard.service
vm-monitoring.service
README.md
static/
templates/
EOF
}

# Test SSH connectivity
test_ssh_connection() {
    log "Testing SSH connection to $REMOTE_HOST..."
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$REMOTE_HOST" "echo 'SSH connection successful'" >/dev/null 2>&1; then
        success "SSH connection established"
        return 0
    else
        warn "SSH connection failed - will use alternative methods"
        return 1
    fi
}

# Method 1: SSH/Rsync deployment (recommended)
deploy_ssh() {
    log "Deploying via SSH/Rsync..."
    
    if ! test_ssh_connection; then
        error "SSH connection required for this method"
        return 1
    fi
    
    # Create remote backup
    log "Creating remote backup..."
    ssh "$REMOTE_HOST" "
        cd $REMOTE_PROJECT_DIR 2>/dev/null && 
        cp -r . ../$BACKUP_DIR 2>/dev/null || echo 'Backup creation skipped (project might not exist)'
    "
    
    # Rsync files
    get_deployment_files
    log "Syncing files..."
    rsync -avz --files-from=/tmp/deployment_files \
        --delete-excluded \
        --exclude="*.pyc" \
        --exclude="__pycache__/" \
        --exclude="*.log*" \
        --exclude=".DS_Store" \
        --exclude="output/*.pdf" \
        "$LOCAL_PROJECT_DIR/" "$REMOTE_HOST:$REMOTE_PROJECT_DIR/"
    
    if [ $? -eq 0 ]; then
        success "SSH deployment completed"
        post_deployment_ssh
        return 0
    else
        error "SSH deployment failed"
        return 1
    fi
}

# Method 2: SCP deployment
deploy_scp() {
    log "Deploying via SCP..."
    
    if ! test_ssh_connection; then
        error "SSH connection required for SCP"
        return 1
    fi
    
    # Create temporary archive
    create_deployment_archive
    
    # Copy archive to remote
    log "Copying archive to remote server..."
    scp "/tmp/$ARCHIVE_NAME" "$REMOTE_HOST:~/"
    
    # Extract on remote
    log "Extracting on remote server..."
    ssh "$REMOTE_HOST" "
        cd ~/
        tar -xzf $ARCHIVE_NAME
        rm -f $ARCHIVE_NAME
        echo 'SCP deployment completed'
    "
    
    success "SCP deployment completed"
    return 0
}

# Method 3: Create local archive for manual deployment
deploy_archive() {
    log "Creating deployment archive..."
    
    create_deployment_archive
    
    local archive_path="/tmp/$ARCHIVE_NAME"
    local desktop_path="$HOME/Desktop/$ARCHIVE_NAME"
    
    # Copy to desktop for easy access
    cp "$archive_path" "$desktop_path"
    
    success "Deployment archive created!"
    info "Archive location: $desktop_path"
    info "Size: $(ls -lh "$desktop_path" | awk '{print $5}')"
    echo
    info "Manual deployment instructions:"
    info "1. Copy $ARCHIVE_NAME to the target server"
    info "2. Extract: tar -xzf $ARCHIVE_NAME"
    info "3. Set permissions: chmod +x *.py *.sh"
    info "4. Install dependencies: pip3 install -r requirements.txt"
    info "5. Configure .env file"
    info "6. Test: python3 daily_report.py --test"
    
    return 0
}

# Method 4: Local copy (for same machine deployment)
deploy_local() {
    log "Deploying locally..."
    
    local target_dir="$1"
    if [ -z "$target_dir" ]; then
        target_dir="$HOME/vm_daily_report_deployed"
    fi
    
    log "Target directory: $target_dir"
    
    # Create target directory
    mkdir -p "$target_dir"
    
    # Copy files
    get_deployment_files
    while IFS= read -r file; do
        if [ -f "$file" ] || [ -d "$file" ]; then
            cp -r "$file" "$target_dir/"
            echo "Copied: $file"
        fi
    done < /tmp/deployment_files
    
    # Set permissions
    chmod +x "$target_dir"/*.py "$target_dir"/*.sh 2>/dev/null || true
    
    success "Local deployment completed to: $target_dir"
    info "Next steps:"
    info "1. cd $target_dir"
    info "2. Configure .env file"
    info "3. pip3 install -r requirements.txt"
    info "4. python3 daily_report.py --test"
    
    return 0
}

# Create deployment archive
create_deployment_archive() {
    log "Creating deployment archive..."
    
    # Clean up any existing archive
    rm -f "/tmp/$ARCHIVE_NAME"
    
    # Create temporary directory
    local temp_dir="/tmp/vm_deploy_$$"
    mkdir -p "$temp_dir"
    
    # Copy deployment files
    get_deployment_files
    while IFS= read -r file; do
        if [ -f "$file" ] || [ -d "$file" ]; then
            cp -r "$file" "$temp_dir/"
        fi
    done < /tmp/deployment_files
    
    # Add deployment info
    cat > "$temp_dir/DEPLOYMENT_INFO.txt" << EOF
VM Daily Report System - Deployment Package
===========================================

Deployment Date: $(date)
Package Created: $(hostname)
Package Version: Enhanced v3.0

Files Included:
- daily_report.py (Main system file)
- ultimate_final_system.py (Alternative simple system)
- Enhanced alert system with power state detection
- Zabbix integration with VM monitoring
- PDF report generation with charts
- Email and LINE notifications
- VM power state change tracking
- Configuration files

Installation:
1. Extract this archive
2. Copy .env.example to .env and configure
3. Install dependencies: pip3 install -r requirements.txt
4. Set permissions: chmod +x *.py *.sh
5. Test: python3 daily_report.py --test
6. Run: python3 daily_report.py

Support: 
- Check README.md for detailed instructions
- Review logs for troubleshooting
EOF
    
    # Create archive
    cd "$temp_dir"
    tar -czf "/tmp/$ARCHIVE_NAME" ./*
    cd - >/dev/null
    
    # Cleanup
    rm -rf "$temp_dir"
    rm -f /tmp/deployment_files
    
    success "Archive created: /tmp/$ARCHIVE_NAME ($(ls -lh "/tmp/$ARCHIVE_NAME" | awk '{print $5}'))"
}

# Post-deployment tasks for SSH
post_deployment_ssh() {
    log "Running post-deployment tasks..."
    
    ssh "$REMOTE_HOST" "
        cd $REMOTE_PROJECT_DIR
        
        # Set permissions
        chmod +x *.py *.sh 2>/dev/null || true
        
        # Install dependencies
        if [ -f requirements.txt ]; then
            echo 'Installing dependencies...'
            pip3 install -r requirements.txt --quiet --user
        fi
        
        # Quick test
        echo 'Testing system...'
        python3 -c 'import sys; print(\"Python:\", sys.version)' 2>/dev/null || true
        python3 -c 'from linebot import LineBotApi; print(\"LINE SDK: OK\")' 2>/dev/null || echo 'LINE SDK: Install needed'
        
        echo 'Post-deployment completed'
    "
}

# Show system status
show_status() {
    log "Showing system status..."
    
    echo
    echo "=== LOCAL SYSTEM ==="
    echo "Directory: $(pwd)"
    echo "Python: $(python3 --version 2>/dev/null || echo 'Not found')"
    echo "Git: $(git log -1 --format='%h %s' 2>/dev/null || echo 'Not a git repo')"
    echo "Files: $(ls -1 *.py | wc -l) Python files"
    echo "Last run: $(ls -la *.log 2>/dev/null | head -1 | awk '{print $6, $7, $8}' || echo 'No logs')"
    
    if test_ssh_connection; then
        echo
        echo "=== REMOTE SYSTEM ==="
        ssh "$REMOTE_HOST" "
            cd $REMOTE_PROJECT_DIR 2>/dev/null || exit 1
            echo \"Directory: \$(pwd)\"
            echo \"Python: \$(python3 --version 2>/dev/null || echo 'Not found')\"
            echo \"Files: \$(ls -1 *.py 2>/dev/null | wc -l) Python files\"
            echo \"Last modified: \$(ls -la daily_report.py 2>/dev/null | awk '{print \$6, \$7, \$8}' || echo 'File not found')\"
            echo \"Last run: \$(ls -la *.log 2>/dev/null | head -1 | awk '{print \$6, \$7, \$8}' || echo 'No logs')\"
        " 2>/dev/null || echo "Remote status unavailable"
    else
        echo
        echo "=== REMOTE SYSTEM ==="
        echo "SSH connection not available"
    fi
}

# Test deployment
test_deployment() {
    log "Testing deployment..."
    
    if test_ssh_connection; then
        ssh "$REMOTE_HOST" "
            cd $REMOTE_PROJECT_DIR
            echo 'Testing remote deployment...'
            python3 daily_report.py --test-alerts 2>/dev/null || echo 'Test completed with warnings'
        "
    else
        log "Testing local system..."
        python3 daily_report.py --test-alerts
    fi
}

# Main menu
show_menu() {
    echo -e "${CYAN}================================================"
    echo -e "🚀 VM Daily Report - Enhanced Deployment Script"
    echo -e "================================================${NC}"
    echo
    echo "Available deployment methods:"
    echo "1. SSH/Rsync  - Direct deployment via SSH (recommended)"
    echo "2. SCP        - Archive transfer via SCP"
    echo "3. Archive    - Create archive for manual deployment"
    echo "4. Local      - Copy to local directory"
    echo "5. Status     - Show system status"
    echo "6. Test       - Test current deployment"
    echo "7. Help       - Show detailed help"
    echo "0. Exit"
    echo
}

# Show help
show_help() {
    cat << 'EOF'
VM Daily Report - Enhanced Deployment Script
===========================================

Usage: ./vm-deploy.sh [method] [options]

Methods:
  ssh         - Deploy via SSH/Rsync (requires SSH access)
  scp         - Deploy via SCP archive transfer
  archive     - Create deployment archive for manual transfer
  local [dir] - Copy to local directory (default: ~/vm_daily_report_deployed)
  status      - Show local and remote status
  test        - Test current deployment
  menu        - Show interactive menu (default)

Examples:
  ./vm-deploy.sh              # Interactive menu
  ./vm-deploy.sh ssh          # SSH deployment
  ./vm-deploy.sh archive      # Create archive
  ./vm-deploy.sh local /opt/vm_report  # Local copy
  ./vm-deploy.sh status       # Show status

SSH Configuration:
  - Host: one-climate@192.168.20.10
  - Requires SSH key authentication
  - Remote directory: ~/project_vm_daily_report_2

Archive Deployment:
  1. Run: ./vm-deploy.sh archive
  2. Copy generated archive to target server
  3. Extract: tar -xzf vm_daily_report_*.tar.gz
  4. Follow instructions in DEPLOYMENT_INFO.txt

Files Included in Deployment:
  - Main system files (daily_report.py, etc.)
  - Configuration files
  - Static assets
  - Documentation
  - Service files

Post-Deployment Steps:
  1. Configure .env file
  2. Install dependencies: pip3 install -r requirements.txt
  3. Test system: python3 daily_report.py --test
  4. Set up cron job for automation

EOF
}

# Main function
main() {
    # Change to project directory
    cd "$LOCAL_PROJECT_DIR" 2>/dev/null || {
        error "Cannot access project directory: $LOCAL_PROJECT_DIR"
        exit 1
    }
    
    case "$1" in
        "ssh")
            check_local_directory
            deploy_ssh
            ;;
        "scp")
            check_local_directory
            deploy_scp
            ;;
        "archive")
            check_local_directory
            deploy_archive
            ;;
        "local")
            check_local_directory
            deploy_local "$2"
            ;;
        "status")
            show_status
            ;;
        "test")
            test_deployment
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        "menu"|"")
            check_local_directory
            while true; do
                show_menu
                read -p "Select method (0-7): " choice
                case $choice in
                    1) deploy_ssh; break ;;
                    2) deploy_scp; break ;;
                    3) deploy_archive; break ;;
                    4) 
                        read -p "Target directory (default: ~/vm_daily_report_deployed): " target
                        deploy_local "$target"
                        break ;;
                    5) show_status; echo; read -p "Press Enter to continue..." ;;
                    6) test_deployment; echo; read -p "Press Enter to continue..." ;;
                    7) show_help; echo; read -p "Press Enter to continue..." ;;
                    0) exit 0 ;;
                    *) warn "Invalid option. Please try again." ;;
                esac
            done
            ;;
        *)
            error "Unknown command: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"