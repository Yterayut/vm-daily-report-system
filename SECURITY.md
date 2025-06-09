# 🔒 Security Guidelines

## ⚠️ CRITICAL: Protecting Sensitive Information

This project handles sensitive information including:
- API credentials and tokens
- Server connection details  
- Email passwords
- LINE Bot tokens
- Database connections

## 🚫 What NOT to commit to Git

### Never commit these files:
- `.env*` - Environment configuration files
- Any file containing passwords, tokens, or API keys
- Configuration files with server details
- Test files with real data
- Backup files that may contain sensitive info
- Log files that may contain credentials

### File patterns to avoid:
```
*password*
*secret*
*token*
*credential*
*key*
*auth*
test_*
debug_*
*real*
*production*
```

## ✅ Safe Practices

### 1. Environment Variables
Always use environment variables for sensitive data:
```bash
# ✅ Good
ZABBIX_PASS=your_password

# ❌ Bad - hardcoded in source
password = "your_password"
```

### 2. Template Files
Use template files instead of real config:
```bash
# ✅ Commit this
.env.example

# ❌ Never commit this  
.env
```

### 3. Gitignore
Maintain strict `.gitignore` rules and regularly review what gets committed.

### 4. Code Review
Always review `git status` before committing:
```bash
git status
git diff --cached
```

## 🔍 Before Committing Checklist

- [ ] No passwords or tokens in code
- [ ] No real server IPs or domains
- [ ] No actual email addresses (use examples)
- [ ] No sensitive file paths
- [ ] All environment variables are templates
- [ ] Log files are excluded
- [ ] Test files with real data are excluded

## 🚨 If Sensitive Data is Accidentally Committed

1. **Immediately** change all exposed credentials
2. Remove sensitive files from Git history:
```bash
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch sensitive_file.py' \
--prune-empty --tag-name-filter cat -- --all
```
3. Force push to overwrite history:
```bash
git push origin --force --all
```

## 📞 Security Contact

If you discover security issues, please contact the project maintainer immediately.

---

**Remember: It's easier to prevent security issues than to fix them later!**
