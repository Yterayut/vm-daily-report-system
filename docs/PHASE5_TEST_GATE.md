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
3. Production policy preflight.
   - Default: optional (warn-and-continue)
   - Required mode: `PRODUCTION_POLICY_REQUIRED=true`
4. Credential hardening preflight.
   - Default: optional (warn-and-continue)
   - Required mode: `CREDENTIAL_HARDENING_REQUIRED=true`
5. Zabbix auth preflight.
   - Default: optional (warn-and-continue)
   - Required mode: `ZABBIX_PREFLIGHT_REQUIRED=true`
6. Contract test for service health schema.
7. Smoke run:
   - Generate VM PDF + Service PDF.
   - Email integration in dry-run mode to one recipient only.
8. Ops dry-run metadata:
   - Branch/head capture.
   - Rollback hint.

## Expected Outputs
- `output/VM_Infrastructure_Report_<YYYY-MM-DD>.pdf`
- `output/Service_Health_Report_<YYYY-MM-DD>.pdf`
- `output/test_gate_<YYYY-MM-DD_HHMMSS>.json`
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

## Optional Production Policy Strict Gate
```bash
PRODUCTION_POLICY_REQUIRED=true ./scripts/phase5_test_gate.sh .
```

## Optional Credential Hardening Strict Gate
```bash
CREDENTIAL_HARDENING_REQUIRED=true ./scripts/phase5_test_gate.sh .
```

## Zabbix Credential Setup (Safe)
```bash
./scripts/configure_zabbix_env.sh .
./scripts/zabbix_auth_preflight.sh .
```

## Production Template
- File: `.env.prod.template`
- Purpose: baseline production flags and structure without secrets.

## Runtime Guard (App Startup)
- `check_credential_hardening()` now runs during app/report initialization.
- Behavior:
  - default: warn-only
  - enforced: fail-fast when one of these is true
    - `CREDENTIAL_HARDENING_REQUIRED=true`
    - `ENABLE_STRICT_ENV_GUARD=true`

## Gate Log UX
- Each gate prints explicit mode in log:
  - `mode=required`
  - `mode=optional`

## Rollback Guidance
- If gate fails, do not deploy.
- Revert only the current phase commit and rerun gate.
