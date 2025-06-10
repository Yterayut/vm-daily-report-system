#!/bin/bash
# Pre-commit hook to prevent secrets from being committed
# Install: cp pre-commit-security-check.sh .git/hooks/pre-commit

echo "🔒 Security check: Scanning for sensitive data..."

# Check for common secrets patterns
SECRETS_FOUND=0

# Check for email passwords
if git diff --cached --name-only | xargs grep -l "[YOUR_EMAIL_APP_PASSWORD]" 2>/dev/null; then
    echo "🚨 BLOCKED: Found exposed email password!"
    SECRETS_FOUND=1
fi

# Check for potential passwords in .env files
if git diff --cached --name-only | grep -E "\.(env|config)" | xargs grep -E "PASSWORD.*=" 2>/dev/null | grep -v "your_password\|PLACEHOLDER\|TEMPLATE"; then
    echo "🚨 BLOCKED: Found potential password in config file!"
    SECRETS_FOUND=1
fi

# Check for LINE tokens
if git diff --cached --name-only | xargs grep -l "LINE_CHANNEL_ACCESS_TOKEN.*=" 2>/dev/null | xargs grep -v "your_line_token"; then
    echo "🚨 BLOCKED: Found potential LINE token!"
    SECRETS_FOUND=1
fi

if [ $SECRETS_FOUND -eq 1 ]; then
    echo "❌ Commit blocked due to security concerns!"
    echo "Please remove sensitive data before committing."
    exit 1
fi

echo "✅ Security check passed"
exit 0
