# eDiscovery Alerting & Monitoring Framework

A comprehensive alerting and monitoring solution for **RelativityOne** and **Reveal AI** eDiscovery environments. This repository provides enterprise-grade operational runbooks and automated monitoring scripts to ensure platform reliability, security, and compliance.

---

## Platform Coverage

| Platform | Runbooks | Scripts | API Support |
|----------|----------|---------|-------------|
| **RelativityOne** | 18 | 6 | OAuth 2.0, REST API, Webhooks |
| **RelativityOne aiR** | 2 | 1 | Object Manager API, Polling |
| **Reveal AI** | 8 | 3 | Session Token, REST API, Polling |

---

## Repository Structure

```
LPT_Alerting_Monitoring/
├── README.md                              # This file
│
├── relativity-one/                        # RelativityOne Platform
│   ├── eDiscovery_Alerting_Framework.md   # RelativityOne architecture
│   ├── aiR_Alerting_Framework.md          # aiR for Review & Privilege monitoring
│   ├── runbooks/
│   │   ├── README.md                      # Runbook index
│   │   ├── RUNBOOK-001 through RUNBOOK-018
│   │   ├── RUNBOOK-AIR-001                # aiR for Review job failures
│   │   └── RUNBOOK-AIR-002                # aiR for Privilege pipeline failures
│   └── scripts/
│       ├── README.md                      # Script documentation
│       ├── config.example.json            # Configuration template
│       ├── scom_integration.py            # SCOM/Event Log helper
│       ├── *_monitor.py                   # 6 core monitoring scripts
│       └── air_job_monitor.py             # aiR for Review & Privilege monitor
│
└── reveal-ai/                             # Reveal AI Platform
    ├── Reveal_AI_Alerting_Framework.md    # Reveal AI architecture
    ├── runbooks/
    │   ├── README.md                      # Runbook index
    │   └── REVEAL-001 through REVEAL-008
    └── scripts/
        ├── README.md                      # Script documentation
        ├── config.example.json            # Configuration template
        ├── scom_integration.py            # SCOM/Event Log helper
        └── reveal_*_monitor.py            # 3 monitoring scripts
```

---

# RelativityOne

## Critical Alert

> ⚠️ **If the Telemetry Metrics Transmission Agent fails, users will be logged out of RelativityOne.** This framework includes dedicated monitoring to prevent this business-critical failure.

## Monitoring Scripts

| Script | Purpose | Polling | Priority |
|--------|---------|---------|----------|
| `telemetry_agent_monitor.py` | Telemetry agent (prevents user logout) | 1 min | **CRITICAL** |
| `billing_agent_monitor.py` | Single-instance billing agent (compliance) | 1 min | **CRITICAL** |
| `alert_manager_monitor.py` | Meta-monitoring (native platform alerts) | 1 min | **CRITICAL** |
| `worker_health_monitor.py` | All worker servers & agents | 1 min | **CRITICAL** |
| `job_queue_monitor.py` | Processing/Production/Imaging queues | 5 min | HIGH |
| `security_audit_monitor.py` | Brute force, exports, lockbox, permissions | 5 min | HIGH |

## Runbooks (18 Total)

| ID | Runbook | Severity |
|----|---------|----------|
| 001 | Processing Job Failures | CRITICAL |
| 002 | Production Job Failures | CRITICAL |
| 003 | Imaging Job Failures | CRITICAL/HIGH |
| 004 | Security Alerts | CRITICAL/HIGH |
| 005 | Integration Points Failures | CRITICAL/HIGH |
| 006 | Agent/Worker Health | CRITICAL/HIGH |
| 007 | dtSearch Index Issues | HIGH/MEDIUM |
| 008 | Structured Analytics Failures | CRITICAL/HIGH |
| 009 | Audit & Compliance Monitoring | CRITICAL/HIGH |
| 010 | Mass Operations | CRITICAL/HIGH |
| 011 | OCR Job Failures | HIGH/MEDIUM |
| 012 | Branding Job Failures | HIGH/MEDIUM |
| 013 | Script Execution Issues | HIGH/MEDIUM |
| 014 | Workspace Health | HIGH/MEDIUM |
| 015 | Data Export & Transfer | CRITICAL/HIGH |
| 016 | Infrastructure Performance | CRITICAL/HIGH |
| 017 | Scheduled Jobs | CRITICAL/HIGH |
| **018** | **Telemetry Agent** | **CRITICAL** |

### Quick Start (RelativityOne)

```bash
# 1. Install dependencies
pip install requests python-dateutil

# 2. Configure
cp relativity-one/scripts/config.example.json relativity-one/scripts/config.json
# Edit with your RelativityOne OAuth credentials

# 3. Test
python relativity-one/scripts/telemetry_agent_monitor.py --config relativity-one/scripts/config.json --dry-run --verbose

# 4. Run
python relativity-one/scripts/telemetry_agent_monitor.py --config relativity-one/scripts/config.json
```

---

# Relativity aiR (aiR for Review & aiR for Privilege)

## Overview

Relativity aiR products use Azure OpenAI's GPT-4 Omni model for AI-powered document analysis:

| Product | Purpose | Workflow |
|---------|---------|----------|
| **aiR for Review** | Relevance analysis, key document identification, issue categorization | Develop → Validate → Apply |
| **aiR for Privilege** | Privilege prediction and classification | 6-step sequential pipeline |

## Monitoring Script

| Script | Purpose | Polling | Priority |
|--------|---------|---------|----------|
| `air_job_monitor.py` | aiR for Review jobs + aiR for Privilege pipelines | 5 min | **CRITICAL** |

## aiR for Review Job Statuses

| Status | Alert Level |
|--------|-------------|
| Not Started | INFO |
| Queued | INFO (WARNING if >2h) |
| In Progress | MONITOR (stuck detection) |
| Completed | OK |
| Cancelling | MEDIUM |
| **Errored** | **CRITICAL** |

## aiR for Privilege Pipeline Statuses

| Status | Alert Level |
|--------|-------------|
| Not Started / Running | INFO |
| Completed | OK |
| **Run Failed** | **CRITICAL** |
| **Apply Annotations Failed** | **HIGH** |
| **Blocked** | **CRITICAL** |
| Awaiting Annotations | WARNING if >24h |

## aiR Runbooks

| ID | Runbook | Severity |
|----|---------|----------|
| AIR-001 | aiR for Review Job Failures | CRITICAL/HIGH |
| AIR-002 | aiR for Privilege Pipeline Failures | CRITICAL/HIGH |

### Quick Start (aiR)

```bash
# Test aiR monitoring
python relativity-one/scripts/air_job_monitor.py --config config.json --dry-run --verbose

# Run aiR for Review only
python relativity-one/scripts/air_job_monitor.py --config config.json --review-only

# Run aiR for Privilege only
python relativity-one/scripts/air_job_monitor.py --config config.json --privilege-only

# Run both
python relativity-one/scripts/air_job_monitor.py --config config.json
```

---

# Reveal AI

## Platform Notes

> ⚠️ **Reveal AI has no webhook support and no native SIEM connectors.** All monitoring requires custom polling. See [Reveal AI Framework](reveal-ai/Reveal_AI_Alerting_Framework.md) for details.

## Monitoring Scripts

| Script | Purpose | Polling | Priority |
|--------|---------|---------|----------|
| `reveal_api_health_monitor.py` | NIA + REST API availability | 1 min | **CRITICAL** |
| `reveal_job_monitor.py` | Job failures (Status=4) and stuck jobs | 5 min | **CRITICAL** |
| `reveal_export_monitor.py` | Large exports, after-hours activity | 15 min | HIGH |

## Job Status Model (12-State)

| Code | Status | Alert Level |
|------|--------|-------------|
| 0 | Created | INFO |
| 1 | Submitted | INFO |
| 2 | InProcess | MONITOR (stuck detection) |
| 3 | Complete | OK |
| **4** | **Error** | **CRITICAL** |
| 5 | Cancelled | WARNING |
| 6 | CancelPending | INFO |
| **7** | **Deleted** | **AUDIT** |
| 8 | Modified | INFO |
| 9-12 | Processing/Deletion | MONITOR |

## Runbooks (8 Total)

| ID | Runbook | Severity |
|----|---------|----------|
| REVEAL-001 | Job Failures | CRITICAL |
| REVEAL-002 | Stuck/Long-Running Jobs | HIGH/CRITICAL |
| REVEAL-003 | API Health Failures | CRITICAL |
| REVEAL-004 | Export & Production Security | CRITICAL/HIGH |
| REVEAL-005 | Bulk Operations | HIGH/CRITICAL |
| REVEAL-006 | Authentication & Security | HIGH/CRITICAL |
| REVEAL-007 | Document Access Monitoring | HIGH |
| REVEAL-008 | Deletion & Compliance | CRITICAL |

### Quick Start (Reveal AI)

```bash
# 1. Install dependencies
pip install requests python-dateutil

# 2. Configure
cp reveal-ai/scripts/config.example.json reveal-ai/scripts/config.json
# Edit with your Reveal AI credentials

# 3. Test
python reveal-ai/scripts/reveal_api_health_monitor.py --config reveal-ai/scripts/config.json --dry-run --verbose

# 4. Run
python reveal-ai/scripts/reveal_api_health_monitor.py --config reveal-ai/scripts/config.json
```

---

## Alert Thresholds

### RelativityOne Agent Monitors

| Level | Last Activity Age |
|-------|-------------------|
| OK | < 30 minutes |
| WARNING | 30-60 minutes |
| HIGH | 60-120 minutes |
| CRITICAL | > 120 minutes |

### Reveal AI Job Monitor

| Level | Failed Jobs | Stuck Duration |
|-------|-------------|----------------|
| WARNING | 1-2 | > 4 hours |
| HIGH | 3-4 | > 8 hours |
| CRITICAL | 5+ | > 24 hours |

### Export Security (Both Platforms)

| Level | Document Count |
|-------|----------------|
| WARNING | > 1,000 docs |
| HIGH | > 5,000 docs |
| CRITICAL | > 10,000 docs |

---

## Response SLAs

| Severity | Response Time | Examples |
|----------|---------------|----------|
| **CRITICAL** | Immediate (15 min) | API down, job errors, mass deletion, telemetry failure |
| **HIGH** | 1 hour | Stuck jobs, large exports, failed logins |
| **MEDIUM** | 4 hours | Cancelled jobs, performance issues |
| **LOW** | Next business day | Monitoring, trends |

---

## Features (All Scripts)

| Feature | Description |
|---------|-------------|
| **Authentication** | OAuth 2.0 (RelativityOne), Session Token (Reveal AI) |
| **Multi-Channel Alerts** | Email, Slack, PagerDuty, Microsoft Teams, Webhooks |
| **SCOM Integration** | Windows Event Log for Microsoft SCOM monitoring |
| **State Tracking** | Prevents duplicate alerts, tracks state changes |
| **Exit Codes** | 0=OK, 1=WARN, 2=HIGH, 3=CRITICAL |
| **Dry Run Mode** | Test without sending alerts |
| **Configurable Thresholds** | Customize alert sensitivity |

---

## Microsoft SCOM Integration

All monitoring scripts integrate with Microsoft System Center Operations Manager (SCOM) via Windows Event Log.

### Event Sources

| Platform | Event Source |
|----------|-------------|
| RelativityOne | `RelativityOne-Monitor` |
| Reveal AI | `RevealAI-Monitor` |

### Complete Event ID Map

| Monitor | Base | OK | INFO | WARN | HIGH | CRIT |
|---------|------|-----|------|------|------|------|
| **RelativityOne** |
| Telemetry Agent | 1000 | 1000 | 1001 | 1002 | 1003 | 1004 |
| Billing Agent | 1100 | 1100 | 1101 | 1102 | 1103 | 1104 |
| Worker Health | 1200 | 1200 | 1201 | 1202 | 1203 | 1204 |
| Job Queue | 1300 | 1300 | 1301 | 1302 | 1303 | 1304 |
| Security Audit | 1400 | 1400 | 1401 | 1402 | 1403 | 1404 |
| Alert Manager | 1500 | 1500 | 1501 | 1502 | 1503 | 1504 |
| aiR for Review | 1600 | 1600 | 1601 | 1602 | 1603 | 1604 |
| aiR for Privilege | 1700 | 1700 | 1701 | 1702 | 1703 | 1704 |
| **Reveal AI** |
| API Health | 2000 | 2000 | 2001 | 2002 | 2003 | 2004 |
| Job Monitor | 2100 | 2100 | 2101 | 2102 | 2103 | 2104 |
| Export Monitor | 2200 | 2200 | 2201 | 2202 | 2203 | 2204 |

### SCOM Setup

**1. Register Event Sources (run as Administrator on monitoring server):**

```powershell
$sources = @("RelativityOne-Monitor", "RevealAI-Monitor")
foreach ($source in $sources) {
    if (-not [System.Diagnostics.EventLog]::SourceExists($source)) {
        [System.Diagnostics.EventLog]::CreateEventSource($source, "Application")
        Write-Host "Created event source: $source"
    }
}
```

Or use the built-in helper:
```bash
python relativity-one/scripts/scom_integration.py --setup
```

**2. Enable SCOM in config.json:**

```json
{
  "scom_enabled": true
}
```

**3. Install Windows dependencies:**

```bash
pip install pywin32
```

### SCOM Management Pack Rules

**All Critical Alerts:**
```xml
<Rule ID="eDiscovery.Critical.Alert">
  <DataSource>
    <EventLog>Application</EventLog>
    <EventSource>RelativityOne-Monitor</EventSource>
    <EventID>1004,1104,1204,1304,1404,1504,1604,1704</EventID>
  </DataSource>
  <WriteAction>
    <AlertSeverity>Critical</AlertSeverity>
    <AlertDescription>eDiscovery critical alert detected</AlertDescription>
  </WriteAction>
</Rule>

<Rule ID="RevealAI.Critical.Alert">
  <DataSource>
    <EventLog>Application</EventLog>
    <EventSource>RevealAI-Monitor</EventSource>
    <EventID>2004,2104,2204</EventID>
  </DataSource>
  <WriteAction>
    <AlertSeverity>Critical</AlertSeverity>
    <AlertDescription>Reveal AI critical alert detected</AlertDescription>
  </WriteAction>
</Rule>
```

**All High Severity Alerts:**
```xml
<Rule ID="eDiscovery.High.Alert">
  <DataSource>
    <EventLog>Application</EventLog>
    <EventSource>RelativityOne-Monitor</EventSource>
    <EventID>1003,1103,1203,1303,1403,1503,1603,1703</EventID>
  </DataSource>
  <WriteAction>
    <AlertSeverity>Error</AlertSeverity>
  </WriteAction>
</Rule>

<Rule ID="RevealAI.High.Alert">
  <DataSource>
    <EventLog>Application</EventLog>
    <EventSource>RevealAI-Monitor</EventSource>
    <EventID>2003,2103,2203</EventID>
  </DataSource>
  <WriteAction>
    <AlertSeverity>Error</AlertSeverity>
  </WriteAction>
</Rule>
```

**All Warning Alerts:**
```xml
<Rule ID="eDiscovery.Warning.Alert">
  <DataSource>
    <EventLog>Application</EventLog>
    <EventSource>RelativityOne-Monitor</EventSource>
    <EventID>1002,1102,1202,1302,1402,1502,1602,1702</EventID>
  </DataSource>
  <WriteAction>
    <AlertSeverity>Warning</AlertSeverity>
  </WriteAction>
</Rule>

<Rule ID="RevealAI.Warning.Alert">
  <DataSource>
    <EventLog>Application</EventLog>
    <EventSource>RevealAI-Monitor</EventSource>
    <EventID>2002,2102,2202</EventID>
  </DataSource>
  <WriteAction>
    <AlertSeverity>Warning</AlertSeverity>
  </WriteAction>
</Rule>
```

### Test SCOM Integration

```bash
# Test event writing
python relativity-one/scripts/scom_integration.py --test

# Verify in Event Viewer
# Application Log → Filter by Source: RelativityOne-Monitor
```

---

## Recommended Polling Schedule

### RelativityOne

```bash
# Critical - every minute
* * * * * python /opt/monitoring/relativity-one/scripts/telemetry_agent_monitor.py --config config.json
* * * * * python /opt/monitoring/relativity-one/scripts/billing_agent_monitor.py --config config.json
* * * * * python /opt/monitoring/relativity-one/scripts/alert_manager_monitor.py --config config.json
* * * * * python /opt/monitoring/relativity-one/scripts/worker_health_monitor.py --config config.json

# High - every 5 minutes
*/5 * * * * python /opt/monitoring/relativity-one/scripts/job_queue_monitor.py --config config.json
*/5 * * * * python /opt/monitoring/relativity-one/scripts/security_audit_monitor.py --config config.json
*/5 * * * * python /opt/monitoring/relativity-one/scripts/air_job_monitor.py --config config.json
```

### Reveal AI

```bash
# Critical - every minute
* * * * * python /opt/monitoring/reveal-ai/scripts/reveal_api_health_monitor.py --config config.json

# High - every 5 minutes
*/5 * * * * python /opt/monitoring/reveal-ai/scripts/reveal_job_monitor.py --config config.json

# Medium - every 15 minutes
*/15 * * * * python /opt/monitoring/reveal-ai/scripts/reveal_export_monitor.py --config config.json
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [relativity-one/eDiscovery_Alerting_Framework.md](relativity-one/eDiscovery_Alerting_Framework.md) | RelativityOne architecture & design |
| [relativity-one/aiR_Alerting_Framework.md](relativity-one/aiR_Alerting_Framework.md) | aiR for Review & Privilege monitoring |
| [relativity-one/runbooks/README.md](relativity-one/runbooks/README.md) | RelativityOne runbook index |
| [relativity-one/scripts/README.md](relativity-one/scripts/README.md) | RelativityOne script documentation |
| [reveal-ai/Reveal_AI_Alerting_Framework.md](reveal-ai/Reveal_AI_Alerting_Framework.md) | Reveal AI architecture |
| [reveal-ai/runbooks/README.md](reveal-ai/runbooks/README.md) | Reveal AI runbook index |
| [reveal-ai/scripts/README.md](reveal-ai/scripts/README.md) | Reveal AI script documentation |

---

## Requirements

- Python 3.8+
- `requests` library
- `python-dateutil` library
- `pywin32` library (Windows only, for SCOM integration)

```bash
pip install requests python-dateutil

# For SCOM integration on Windows:
pip install pywin32
```

---

## Security Considerations

- Store credentials in environment variables or secure vault
- Use OAuth/service accounts (not personal credentials)
- Restrict config file access: `chmod 600 config.json`
- Use HTTPS for all webhook URLs
- Rotate credentials regularly
- Config files are excluded from git via `.gitignore`

---

## Platform Comparison

| Capability | RelativityOne | Reveal AI |
|------------|---------------|-----------|
| Webhooks | ✅ Supported | ❌ Not available |
| Native SIEM Connectors | ✅ Splunk, Sentinel | ❌ Not available |
| Audit API | ✅ Dedicated API | ❌ Export only |
| Public Status Page | ✅ Available | ❌ Not available |
| Rate Limits | ✅ Documented | ❌ Not documented |
| Development Effort | ~8-16 hours | ~40-60 hours |

---

## Support

**RelativityOne:** support@relativity.com
**Reveal AI:** support@revealdata.com

For framework issues:
- Open a GitHub issue
- Contact the repository maintainer
