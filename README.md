# RelativityOne Alerting & Monitoring Framework

A comprehensive alerting and monitoring solution for RelativityOne eDiscovery environments. This repository provides enterprise-grade operational runbooks and automated monitoring scripts to ensure platform reliability, security, and compliance.

## Overview

This framework addresses a critical gap in RelativityOne's native capabilities: **proactive, external monitoring**. While RelativityOne provides some built-in alerting, this solution adds:

- **External monitoring** that works even when platform alerting fails
- **Proactive detection** of issues before users are impacted
- **Comprehensive runbooks** for consistent incident response
- **Multi-channel notifications** (Email, Slack, PagerDuty, Teams, Webhooks)

### Critical Alert: Telemetry Agent

> ⚠️ **If the Telemetry Metrics Transmission Agent fails, users will be logged out of RelativityOne.** This framework includes dedicated monitoring to prevent this business-critical failure.

---

## Repository Structure

```
LPT_Alerting_Monitoring/
├── README.md                           # This file
├── eDiscovery_Alerting_Framework.md    # Architecture & design document
├── runbooks/
│   ├── README.md                       # Runbook index & alert mappings
│   └── RUNBOOK-001 through RUNBOOK-018 # Operational runbooks
└── scripts/
    ├── README.md                       # Script documentation & deployment
    ├── config.example.json             # Configuration template
    └── *.py                            # Monitoring scripts
```

---

## Monitoring Scripts

### Script Summary

| Script | Purpose | Polling | Priority |
|--------|---------|---------|----------|
| `telemetry_agent_monitor.py` | Telemetry agent (prevents user logout) | 1 min | **CRITICAL** |
| `billing_agent_monitor.py` | Single-instance billing agent (compliance) | 1 min | **CRITICAL** |
| `alert_manager_monitor.py` | Meta-monitoring (native platform alerts) | 1 min | **CRITICAL** |
| `worker_health_monitor.py` | All worker servers & agents | 1 min | **CRITICAL** |
| `job_queue_monitor.py` | Processing/Production/Imaging queues | 5 min | HIGH |
| `security_audit_monitor.py` | Brute force, exports, lockbox, permissions | 5 min | HIGH |

### Features (All Scripts)

| Feature | Description |
|---------|-------------|
| **OAuth 2.0 Authentication** | Secure bearer token authentication with RelativityOne |
| **Multi-Channel Alerts** | Email, Slack, PagerDuty, Microsoft Teams, Generic Webhooks |
| **State Tracking** | Prevents duplicate alerts, tracks state changes |
| **Exit Codes** | Integration with monitoring systems (0=OK, 1=WARN, 2=HIGH, 3=CRITICAL) |
| **Dry Run Mode** | Test without sending alerts |
| **Configurable Thresholds** | Customize alert sensitivity |

### Quick Start

```bash
# 1. Install dependencies
pip install requests python-dateutil

# 2. Configure
cp scripts/config.example.json scripts/config.json
# Edit config.json with your RelativityOne credentials

# 3. Test (dry run)
python scripts/telemetry_agent_monitor.py --config scripts/config.json --dry-run --verbose

# 4. Run for real
python scripts/telemetry_agent_monitor.py --config scripts/config.json
```

### Deployment Options

See [scripts/README.md](scripts/README.md) for detailed deployment guides including:
- Linux cron scheduling
- Windows Task Scheduler
- Docker / Docker Compose
- Kubernetes CronJobs

---

## Operational Runbooks

### Runbook Summary

| ID | Runbook | Severity | Primary Alert Conditions |
|----|---------|----------|--------------------------|
| [001](runbooks/RUNBOOK-001_Processing_Job_Failures.md) | Processing Job Failures | CRITICAL | Job errors, environment errors, data source errors |
| [002](runbooks/RUNBOOK-002_Production_Job_Failures.md) | Production Job Failures | CRITICAL | Production errors, numbering conflicts, stuck jobs |
| [003](runbooks/RUNBOOK-003_Imaging_Job_Failures.md) | Imaging Job Failures | CRITICAL/HIGH | Imaging errors, document-level failures |
| [004](runbooks/RUNBOOK-004_Security_Alerts.md) | Security Alerts | CRITICAL/HIGH | Brute force, failed logins, permission changes |
| [005](runbooks/RUNBOOK-005_Integration_Points_Failures.md) | Integration Points Failures | CRITICAL/HIGH | Job failures, validation errors, sync issues |
| [006](runbooks/RUNBOOK-006_Agent_Worker_Health.md) | Agent/Worker Health | CRITICAL/HIGH | Agent disabled, worker unresponsive |
| [007](runbooks/RUNBOOK-007_dtSearch_Index_Issues.md) | dtSearch Index Issues | HIGH/MEDIUM | Build errors, fragmentation |
| [008](runbooks/RUNBOOK-008_Structured_Analytics_Failures.md) | Structured Analytics Failures | CRITICAL/HIGH | Analytics job failures, stuck operations |
| [009](runbooks/RUNBOOK-009_Audit_Compliance_Monitoring.md) | Audit & Compliance | CRITICAL/HIGH | Data exfiltration, suspicious activity |
| [010](runbooks/RUNBOOK-010_Mass_Operations.md) | Mass Operations | CRITICAL/HIGH | Mass delete, bulk edits, legal hold impact |
| [011](runbooks/RUNBOOK-011_OCR_Job_Failures.md) | OCR Job Failures | HIGH/MEDIUM | OCR errors, quality issues |
| [012](runbooks/RUNBOOK-012_Branding_Job_Failures.md) | Branding Job Failures | HIGH/MEDIUM | Branding errors, template issues |
| [013](runbooks/RUNBOOK-013_Script_Execution_Issues.md) | Script Execution Issues | HIGH/MEDIUM | Script failures, performance, unauthorized |
| [014](runbooks/RUNBOOK-014_Workspace_Health.md) | Workspace Health | HIGH/MEDIUM | Workspace unavailable, capacity issues |
| [015](runbooks/RUNBOOK-015_Data_Export_Transfer.md) | Data Export & Transfer | CRITICAL/HIGH | Large exports, potential exfiltration |
| [016](runbooks/RUNBOOK-016_Infrastructure_Performance.md) | Infrastructure Performance | CRITICAL/HIGH | SQL latency, worker resources, API issues |
| [017](runbooks/RUNBOOK-017_Scheduled_Jobs.md) | Scheduled Jobs | CRITICAL/HIGH | Stopped jobs, recurring failures |
| [018](runbooks/RUNBOOK-018_Telemetry_Agent_Critical.md) | **Telemetry Agent** | **CRITICAL** | **Agent disabled/stale = USER LOGOUT** |

### Coverage Matrix

| Area | Runbook(s) | Coverage |
|------|------------|----------|
| **Processing Pipeline** | 001, 003, 011 | Processing, Imaging, OCR |
| **Production Pipeline** | 002, 012 | Productions, Branding |
| **Analytics** | 007, 008 | dtSearch, Structured Analytics |
| **Security** | 004, 009, 015 | Auth, Audit, Data Loss Prevention |
| **Integration** | 005, 017 | Integration Points, Scheduled Jobs |
| **Infrastructure** | 006, 014, 016, 018 | Agents, Workers, Performance, Telemetry |
| **Operations** | 010, 013 | Mass Operations, Scripts |

### Response SLAs

| Severity | Response Time | Examples |
|----------|---------------|----------|
| **CRITICAL** | Immediate (15 min) | Worker down, data breach, telemetry failure, legal hold |
| **HIGH** | 1 hour | Job failures, security events |
| **MEDIUM** | 4 hours | Performance issues, warnings |
| **LOW** | Next business day | Monitoring, trends |

---

## Alert Thresholds

### Agent Monitors (Telemetry, Billing, Alert Manager)

| Level | Last Activity Age | Action |
|-------|-------------------|--------|
| OK | < 30 minutes | No alert |
| WARNING | 30-60 minutes | Monitor closely |
| HIGH | 60-120 minutes | Investigate |
| CRITICAL | > 120 minutes | Immediate action |

**Also CRITICAL if:** Agent disabled, not responding, or not found

### Job Queue Monitor

| Level | Failed Jobs | Stuck Jobs |
|-------|-------------|------------|
| WARNING | 1-2 failed | > 4 hours |
| HIGH | 3-4 failed | > 8 hours |
| CRITICAL | 5+ failed | > 24 hours |

### Security Audit Monitor

| Event Type | Warning | High | Critical |
|------------|---------|------|----------|
| Failed Logins | 5+ | 20+ | 50+ (brute force) |
| Large Exports | 1,000+ docs | 5,000+ docs | 10,000+ docs |
| Lockbox Changes | - | - | Any change |
| After-Hours Exports | - | Any | - |

---

## Configuration

### Environment Variables (Recommended for Production)

```bash
# Required - RelativityOne Connection
export RELATIVITY_HOST="https://your-instance.relativity.one"
export RELATIVITY_CLIENT_ID="your-client-id"
export RELATIVITY_CLIENT_SECRET="your-client-secret"
export RELATIVITY_AUTH_METHOD="bearer"

# Notifications
export SLACK_ENABLED="true"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

export PAGERDUTY_ENABLED="true"
export PAGERDUTY_ROUTING_KEY="your-routing-key"

export TEAMS_ENABLED="true"
export TEAMS_WEBHOOK_URL="https://outlook.office.com/webhook/YOUR/URL"
```

### Configuration File

Copy and customize `scripts/config.example.json`:

```json
{
    "relativity_host": "https://your-instance.relativity.one",
    "client_id": "your-oauth-client-id",
    "client_secret": "your-oauth-client-secret",
    "auth_method": "bearer",
    "notifications": {
        "slack_enabled": true,
        "slack_webhook_url": "https://hooks.slack.com/...",
        "pagerduty_enabled": true,
        "pagerduty_routing_key": "your-key"
    }
}
```

---

## API Permissions Required

| Script | Required Permissions |
|--------|---------------------|
| All agent monitors | View agents (Agent Manager) |
| Worker Health | View resource servers |
| Job Queue | Query processing/production/imaging objects |
| Security Audit | Query audit records, Audit API access |

---

## Recommended Polling Schedule

```bash
# Critical agents - every minute
* * * * * python /opt/monitoring/telemetry_agent_monitor.py --config /opt/monitoring/config.json
* * * * * python /opt/monitoring/billing_agent_monitor.py --config /opt/monitoring/config.json
* * * * * python /opt/monitoring/alert_manager_monitor.py --config /opt/monitoring/config.json
* * * * * python /opt/monitoring/worker_health_monitor.py --config /opt/monitoring/config.json

# Job queues & security - every 5 minutes
*/5 * * * * python /opt/monitoring/job_queue_monitor.py --config /opt/monitoring/config.json
*/5 * * * * python /opt/monitoring/security_audit_monitor.py --config /opt/monitoring/config.json
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [eDiscovery_Alerting_Framework.md](eDiscovery_Alerting_Framework.md) | Architecture, design decisions, platform comparison |
| [runbooks/README.md](runbooks/README.md) | Runbook index, alert-to-runbook mappings, SLAs |
| [scripts/README.md](scripts/README.md) | Script documentation, deployment guides, troubleshooting |

---

## Requirements

- Python 3.8+
- `requests` library
- `python-dateutil` library

```bash
pip install requests python-dateutil
```

---

## Security Considerations

- Store credentials in environment variables or secure vault (not in code)
- Use OAuth client credentials (not username/password) when possible
- Restrict access to configuration files: `chmod 600 config.json`
- Use HTTPS for all webhook URLs
- Rotate credentials regularly
- The `config.json` file is excluded from git via `.gitignore`

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## License

Internal use only. Contact repository owner for licensing information.

---

## Support

For issues or questions:
- Open a GitHub issue
- Contact the repository maintainer
