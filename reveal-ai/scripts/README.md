# Reveal AI Monitoring Scripts

## Overview

These scripts provide automated monitoring for Reveal AI eDiscovery environments. Unlike RelativityOne, Reveal AI **does not support webhooks or native SIEM connectors**, so all monitoring uses a polling-based approach.

> **Note:** Comprehensive Reveal AI API documentation requires authenticated customer access. These scripts are based on publicly available information and may require adjustment for your specific deployment.

---

## Scripts Summary

| Script | Purpose | Polling | Priority |
|--------|---------|---------|----------|
| `reveal_api_health_monitor.py` | NIA + REST API availability | 1 min | **CRITICAL** |
| `reveal_job_monitor.py` | Job failures (Status=4) and stuck jobs | 5 min | **CRITICAL** |
| `reveal_export_monitor.py` | Large exports, after-hours activity | 15 min | HIGH |

---

## Quick Start

```bash
# 1. Install dependencies
pip install requests python-dateutil

# 2. Configure
cp config.example.json config.json
# Edit config.json with your Reveal AI credentials

# 3. Test (dry run)
python reveal_api_health_monitor.py --config config.json --dry-run --verbose
python reveal_job_monitor.py --config config.json --dry-run --verbose
python reveal_export_monitor.py --config config.json --dry-run --verbose

# 4. Run for real
python reveal_api_health_monitor.py --config config.json
python reveal_job_monitor.py --config config.json
python reveal_export_monitor.py --config config.json
```

---

## API Health Monitor

**Script:** `reveal_api_health_monitor.py`

Monitors the health of Reveal AI APIs:
- NIA API (`/nia/version`)
- REST API v2 health endpoint

### Alert Thresholds

| Level | Condition |
|-------|-----------|
| OK | All APIs responding, response time < 2s |
| WARNING | Response time 2-5s |
| HIGH | Response time 5-10s |
| CRITICAL | API down, timeout, or response > 10s |

### Configuration Options

```json
{
    "reveal_host": "https://your-instance.revealdata.com",
    "nia_host": "http://your-nia-server",
    "nia_port": 5566,
    "timeout_seconds": 10,
    "response_time_warning_ms": 2000,
    "response_time_high_ms": 5000,
    "response_time_critical_ms": 10000
}
```

---

## Job Monitor

**Script:** `reveal_job_monitor.py`

Monitors the NIA job queue for failures and stuck jobs using the 12-state status model.

### Job Status Codes

| Code | Status | Alert |
|------|--------|-------|
| 0 | Created | - |
| 1 | Submitted | - |
| 2 | InProcess | Monitor duration |
| 3 | Complete | - |
| **4** | **Error** | **CRITICAL** |
| 5 | Cancelled | WARNING |
| 6 | CancelPending | - |
| **7** | **Deleted** | **AUDIT** |
| 8 | Modified | - |
| 9-12 | Processing/Deletion | Monitor |

### Alert Thresholds

**Failed Jobs (Status=4):**

| Level | Count |
|-------|-------|
| WARNING | 1-2 failed |
| HIGH | 3-4 failed |
| CRITICAL | 5+ failed |

**Stuck Jobs (Status=2 InProcess):**

| Level | Duration |
|-------|----------|
| WARNING | > 4 hours |
| HIGH | > 8 hours |
| CRITICAL | > 24 hours |

### Configuration Options

```json
{
    "lookback_hours": 24,
    "stuck_job_warning_hours": 4,
    "stuck_job_high_hours": 8,
    "stuck_job_critical_hours": 24,
    "failed_jobs_warning": 1,
    "failed_jobs_high": 3,
    "failed_jobs_critical": 5
}
```

---

## Export Monitor

**Script:** `reveal_export_monitor.py`

Monitors export and production jobs for security concerns:
- Large exports (potential data exfiltration)
- After-hours export activity
- Production exports to external destinations

### Alert Thresholds

| Level | Document Count |
|-------|----------------|
| WARNING | > 1,000 docs |
| HIGH | > 5,000 docs |
| CRITICAL | > 10,000 docs |

**Also HIGH if:** Any export outside business hours (configurable)

### Configuration Options

```json
{
    "export_docs_warning": 1000,
    "export_docs_high": 5000,
    "export_docs_critical": 10000,
    "business_hours_start": 7,
    "business_hours_end": 19,
    "alert_after_hours": true
}
```

---

## Configuration

### Environment Variables

```bash
# Required - Reveal AI Connection
export REVEAL_HOST="https://your-instance.revealdata.com"
export REVEAL_NIA_HOST="http://your-nia-server"
export REVEAL_NIA_PORT="5566"
export REVEAL_USERNAME="your-username"
export REVEAL_PASSWORD="your-password"

# Notifications
export SLACK_ENABLED="true"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

export PAGERDUTY_ENABLED="true"
export PAGERDUTY_ROUTING_KEY="your-routing-key"

export TEAMS_ENABLED="true"
export TEAMS_WEBHOOK_URL="https://outlook.office.com/webhook/YOUR/URL"
```

### Configuration File

Copy and customize `config.example.json`:

```bash
cp config.example.json config.json
# Edit config.json with your values
```

---

## Scheduling

### Linux (cron)

```bash
# API Health - every minute
* * * * * /usr/bin/python3 /opt/monitoring/reveal_api_health_monitor.py --config /opt/monitoring/config.json >> /var/log/reveal_monitor.log 2>&1

# Job Monitor - every 5 minutes
*/5 * * * * /usr/bin/python3 /opt/monitoring/reveal_job_monitor.py --config /opt/monitoring/config.json >> /var/log/reveal_monitor.log 2>&1

# Export Monitor - every 15 minutes
*/15 * * * * /usr/bin/python3 /opt/monitoring/reveal_export_monitor.py --config /opt/monitoring/config.json >> /var/log/reveal_monitor.log 2>&1
```

### Docker Compose

```yaml
version: '3'
services:
  reveal-api-health:
    build: .
    command: sh -c "while true; do python reveal_api_health_monitor.py --config config.json; sleep 60; done"
    env_file: .env
    restart: always

  reveal-job-monitor:
    build: .
    command: sh -c "while true; do python reveal_job_monitor.py --config config.json; sleep 300; done"
    env_file: .env
    restart: always

  reveal-export-monitor:
    build: .
    command: sh -c "while true; do python reveal_export_monitor.py --config config.json; sleep 900; done"
    env_file: .env
    restart: always
```

---

## Exit Codes

| Code | Level | Meaning |
|------|-------|---------|
| 0 | OK | All healthy |
| 1 | WARNING | Minor concern |
| 2 | HIGH | Significant issue |
| 3 | CRITICAL | Immediate action required |

---

## Notification Channels

All scripts support:

| Channel | Use Case |
|---------|----------|
| **Email** | Standard alerting |
| **Slack** | Team chat integration |
| **PagerDuty** | On-call alerting with escalation |
| **Microsoft Teams** | Enterprise chat |
| **Generic Webhook** | Custom integrations (Datadog, Splunk, etc.) |

---

## Troubleshooting

### Authentication Errors
```
ERROR: Failed to get session token
```
- Verify username and password are correct
- Check that user has API access permissions
- Ensure host URL is correct

### NIA API Connection Failed
```
ERROR: Failed to query NIA API
```
- Verify NIA host and port are correct
- Check network connectivity to NIA server
- Verify firewall allows connection

### No Jobs Found
```
INFO: Retrieved 0 jobs
```
- Verify API credentials have permission to view jobs
- Check if NIA API endpoint is correct
- May require vendor documentation for your deployment

---

## API Reference

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

### NIA API

```bash
# Health check
curl "http://[server]:5566/nia/version"

# Get jobs
curl "http://[server]:5566/nia/jobs"
```

---

## Related Documentation

- [Reveal AI Alerting Framework](../Reveal_AI_Alerting_Framework.md)
- [Reveal AI Runbooks](../runbooks/README.md)
- [Main Repository README](../../README.md)

---

## Security Considerations

- Store credentials in environment variables or secure vault
- Use HTTPS for all REST API calls
- Restrict access to configuration files: `chmod 600 config.json`
- Rotate credentials regularly
- The config.json file is excluded from git via .gitignore

---

## SCOM Integration

All Reveal AI monitoring scripts support Microsoft SCOM (System Center Operations Manager) integration via Windows Event Log.

**Enable SCOM Integration:**

```json
{
    "scom_enabled": true,
    "scom_fallback_file": "/var/log/scom_events.json"
}
```

**Event Sources:**
- `RevealAI-Monitor` - All Reveal AI events

**Event ID Ranges:**

| Monitor | Event IDs | Description |
|---------|-----------|-------------|
| API Health | 2000-2004 | OK, INFO, WARNING, HIGH, CRITICAL |
| Job Monitor | 2100-2104 | OK, INFO, WARNING, HIGH, CRITICAL |
| Export Monitor | 2200-2204 | OK, INFO, WARNING, HIGH, CRITICAL |

**Setup (Run as Administrator):**

```powershell
# Register event source
if (-not [System.Diagnostics.EventLog]::SourceExists("RevealAI-Monitor")) {
    [System.Diagnostics.EventLog]::CreateEventSource("RevealAI-Monitor", "Application")
}
```

**Requirements:**
```bash
pip install pywin32  # Windows only
```

---

## Vendor Contact

For API documentation and support:
- **Reveal Data Support:** support@revealdata.com
- **Trust Center:** security.revealdata.com
