# Reveal AI Alert Runbooks

## Overview

This directory contains operational runbooks for responding to Reveal AI alerts. Each runbook provides step-by-step procedures for investigating, resolving, and preventing specific alert types.

> **Note:** Reveal AI lacks native SIEM integration and webhooks. All monitoring is polling-based, requiring custom scripts to detect issues.

---

## Runbook Index

| ID | Runbook | Severity | Primary Alert Conditions |
|----|---------|----------|--------------------------|
| [REVEAL-001](REVEAL-001_Job_Failures.md) | Job Failures | CRITICAL | Status=4 (Error), any job type |
| [REVEAL-002](REVEAL-002_Stuck_Jobs.md) | Stuck/Long-Running Jobs | HIGH/CRITICAL | Status=2 (InProcess) exceeding thresholds |
| [REVEAL-003](REVEAL-003_API_Health.md) | API Health Failures | CRITICAL | NIA API down, timeout, non-200 response |
| [REVEAL-004](REVEAL-004_Export_Security.md) | Export & Production Security | CRITICAL/HIGH | Large exports, unauthorized exports |
| [REVEAL-005](REVEAL-005_Bulk_Operations.md) | Bulk Operations | HIGH/CRITICAL | Mass deletions, bulk updates |
| [REVEAL-006](REVEAL-006_Authentication_Security.md) | Authentication & Security | HIGH/CRITICAL | Failed logins, brute force, unusual activity |
| [REVEAL-007](REVEAL-007_Document_Access.md) | Document Access Monitoring | HIGH | High-volume downloads, after-hours access |
| [REVEAL-008](REVEAL-008_Deletion_Compliance.md) | Deletion & Compliance | CRITICAL | Status=7 (Deleted), compliance tracking |

---

## Quick Reference: Alert to Runbook Mapping

### Critical Alerts (Immediate Response - 15 min)

| Alert Condition | Runbook |
|-----------------|---------|
| Job Status = 4 (Error) | [REVEAL-001](REVEAL-001_Job_Failures.md) |
| NIA API not responding | [REVEAL-003](REVEAL-003_API_Health.md) |
| API timeout > 5 seconds | [REVEAL-003](REVEAL-003_API_Health.md) |
| Export > 10,000 documents | [REVEAL-004](REVEAL-004_Export_Security.md) |
| Mass deletion detected | [REVEAL-005](REVEAL-005_Bulk_Operations.md) |
| Job stuck > 24 hours | [REVEAL-002](REVEAL-002_Stuck_Jobs.md) |
| Brute force login attempt | [REVEAL-006](REVEAL-006_Authentication_Security.md) |

### High Alerts (1-Hour Response)

| Alert Condition | Runbook |
|-----------------|---------|
| Job stuck > 4 hours | [REVEAL-002](REVEAL-002_Stuck_Jobs.md) |
| Export > 1,000 documents | [REVEAL-004](REVEAL-004_Export_Security.md) |
| Bulk update operation | [REVEAL-005](REVEAL-005_Bulk_Operations.md) |
| Multiple failed logins | [REVEAL-006](REVEAL-006_Authentication_Security.md) |
| High-volume document downloads | [REVEAL-007](REVEAL-007_Document_Access.md) |
| After-hours data access | [REVEAL-007](REVEAL-007_Document_Access.md) |
| Document deletion | [REVEAL-008](REVEAL-008_Deletion_Compliance.md) |

### Medium Alerts (4-Hour Response)

| Alert Condition | Runbook |
|-----------------|---------|
| Job Status = 5 (Cancelled) | [REVEAL-001](REVEAL-001_Job_Failures.md) |
| Unusual login location | [REVEAL-006](REVEAL-006_Authentication_Security.md) |
| Reviewer activity anomaly | [REVEAL-007](REVEAL-007_Document_Access.md) |

---

## Job Status Code Reference

| Code | Status | Alert Level | Runbook |
|------|--------|-------------|---------|
| 0 | Created | INFO | - |
| 1 | Submitted | INFO | - |
| 2 | InProcess | MONITOR | [REVEAL-002](REVEAL-002_Stuck_Jobs.md) |
| 3 | Complete | OK | - |
| **4** | **Error** | **CRITICAL** | [REVEAL-001](REVEAL-001_Job_Failures.md) |
| 5 | Cancelled | MEDIUM | [REVEAL-001](REVEAL-001_Job_Failures.md) |
| 6 | CancelPending | INFO | - |
| **7** | **Deleted** | **AUDIT** | [REVEAL-008](REVEAL-008_Deletion_Compliance.md) |
| 8 | Modified | INFO | - |
| 9-12 | Processing/Deletion | MONITOR | [REVEAL-002](REVEAL-002_Stuck_Jobs.md) |

---

## Response SLA Summary

| Severity | Response Time | Escalation | Examples |
|----------|---------------|------------|----------|
| **CRITICAL** | Immediate (15 min) | On-call → Team Lead → Vendor | API down, job errors, mass deletion |
| **HIGH** | 1 hour | Assigned engineer → Team Lead | Stuck jobs, large exports, failed logins |
| **MEDIUM** | 4 hours | Scheduled review | Cancelled jobs, unusual activity |
| **LOW** | Next business day | Batch processing | Trends, metrics |

---

## Escalation Contacts

| Level | Contact | When |
|-------|---------|------|
| Tier 1 | On-call engineer | First response |
| Tier 2 | Team Lead | Unresolved after 1 hour |
| Tier 3 | Reveal Data Support | Platform issues, bugs |
| Security | Security Team | Data exfiltration, breaches |
| Legal | Legal/Compliance Team | Deletion compliance issues |

**Reveal Data Support:** support@revealdata.com

---

## Runbook Structure

Each runbook follows a consistent format:

1. **Alert Overview** - Quick reference for the alert type
2. **Alert Conditions** - What triggers this runbook
3. **Initial Triage** - First 5 minutes of response
4. **Investigation Procedures** - Gathering information
5. **Resolution Procedures** - Fixing the issue
6. **Escalation Procedures** - When and how to escalate
7. **Post-Incident Actions** - Follow-up tasks
8. **Prevention Measures** - Avoiding future incidents
9. **API Reference** - Useful API calls

---

## API Quick Reference

### Authentication

```bash
# Get session token
curl -X POST "https://[instance].revealdata.com/rest/api/v2/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'
# Returns: {"loginSessionId": "token..."}

# Use in subsequent requests
curl -X GET "https://[instance].revealdata.com/rest/api/v2/..." \
  -H "incontrolauthtoken: {loginSessionId}"
```

### NIA API Health Check

```bash
curl -X GET "http://[server]:5566/nia/version"
# Expect: 200 OK with version info
```

### Job Status Query

```bash
# Query jobs via NIA API
curl -X GET "http://[server]:5566/nia/jobs" \
  -H "Content-Type: application/json"
```

---

## Document Information

| Attribute | Value |
|-----------|-------|
| **Version** | 1.0 |
| **Last Updated** | 2024-11-29 |
| **Total Runbooks** | 8 |
| **Platform** | Reveal AI |
