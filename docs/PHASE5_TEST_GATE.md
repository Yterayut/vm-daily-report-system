# Phase 5 Test Gate and Runbook

Date: 2026-03-06

## Objective
- Validate production readiness with repeatable gates.
- Prevent rollout if any critical check fails.

## Gate Script
- Script: `scripts/phase5_test_gate.sh`
- Run:
```bash
./scripts/phase5_test_gate.sh
```

## Included Gates
1. Compile check for main runtime modules.
2. Secret scan (`gitleaks` if available, regex fallback otherwise).
3. Zabbix auth preflight.
   - Default: optional (warn-and-continue)
   - Required mode: `ZABBIX_PREFLIGHT_REQUIRED=true`
4. Contract test for service health schema.
5. Smoke run:
   - Generate VM PDF + Service PDF.
   - Email integration in dry-run mode to one recipient only.
6. Ops dry-run metadata:
   - Branch/head capture.
   - Rollback hint.

## Expected Outputs
- `output/VM_Infrastructure_Report_<YYYY-MM-DD>.pdf`
- `output/Service_Health_Report_<YYYY-MM-DD>.pdf`
- `Phase 5 Test Gate PASS`

## Optional Real Email Test (Controlled)
- Validate SMTP credential first:
```bash
./scripts/email_auth_preflight.sh .
```
- Only run real send after preflight passes:
```bash
ENABLE_NEW_SERVICE_SOURCE=true \
EMAIL_DRY_RUN=false \
LINE_NOTIFICATIONS_ENABLED=false \
TO_EMAILS=yterayut@gmail.com \
python3 daily_report.py --simple
```

## Optional Zabbix Strict Gate
```bash
ZABBIX_PREFLIGHT_REQUIRED=true ./scripts/phase5_test_gate.sh .
```

## Rollback Guidance
- If gate fails, do not deploy.
- Revert only the current phase commit and rerun gate.
