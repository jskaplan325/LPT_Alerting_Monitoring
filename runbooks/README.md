# RelativityOne Alert Runbooks

## Overview

This directory contains comprehensive operational runbooks for responding to RelativityOne alerts. Each runbook provides step-by-step procedures for investigating, resolving, and preventing specific alert types. This collection provides **best-in-class coverage** for enterprise eDiscovery alerting and monitoring.

## Runbook Index

### Core Operations (RUNBOOK 001-007)

| ID | Runbook | Severity | Primary Alert Conditions |
|----|---------|----------|-------------------------|
| [RUNBOOK-001](RUNBOOK-001_Processing_Job_Failures.md) | Processing Job Failures | CRITICAL | Job errors, environment errors, data source errors |
| [RUNBOOK-002](RUNBOOK-002_Production_Job_Failures.md) | Production Job Failures | CRITICAL | Production errors, numbering conflicts, stuck jobs |
| [RUNBOOK-003](RUNBOOK-003_Imaging_Job_Failures.md) | Imaging Job Failures | CRITICAL/HIGH | Imaging errors, document-level failures |
| [RUNBOOK-004](RUNBOOK-004_Security_Alerts.md) | Security Alerts | CRITICAL/HIGH/MEDIUM | Brute force, failed logins, permission changes |
| [RUNBOOK-005](RUNBOOK-005_Integration_Points_Failures.md) | Integration Points Failures | CRITICAL/HIGH | Job failures, validation errors, sync issues |
| [RUNBOOK-006](RUNBOOK-006_Agent_Worker_Health.md) | Agent/Worker Health | CRITICAL/HIGH | Agent disabled, worker unresponsive |
| [RUNBOOK-007](RUNBOOK-007_dtSearch_Index_Issues.md) | dtSearch Index Issues | HIGH/MEDIUM | Build errors, fragmentation |

### Advanced Operations (RUNBOOK 008-012)

| ID | Runbook | Severity | Primary Alert Conditions |
|----|---------|----------|-------------------------|
| [RUNBOOK-008](RUNBOOK-008_Structured_Analytics_Failures.md) | Structured Analytics Failures | CRITICAL/HIGH | Analytics job failures, stuck operations |
| [RUNBOOK-009](RUNBOOK-009_Audit_Compliance_Monitoring.md) | Audit & Compliance Monitoring | CRITICAL/HIGH | Data exfiltration, suspicious activity |
| [RUNBOOK-010](RUNBOOK-010_Mass_Operations.md) | Mass Operations | CRITICAL/HIGH | Mass delete, bulk edits, legal hold impact |
| [RUNBOOK-011](RUNBOOK-011_OCR_Job_Failures.md) | OCR Job Failures | HIGH/MEDIUM | OCR errors, quality issues |
| [RUNBOOK-012](RUNBOOK-012_Branding_Job_Failures.md) | Branding Job Failures | HIGH/MEDIUM | Branding errors, template issues |

### Platform Health (RUNBOOK 013-018)

| ID | Runbook | Severity | Primary Alert Conditions |
|----|---------|----------|-------------------------|
| [RUNBOOK-013](RUNBOOK-013_Script_Execution_Issues.md) | Script Execution Issues | HIGH/MEDIUM | Script failures, performance, unauthorized |
| [RUNBOOK-014](RUNBOOK-014_Workspace_Health.md) | Workspace Health | HIGH/MEDIUM | Workspace unavailable, capacity issues |
| [RUNBOOK-015](RUNBOOK-015_Data_Export_Transfer.md) | Data Export & Transfer | CRITICAL/HIGH | Large exports, potential exfiltration |
| [RUNBOOK-016](RUNBOOK-016_Infrastructure_Performance.md) | Infrastructure Performance | CRITICAL/HIGH | SQL latency, worker resources, API issues |
| [RUNBOOK-017](RUNBOOK-017_Scheduled_Jobs.md) | Scheduled Jobs | CRITICAL/HIGH | Stopped jobs, recurring failures |
| [RUNBOOK-018](RUNBOOK-018_Telemetry_Agent_Critical.md) | **Telemetry Agent (CRITICAL)** | **CRITICAL** | **Agent disabled/stale = USER LOGOUT** |

---

## Quick Reference: Alert to Runbook Mapping

### Critical Alerts (Immediate Response - 15 min)

| Alert | Runbook |
|-------|---------|
| Processing job error/failed | [RUNBOOK-001](RUNBOOK-001_Processing_Job_Failures.md) |
| Production job error | [RUNBOOK-002](RUNBOOK-002_Production_Job_Failures.md) |
| Imaging job error | [RUNBOOK-003](RUNBOOK-003_Imaging_Job_Failures.md) |
| Brute force login (50+ failures/hour) | [RUNBOOK-004](RUNBOOK-004_Security_Alerts.md) |
| Lockbox setting modified | [RUNBOOK-004](RUNBOOK-004_Security_Alerts.md) |
| Integration Points job failed | [RUNBOOK-005](RUNBOOK-005_Integration_Points_Failures.md) |
| Worker "Service not responding" | [RUNBOOK-006](RUNBOOK-006_Agent_Worker_Health.md) |
| Structured Analytics failed | [RUNBOOK-008](RUNBOOK-008_Structured_Analytics_Failures.md) |
| Mass delete (>100 docs) | [RUNBOOK-010](RUNBOOK-010_Mass_Operations.md) |
| Legal hold documents affected | [RUNBOOK-010](RUNBOOK-010_Mass_Operations.md) |
| Large unauthorized export | [RUNBOOK-015](RUNBOOK-015_Data_Export_Transfer.md) |
| Database connectivity errors | [RUNBOOK-016](RUNBOOK-016_Infrastructure_Performance.md) |
| Scheduled job stopped | [RUNBOOK-017](RUNBOOK-017_Scheduled_Jobs.md) |
| **Telemetry Agent disabled** | [RUNBOOK-018](RUNBOOK-018_Telemetry_Agent_Critical.md) |
| **Telemetry Agent not responding** | [RUNBOOK-018](RUNBOOK-018_Telemetry_Agent_Critical.md) |
| **Telemetry Agent stale (>2 hours)** | [RUNBOOK-018](RUNBOOK-018_Telemetry_Agent_Critical.md) |

### High Alerts (1-Hour Response)

| Alert | Runbook |
|-------|---------|
| Document-level processing errors | [RUNBOOK-001](RUNBOOK-001_Processing_Job_Failures.md) |
| Imaging completed with errors | [RUNBOOK-003](RUNBOOK-003_Imaging_Job_Failures.md) |
| Multiple failed logins | [RUNBOOK-004](RUNBOOK-004_Security_Alerts.md) |
| Login method change | [RUNBOOK-004](RUNBOOK-004_Security_Alerts.md) |
| Permission elevation | [RUNBOOK-004](RUNBOOK-004_Security_Alerts.md) |
| Integration Points with errors | [RUNBOOK-005](RUNBOOK-005_Integration_Points_Failures.md) |
| Agent disabled | [RUNBOOK-006](RUNBOOK-006_Agent_Worker_Health.md) |
| dtSearch build error | [RUNBOOK-007](RUNBOOK-007_dtSearch_Index_Issues.md) |
| Analytics job errors | [RUNBOOK-008](RUNBOOK-008_Structured_Analytics_Failures.md) |
| Large export (>10k docs) | [RUNBOOK-009](RUNBOOK-009_Audit_Compliance_Monitoring.md) |
| Mass edit (>1k docs) | [RUNBOOK-010](RUNBOOK-010_Mass_Operations.md) |
| OCR job failed | [RUNBOOK-011](RUNBOOK-011_OCR_Job_Failures.md) |
| Branding job failed | [RUNBOOK-012](RUNBOOK-012_Branding_Job_Failures.md) |
| Script execution failed | [RUNBOOK-013](RUNBOOK-013_Script_Execution_Issues.md) |
| Workspace unavailable | [RUNBOOK-014](RUNBOOK-014_Workspace_Health.md) |
| After-hours export activity | [RUNBOOK-015](RUNBOOK-015_Data_Export_Transfer.md) |
| High resource utilization | [RUNBOOK-016](RUNBOOK-016_Infrastructure_Performance.md) |
| Scheduled job failure | [RUNBOOK-017](RUNBOOK-017_Scheduled_Jobs.md) |

### Medium/Warning Alerts (4-Hour Response)

| Alert | Runbook |
|-------|---------|
| Jobs paused >30 minutes | [RUNBOOK-001](RUNBOOK-001_Processing_Job_Failures.md) |
| Production job cancelled | [RUNBOOK-002](RUNBOOK-002_Production_Job_Failures.md) |
| New login location | [RUNBOOK-004](RUNBOOK-004_Security_Alerts.md) |
| Integration Points pending >30 min | [RUNBOOK-005](RUNBOOK-005_Integration_Points_Failures.md) |
| High dtSearch fragmentation | [RUNBOOK-007](RUNBOOK-007_dtSearch_Index_Issues.md) |
| OCR completed with errors | [RUNBOOK-011](RUNBOOK-011_OCR_Job_Failures.md) |
| Script performance issues | [RUNBOOK-013](RUNBOOK-013_Script_Execution_Issues.md) |
| Workspace capacity warning | [RUNBOOK-014](RUNBOOK-014_Workspace_Health.md) |
| Job duration exceeded | [RUNBOOK-017](RUNBOOK-017_Scheduled_Jobs.md) |

---

## Coverage Matrix

| Area | Runbook(s) | Coverage |
|------|------------|----------|
| **Processing Pipeline** | 001, 003, 011 | Processing, Imaging, OCR |
| **Production Pipeline** | 002, 012 | Productions, Branding |
| **Analytics** | 007, 008 | dtSearch, Structured Analytics |
| **Security** | 004, 009, 015 | Auth, Audit, Data Loss Prevention |
| **Integration** | 005, 017 | Integration Points, Scheduled Jobs |
| **Infrastructure** | 006, 014, 016 | Agents, Workers, Performance |
| **Operations** | 010, 013 | Mass Operations, Scripts |

---

## Response SLA Summary

| Severity | Response Time | Escalation | Examples |
|----------|---------------|------------|----------|
| **CRITICAL** | Immediate (15 min) | On-call → Team Lead → Vendor | Worker down, data breach, legal hold |
| **HIGH** | 1 hour | Assigned engineer → Team Lead | Job failures, security events |
| **MEDIUM** | 4 hours | Scheduled review | Performance, warnings |
| **LOW/WARNING** | Next business day | Batch processing | Monitoring, trends |

---

## Escalation Contacts

| Level | Contact | When |
|-------|---------|------|
| Tier 1 | On-call engineer | First response |
| Tier 2 | Team Lead | Unresolved after 1 hour |
| Tier 3 | Relativity Support | Infrastructure issues, platform bugs |
| Security | Security Team | Security incidents, data concerns |
| Legal | Legal Team | Legal hold impacts, compliance |

**Relativity Support:** support@relativity.com

---

## Using These Runbooks

### During an Incident
1. Identify the alert type
2. Open the corresponding runbook
3. Follow the **Initial Triage** steps (0-5 minutes)
4. Proceed to **Investigation Procedures**
5. Apply the appropriate **Resolution Procedure**
6. Complete **Post-Incident Actions**

### Runbook Structure
Each runbook follows a consistent format:
- **Alert Overview**: Quick reference for the alert type
- **Alert Conditions**: What triggers this runbook
- **Initial Triage**: First 5 minutes of response
- **Investigation Procedures**: Gathering information
- **Resolution Procedures**: Fixing the issue by scenario
- **Escalation Procedures**: When and how to escalate
- **Post-Incident Actions**: Follow-up tasks
- **Prevention Measures**: Avoiding future incidents
- **API Reference**: Useful API calls

---

## Maintaining These Runbooks

### Update Triggers
- New alert types added to monitoring
- Significant incidents with lessons learned
- Platform API or UI changes
- Process improvements identified

### Review Schedule
- **Quarterly:** Review of all runbooks
- **Immediate:** Update after major incidents
- **Annual:** Comprehensive revision

### Version Control
- Document all changes with version history
- Track author and date of changes
- Maintain changelog for each runbook

---

## Monitoring Implementation

### Polling Schedule Summary

| Interval | What to Monitor |
|----------|-----------------|
| 1 min | Worker health, API availability |
| 5 min | Processing/Production/Imaging queues, Critical job status |
| 15 min | Audit (security events), dtSearch, Scheduled jobs |
| 30 min | Workspace health, Performance metrics |
| 1 hour | Full audit export, Compliance reports |

### Alert Priority by API

| API/Source | Poll Frequency | Alert Priority |
|------------|----------------|----------------|
| Processing Set Manager | 1-5 min | Critical |
| Production Queue Manager | 1-5 min | Critical |
| Imaging Job Manager | 1-5 min | Critical |
| Worker Monitoring | 1 min | Critical |
| Security Alerts | Native push | Critical |
| Audit API | 5-15 min | High |
| Integration Points | 5 min | High |
| Structured Analytics | 5-10 min | High |
| dtSearch Index | 15 min | Medium |
| Workspace Manager | 15-30 min | Low |

---

## Related Documentation

- [eDiscovery Alerting Framework](../eDiscovery_Alerting_Framework.md)
- RelativityOne Platform Documentation: help.relativity.com
- RelativityOne API Documentation: platform.relativity.com
- Relativity Community: community.relativity.com

---

## Document Information

| Attribute | Value |
|-----------|-------|
| **Version** | 2.0 |
| **Last Updated** | 2024-11-29 |
| **Total Runbooks** | 18 |
| **Coverage Areas** | Processing, Production, Imaging, Security, Analytics, Integration, Infrastructure, Operations |

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-11-29 | Initial 7 runbooks (001-007) |
| 2.0 | 2024-11-29 | Added 10 advanced runbooks (008-017) for comprehensive coverage |
| 2.1 | 2024-11-29 | Added RUNBOOK-018 (Telemetry Agent - CRITICAL) with automated monitoring script |
