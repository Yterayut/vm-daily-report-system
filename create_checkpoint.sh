#!/bin/bash
# create_checkpoint.sh - Create system checkpoint for rollback capability
# Usage: ./create_checkpoint.sh [checkpoint_name] [description]

set -e

# Configuration - Auto-detect local vs remote
if [ -f "/home/one-climate/project_vm_daily_report_2/daily_report.py" ]; then
    PROJECT_DIR="/home/one-climate/project_vm_daily_report_2"
else
    PROJECT_DIR="$(pwd)"
fi
CHECKPOINT_DIR="$PROJECT_DIR/checkpoints"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
CHECKPOINT_NAME=${1:-"checkpoint_${TIMESTAMP}"}
DESCRIPTION=${2:-"Automated checkpoint created at $(date)"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create checkpoints directory if it doesn't exist
mkdir -p "$CHECKPOINT_DIR"

echo -e "${BLUE}🔄 Creating VM Daily Report System Checkpoint...${NC}"
echo -e "${YELLOW}📁 Checkpoint Name: $CHECKPOINT_NAME${NC}"
echo -e "${YELLOW}📝 Description: $DESCRIPTION${NC}"
echo ""

# Create checkpoint directory
CHECKPOINT_PATH="$CHECKPOINT_DIR/$CHECKPOINT_NAME"
mkdir -p "$CHECKPOINT_PATH"

echo -e "${BLUE}📂 Backing up core files...${NC}"

# Files to backup
CORE_FILES=(
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
    "vm-dashboard.service"
    "vm-monitoring.service"
)

# Backup core files
for file in "${CORE_FILES[@]}"; do
    if [ -f "$PROJECT_DIR/$file" ]; then
        cp "$PROJECT_DIR/$file" "$CHECKPOINT_PATH/"
        echo -e "  ✅ $file"
    else
        echo -e "  ⚠️  $file (not found)"
    fi
done

# Backup directories
echo -e "${BLUE}📁 Backing up directories...${NC}"
DIRS_TO_BACKUP=(
    "templates"
    "static" 
    "logs"
    "archive"
)

for dir in "${DIRS_TO_BACKUP[@]}"; do
    if [ -d "$PROJECT_DIR/$dir" ]; then
        cp -r "$PROJECT_DIR/$dir" "$CHECKPOINT_PATH/"
        echo -e "  ✅ $dir/ ($(du -sh $PROJECT_DIR/$dir | cut -f1))"
    else
        echo -e "  ⚠️  $dir/ (not found)"
    fi
done

# Create checkpoint metadata
echo -e "${BLUE}📋 Creating checkpoint metadata...${NC}"
cat > "$CHECKPOINT_PATH/checkpoint_info.json" << EOF
{
    "checkpoint_name": "$CHECKPOINT_NAME",
    "description": "$DESCRIPTION",
    "created_at": "$(date -Iseconds)",
    "created_by": "$(whoami)",
    "hostname": "$(hostname)",
    "git_commit": "$(cd $PROJECT_DIR && git rev-parse HEAD 2>/dev/null || echo 'No git repository')",
    "system_status": {
        "vm_monitoring_service": "$(systemctl is-active vm-monitoring.service 2>/dev/null || echo 'inactive')",
        "mobile_api_processes": $(ps aux | grep mobile_api.py | grep -v grep | wc -l),
        "disk_usage": "$(df -h $PROJECT_DIR | tail -1 | awk '{print $5}')",
        "last_report": "$(ls -t $PROJECT_DIR/output/*.pdf 2>/dev/null | head -1 | xargs basename 2>/dev/null || echo 'none')"
    },
    "files_backed_up": $(find "$CHECKPOINT_PATH" -type f ! -name "checkpoint_info.json" | wc -l),
    "total_size": "$(du -sh $CHECKPOINT_PATH | cut -f1)"
}
EOF

# Create system snapshot
echo -e "${BLUE}🔍 Creating system snapshot...${NC}"
cat > "$CHECKPOINT_PATH/system_snapshot.txt" << EOF
=== VM Daily Report System Checkpoint ===
Created: $(date)
Checkpoint: $CHECKPOINT_NAME
Description: $DESCRIPTION

=== Running Services ===
$(ps aux | grep -E "(python.*daily_report|python.*mobile_api)" | grep -v grep)

=== Cron Jobs ===
$(crontab -l 2>/dev/null || echo "No crontab")

=== System Load ===
$(uptime)

=== Disk Usage ===
$(df -h $PROJECT_DIR)

=== Recent Logs (last 10 lines) ===
$(tail -10 $PROJECT_DIR/alerts.log 2>/dev/null || echo "No alerts.log")

=== Last 3 Reports ===
$(ls -la $PROJECT_DIR/output/*.pdf 2>/dev/null | tail -3 || echo "No reports found")

=== Environment Status ===
$(if [ -f "$PROJECT_DIR/.env" ]; then echo "✅ .env file exists"; else echo "❌ .env file missing"; fi)
$(if [ -f "$PROJECT_DIR/requirements.txt" ]; then echo "✅ requirements.txt exists"; else echo "❌ requirements.txt missing"; fi)

=== Network Status ===
$(ping -c 1 8.8.8.8 >/dev/null 2>&1 && echo "✅ Internet connectivity OK" || echo "❌ Internet connectivity issues")
EOF

# Create restore script for this checkpoint
echo -e "${BLUE}🔧 Creating restore script...${NC}"
cat > "$CHECKPOINT_PATH/restore.sh" << 'EOF'
#!/bin/bash
# Auto-generated restore script for this checkpoint

set -e
PROJECT_DIR="/home/one-climate/project_vm_daily_report_2"
CHECKPOINT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔄 Restoring from checkpoint: $(basename $CHECKPOINT_PATH)"
echo "⚠️  This will overwrite current files. Continue? (y/N)"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "❌ Restore cancelled"
    exit 1
fi

echo "📁 Stopping services..."
sudo systemctl stop vm-monitoring.service 2>/dev/null || true
pkill -f mobile_api.py 2>/dev/null || true

echo "📂 Restoring files..."
cp -v "$CHECKPOINT_PATH"/*.py "$PROJECT_DIR/" 2>/dev/null || true
cp -v "$CHECKPOINT_PATH"/*.txt "$PROJECT_DIR/" 2>/dev/null || true
cp -v "$CHECKPOINT_PATH"/.env "$PROJECT_DIR/" 2>/dev/null || true
cp -v "$CHECKPOINT_PATH"/*.service "$PROJECT_DIR/" 2>/dev/null || true

if [ -d "$CHECKPOINT_PATH/templates" ]; then
    cp -rv "$CHECKPOINT_PATH/templates" "$PROJECT_DIR/"
fi
if [ -d "$CHECKPOINT_PATH/static" ]; then
    cp -rv "$CHECKPOINT_PATH/static" "$PROJECT_DIR/"
fi

echo "🔧 Restarting services..."
cd "$PROJECT_DIR"
sudo systemctl start vm-monitoring.service 2>/dev/null || true
nohup python3 mobile_api.py > /dev/null 2>&1 &

echo "✅ Restore completed from checkpoint: $(basename $CHECKPOINT_PATH)"
echo "📋 Check system status with: systemctl status vm-monitoring.service"
EOF

chmod +x "$CHECKPOINT_PATH/restore.sh"

# Update checkpoint index
echo -e "${BLUE}📋 Updating checkpoint index...${NC}"
CHECKPOINT_INDEX="$CHECKPOINT_DIR/checkpoint_index.txt"
echo "$(date -Iseconds) | $CHECKPOINT_NAME | $DESCRIPTION | $(du -sh $CHECKPOINT_PATH | cut -f1)" >> "$CHECKPOINT_INDEX"

# Calculate total checkpoint storage
TOTAL_SIZE=$(du -sh "$CHECKPOINT_DIR" | cut -f1)
CHECKPOINT_COUNT=$(find "$CHECKPOINT_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l)

echo ""
echo -e "${GREEN}✅ Checkpoint created successfully!${NC}"
echo -e "${GREEN}📂 Location: $CHECKPOINT_PATH${NC}"
echo -e "${GREEN}💾 Size: $(du -sh $CHECKPOINT_PATH | cut -f1)${NC}"
echo -e "${GREEN}📊 Total checkpoints: $CHECKPOINT_COUNT ($TOTAL_SIZE)${NC}"
echo ""
echo -e "${YELLOW}🔧 To restore this checkpoint:${NC}"
echo -e "${YELLOW}   $CHECKPOINT_PATH/restore.sh${NC}"
echo ""
echo -e "${YELLOW}📋 To list all checkpoints:${NC}"
echo -e "${YELLOW}   ./list_checkpoints.sh${NC}"

# Auto-sync checkpoint to remote server
if [ -f "./checkpoint_sync.sh" ]; then
    echo ""
    echo -e "${BLUE}🔄 Auto-syncing checkpoint to remote server...${NC}"
    if ./checkpoint_sync.sh auto >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Checkpoint synced to remote server${NC}"
    else
        echo -e "${YELLOW}⚠️ Auto-sync failed (manual sync may be needed)${NC}"
    fi
fi

echo ""

# Clean up old checkpoints (keep last 10)
CHECKPOINT_LIMIT=10
OLD_CHECKPOINTS=$(find "$CHECKPOINT_DIR" -mindepth 1 -maxdepth 1 -type d | sort | head -n -$CHECKPOINT_LIMIT)
if [ ! -z "$OLD_CHECKPOINTS" ]; then
    echo -e "${YELLOW}🧹 Cleaning up old checkpoints (keeping last $CHECKPOINT_LIMIT)...${NC}"
    echo "$OLD_CHECKPOINTS" | while read checkpoint; do
        echo -e "  🗑️  Removing: $(basename $checkpoint)"
        rm -rf "$checkpoint"
    done
fi

echo -e "${BLUE}🎯 Checkpoint system ready for development!${NC}"