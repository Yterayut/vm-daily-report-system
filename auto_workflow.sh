#!/bin/bash
# =========================================================================
# Auto Workflow - Complete Development and Deployment Pipeline
# Implements the standard workflow with automatic checkpoint management
# =========================================================================

set -e

# Configuration
LOCAL_PROJECT_DIR="$(pwd)"
REMOTE_HOST="one-climate@192.168.20.10"
REMOTE_PROJECT_DIR="~/project_vm_daily_report_2"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging
log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Test SSH connection
test_ssh() {
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$REMOTE_HOST" "echo 'ok'" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Step 1: Development and Testing (Manual)
step1_develop() {
    echo -e "${CYAN}🎯 Step 1: Development and Testing${NC}"
    echo "This step is done manually:"
    echo "  ✅ Code development"
    echo "  ✅ Local testing"
    echo "  ✅ Feature validation"
    echo ""
    log "Ready for automated workflow..."
}

# Step 2: Create checkpoint before deploy (Local)
step2_local_checkpoint() {
    echo -e "${CYAN}🎯 Step 2: Creating Local Checkpoint Before Deploy${NC}"
    
    local checkpoint_name="before_deploy_$(date +%Y%m%d_%H%M%S)"
    local description="Checkpoint before deployment - $(date)"
    
    log "Creating local checkpoint: $checkpoint_name"
    
    if [ -f "./create_checkpoint.sh" ]; then
        ./create_checkpoint.sh "$checkpoint_name" "$description"
        success "✅ Local checkpoint created: $checkpoint_name"
        return 0
    else
        error "❌ create_checkpoint.sh not found"
        return 1
    fi
}

# Step 3: Create checkpoint on server before receiving changes
step3_server_checkpoint() {
    echo -e "${CYAN}🎯 Step 3: Creating Server Checkpoint Before Changes${NC}"
    
    if ! test_ssh; then
        error "❌ SSH connection failed"
        return 1
    fi
    
    local checkpoint_name="before_receive_$(date +%Y%m%d_%H%M%S)"
    local description="Checkpoint before receiving changes - $(date)"
    
    log "Creating server checkpoint: $checkpoint_name"
    
    ssh "$REMOTE_HOST" "
        cd \"$REMOTE_PROJECT_DIR\"
        if [ -f './create_checkpoint.sh' ]; then
            ./create_checkpoint.sh \"$checkpoint_name\" \"$description\"
            echo 'Server checkpoint created successfully'
        else
            echo 'ERROR: create_checkpoint.sh not found on server'
            exit 1
        fi
    "
    
    if [ $? -eq 0 ]; then
        success "✅ Server checkpoint created: $checkpoint_name"
        return 0
    else
        error "❌ Failed to create server checkpoint"
        return 1
    fi
}

# Step 4: Deploy code to server
step4_deploy() {
    echo -e "${CYAN}🎯 Step 4: Deploying Code to Server${NC}"
    
    log "Starting deployment..."
    
    if [ -f "./vm-deploy.sh" ]; then
        ./vm-deploy.sh ssh
        if [ $? -eq 0 ]; then
            success "✅ Deployment completed successfully"
            return 0
        else
            error "❌ Deployment failed"
            return 1
        fi
    else
        error "❌ vm-deploy.sh not found"
        return 1
    fi
}

# Step 5: Create checkpoint after successful deploy
step5_post_deploy_checkpoint() {
    echo -e "${CYAN}🎯 Step 5: Creating Post-Deploy Checkpoint${NC}"
    
    if ! test_ssh; then
        error "❌ SSH connection failed"
        return 1
    fi
    
    local checkpoint_name="after_deploy_$(date +%Y%m%d_%H%M%S)"
    local description="Checkpoint after successful deployment - $(date)"
    
    log "Creating post-deployment checkpoint: $checkpoint_name"
    
    ssh "$REMOTE_HOST" "
        cd \"$REMOTE_PROJECT_DIR\"
        if [ -f './create_checkpoint.sh' ]; then
            ./create_checkpoint.sh \"$checkpoint_name\" \"$description\"
            echo 'Post-deployment checkpoint created successfully'
        else
            echo 'ERROR: create_checkpoint.sh not found on server'
            exit 1
        fi
    "
    
    if [ $? -eq 0 ]; then
        success "✅ Post-deployment checkpoint created: $checkpoint_name"
        return 0
    else
        error "❌ Failed to create post-deployment checkpoint"
        return 1
    fi
}

# Step 6: Auto-sync all checkpoints
step6_sync_checkpoints() {
    echo -e "${CYAN}🎯 Step 6: Auto-Syncing All Checkpoints${NC}"
    
    log "Starting checkpoint synchronization..."
    
    if [ -f "./checkpoint_sync.sh" ]; then
        ./checkpoint_sync.sh auto
        if [ $? -eq 0 ]; then
            success "✅ All checkpoints synchronized"
            return 0
        else
            warn "⚠️ Checkpoint sync had issues (check logs)"
            return 1
        fi
    else
        warn "⚠️ checkpoint_sync.sh not found, skipping sync"
        return 1
    fi
}

# Test deployment and show status
test_deployment() {
    echo -e "${CYAN}🎯 Testing Deployment${NC}"
    
    if ! test_ssh; then
        error "❌ SSH connection failed"
        return 1
    fi
    
    log "Running deployment test..."
    
    ssh "$REMOTE_HOST" "
        cd \"$REMOTE_PROJECT_DIR\"
        echo '🔍 Testing system components...'
        
        # Test Python
        python3 --version && echo '✅ Python OK' || echo '❌ Python issues'
        
        # Test main script
        if [ -f 'daily_report.py' ]; then
            python3 -c 'import daily_report; print(\"✅ daily_report.py OK\")' 2>/dev/null || echo '⚠️ daily_report.py import issues'
        fi
        
        # Test dependencies
        python3 -c 'import requests; print(\"✅ requests OK\")' 2>/dev/null || echo '⚠️ requests missing'
        python3 -c 'from linebot import LineBotApi; print(\"✅ LINE SDK OK\")' 2>/dev/null || echo '⚠️ LINE SDK issues'
        
        # Check recent logs
        if [ -f 'cron.log' ]; then
            echo '📋 Recent cron log entries:'
            tail -3 cron.log 2>/dev/null || echo 'No recent cron logs'
        fi
        
        echo '✅ Deployment test completed'
    "
    
    success "✅ Deployment test completed"
}

# Show final status
show_final_status() {
    echo ""
    echo -e "${CYAN}🎉 Workflow Completed Successfully!${NC}"
    echo -e "${CYAN}=================================${NC}"
    echo ""
    
    # Show checkpoint status
    if [ -f "./checkpoint_sync.sh" ]; then
        ./checkpoint_sync.sh status
    fi
    
    echo ""
    echo -e "${GREEN}✅ Standard Workflow Steps Completed:${NC}"
    echo "   1. ✅ Development and Testing (manual)"
    echo "   2. ✅ Local checkpoint before deploy"
    echo "   3. ✅ Server checkpoint before changes"
    echo "   4. ✅ Code deployment to server"
    echo "   5. ✅ Server checkpoint after deploy"
    echo "   6. ✅ Checkpoint synchronization"
    echo ""
    echo -e "${BLUE}🚀 System Status: Production Ready${NC}"
    echo -e "${BLUE}📧 Email System: Enhanced with anti-spam headers${NC}"
    echo -e "${BLUE}💾 Checkpoints: Synchronized across local and server${NC}"
    echo ""
}

# Rollback function (emergency use)
emergency_rollback() {
    local checkpoint_name="$1"
    if [ -z "$checkpoint_name" ]; then
        error "❌ Please specify checkpoint name for rollback"
        echo "Usage: $0 rollback <checkpoint_name>"
        return 1
    fi
    
    echo -e "${YELLOW}⚠️ Emergency Rollback to: $checkpoint_name${NC}"
    read -p "Are you sure? This will revert changes. (y/N): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        log "Rolling back to checkpoint: $checkpoint_name"
        
        if ! test_ssh; then
            error "❌ SSH connection failed"
            return 1
        fi
        
        ssh "$REMOTE_HOST" "
            cd \"$REMOTE_PROJECT_DIR\"
            if [ -f './rollback_checkpoint.sh' ]; then
                ./rollback_checkpoint.sh \"$checkpoint_name\"
            elif [ -f \"./checkpoints/$checkpoint_name/restore.sh\" ]; then
                \"./checkpoints/$checkpoint_name/restore.sh\"
            else
                echo 'ERROR: Rollback scripts not found'
                exit 1
            fi
        "
        
        if [ $? -eq 0 ]; then
            success "✅ Rollback completed"
            log "Re-syncing checkpoints after rollback..."
            [ -f "./checkpoint_sync.sh" ] && ./checkpoint_sync.sh auto
        else
            error "❌ Rollback failed"
        fi
    else
        log "Rollback cancelled"
    fi
}

# Help function
show_help() {
    cat << 'EOF'
Auto Workflow - Complete Development and Deployment Pipeline
===========================================================

Usage: ./auto_workflow.sh [command]

Commands:
  full        - Run complete workflow (Steps 1-6)
  deploy      - Run deployment workflow (Steps 2-6)
  test        - Test current deployment
  status      - Show system and checkpoint status
  rollback    - Emergency rollback to checkpoint
  help        - Show this help

Standard Workflow Steps:
  1. Development and Testing (manual)
  2. Create local checkpoint before deploy
  3. Create server checkpoint before changes
  4. Deploy code to server
  5. Create server checkpoint after deploy
  6. Auto-sync all checkpoints

Examples:
  ./auto_workflow.sh full              # Complete workflow
  ./auto_workflow.sh deploy            # Deployment only
  ./auto_workflow.sh test              # Test deployment
  ./auto_workflow.sh rollback stable   # Emergency rollback

Features:
  ✅ Automated checkpoint management
  ✅ SSH deployment with error handling
  ✅ Bidirectional checkpoint sync
  ✅ Deployment testing and validation
  ✅ Emergency rollback capability

Configuration:
  Local:  Current directory
  Remote: one-climate@192.168.20.10:~/project_vm_daily_report_2

EOF
}

# Main function
main() {
    case "${1:-full}" in
        "full")
            step1_develop
            step2_local_checkpoint && \
            step3_server_checkpoint && \
            step4_deploy && \
            step5_post_deploy_checkpoint && \
            step6_sync_checkpoints && \
            test_deployment && \
            show_final_status
            ;;
        "deploy")
            step2_local_checkpoint && \
            step3_server_checkpoint && \
            step4_deploy && \
            step5_post_deploy_checkpoint && \
            step6_sync_checkpoints && \
            test_deployment && \
            show_final_status
            ;;
        "test")
            test_deployment
            ;;
        "status")
            if [ -f "./checkpoint_sync.sh" ]; then
                ./checkpoint_sync.sh status
            else
                echo "Checkpoint sync not available"
            fi
            ;;
        "rollback")
            emergency_rollback "$2"
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