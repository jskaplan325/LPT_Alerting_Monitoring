# RelativityOne Monitoring Scripts

## Telemetry Agent Monitor

**CRITICAL MONITORING SCRIPT**

The `telemetry_agent_monitor.py` script monitors the Telemetry Metrics Transmission Agent. This is critical because **if this agent fails, users will be logged out of RelativityOne**.

### Quick Start

```bash
# 1. Install dependencies
pip install requests python-dateutil

# 2. Copy and configure
cp config.example.json config.json
# Edit config.json with your credentials

# 3. Test (dry run)
python telemetry_agent_monitor.py --config config.json --dry-run --verbose

# 4. Run for real
python telemetry_agent_monitor.py --config config.json
```

### Installation

#### Requirements

```bash
pip install requests python-dateutil
```

#### Configuration Options

**Option 1: Environment Variables (Recommended for Production)**

```bash
# Required - RelativityOne Connection
export RELATIVITY_HOST="https://your-instance.relativity.one"
export RELATIVITY_CLIENT_ID="your-client-id"
export RELATIVITY_CLIENT_SECRET="your-client-secret"
export RELATIVITY_AUTH_METHOD="bearer"

# Optional - Notification Settings
export EMAIL_ENABLED="true"
export SMTP_SERVER="smtp.office365.com"
export SMTP_PORT="587"
export SMTP_USERNAME="alerts@company.com"
export SMTP_PASSWORD="your-password"
export EMAIL_FROM="alerts@company.com"
export EMAIL_TO="oncall@company.com,admin@company.com"

export SLACK_ENABLED="true"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

export PAGERDUTY_ENABLED="true"
export PAGERDUTY_ROUTING_KEY="your-routing-key"

export TEAMS_ENABLED="true"
export TEAMS_WEBHOOK_URL="https://outlook.office.com/webhook/YOUR/URL"
```

**Option 2: Configuration File**

```bash
cp config.example.json config.json
# Edit config.json with your values
python telemetry_agent_monitor.py --config config.json
```

### Scheduling

#### Linux (cron)

Run every minute:

```bash
# Edit crontab
crontab -e

# Add this line (adjust paths):
* * * * * /usr/bin/python3 /opt/monitoring/telemetry_agent_monitor.py --config /opt/monitoring/config.json >> /var/log/telemetry_monitor.log 2>&1
```

#### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily, repeat every 1 minute
4. Action: Start a program
   - Program: `python`
   - Arguments: `C:\monitoring\telemetry_agent_monitor.py --config C:\monitoring\config.json`
5. Enable "Run whether user is logged on or not"

#### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY telemetry_agent_monitor.py .
COPY config.json .

CMD ["python", "telemetry_agent_monitor.py", "--config", "config.json"]
```

```yaml
# docker-compose.yml
version: '3'
services:
  telemetry-monitor:
    build: .
    environment:
      - RELATIVITY_HOST=${RELATIVITY_HOST}
      - RELATIVITY_CLIENT_ID=${RELATIVITY_CLIENT_ID}
      - RELATIVITY_CLIENT_SECRET=${RELATIVITY_CLIENT_SECRET}
    restart: always
    # Run every minute using a simple loop
    command: >
      sh -c "while true; do
        python telemetry_agent_monitor.py --config config.json;
        sleep 60;
      done"
```

#### Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: telemetry-agent-monitor
spec:
  schedule: "* * * * *"  # Every minute
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: monitor
            image: your-registry/telemetry-monitor:latest
            envFrom:
            - secretRef:
                name: relativity-credentials
          restartPolicy: OnFailure
```

### Alert Thresholds

| Level | Last Activity Age | Action |
|-------|-------------------|--------|
| OK | < 30 minutes | No alert |
| WARNING | 30-60 minutes | Monitor closely |
| HIGH | 60-120 minutes | Investigate |
| CRITICAL | > 120 minutes | Immediate action |

Also CRITICAL if:
- Agent is disabled
- Agent status is "Not Responding"
- Agent not found

### Notification Channels

The script supports multiple notification channels:

| Channel | Use Case |
|---------|----------|
| **Email** | Standard alerting |
| **Slack** | Team chat integration |
| **PagerDuty** | On-call alerting with escalation |
| **Microsoft Teams** | Enterprise chat |
| **Generic Webhook** | Custom integrations (Datadog, Splunk, etc.) |

### Exit Codes

| Code | Level | Meaning |
|------|-------|---------|
| 0 | OK | Agent healthy |
| 1 | WARNING | Minor concern |
| 2 | HIGH | Significant issue |
| 3 | CRITICAL | Immediate action required |

### Command Line Options

```
usage: telemetry_agent_monitor.py [-h] [--config CONFIG] [--dry-run] [--verbose]

Monitor RelativityOne Telemetry Agent

optional arguments:
  -h, --help       show this help message and exit
  --config CONFIG  Path to JSON config file
  --dry-run        Check only, don't send alerts
  --verbose, -v    Verbose output
```

### Troubleshooting

**Authentication Errors:**
```
ERROR: Failed to get bearer token
```
- Verify client_id and client_secret are correct
- Check that OAuth app has correct permissions in RelativityOne
- Ensure the host URL is correct (no trailing slash)

**Agent Not Found:**
```
CRITICAL: Telemetry agent not found!
```
- Verify "agent_name_contains" matches your agent name
- Check API permissions for viewing agents

**Connection Errors:**
```
ERROR: Failed to query agents
```
- Check network connectivity to RelativityOne
- Verify firewall allows outbound HTTPS
- Check if host URL is correct

### API Permissions Required

The OAuth client or user account needs permissions to:
- View agents (`Agent Manager` or similar permission)
- Access the Agents API endpoint

### Security Considerations

- Store credentials in environment variables or secure vault (not in code)
- Use OAuth client credentials (not username/password) when possible
- Restrict access to configuration files: `chmod 600 config.json`
- Use HTTPS for all webhook URLs
- Rotate credentials regularly

### Related Documentation

- [RUNBOOK-018: Telemetry Agent Critical](../runbooks/RUNBOOK-018_Telemetry_Agent_Critical.md)
- [eDiscovery Alerting Framework](../eDiscovery_Alerting_Framework.md)

---

## Billing Agent Monitor

**CRITICAL SINGLE-INSTANCE AGENT**

The `billing_agent_monitor.py` script monitors the Billing Agent responsible for usage metering and compliance reporting.

### Quick Start

```bash
python billing_agent_monitor.py --config config.json --dry-run --verbose
python billing_agent_monitor.py --config config.json
```

### Alert Thresholds

| Level | Last Activity Age | Action |
|-------|-------------------|--------|
| OK | < 60 minutes | No alert |
| WARNING | 60-120 minutes | Monitor closely |
| HIGH | 120-240 minutes | Investigate |
| CRITICAL | > 240 minutes | Immediate action |

Also CRITICAL if agent is disabled or not responding.

### Related Runbook

- [RUNBOOK-006: Agent/Worker Health](../runbooks/RUNBOOK-006_Agent_Worker_Health.md)

---

## Worker Health Monitor

**INFRASTRUCTURE MONITORING**

The `worker_health_monitor.py` script monitors all worker services and agents across the RelativityOne environment. If workers go down, ALL job processing stops.

### Quick Start

```bash
python worker_health_monitor.py --config config.json --dry-run --verbose
python worker_health_monitor.py --config config.json
```

### What It Monitors

- Resource server status (worker servers)
- Agent enabled/disabled state
- Agent response status
- Overall worker pool health

### Alert Thresholds

| Level | Condition |
|-------|-----------|
| OK | All workers healthy |
| WARNING | 1 unhealthy worker/agent |
| HIGH | 2 unhealthy workers/agents |
| CRITICAL | 3+ unhealthy OR no healthy servers |

### Related Runbook

- [RUNBOOK-006: Agent/Worker Health](../runbooks/RUNBOOK-006_Agent_Worker_Health.md)

---

## Job Queue Monitor

**PROACTIVE FAILURE DETECTION**

The `job_queue_monitor.py` script monitors Processing, Production, and Imaging job queues for failures and stuck jobs.

### Quick Start

```bash
python job_queue_monitor.py --config config.json --dry-run --verbose
python job_queue_monitor.py --config config.json
```

### What It Monitors

- Processing jobs (errors, stuck states)
- Production jobs (failures, numbering issues)
- Imaging jobs (errors, document failures)
- Job duration (stuck job detection)

### Alert Thresholds

**Failed Jobs:**

| Level | Failed Jobs |
|-------|-------------|
| WARNING | 1-2 failed |
| HIGH | 3-4 failed |
| CRITICAL | 5+ failed |

**Stuck Jobs:**

| Level | Hours Running |
|-------|---------------|
| WARNING | > 4 hours |
| HIGH | > 8 hours |
| CRITICAL | > 24 hours |

### Configuration Options

```json
{
    "check_processing": true,
    "check_production": true,
    "check_imaging": true,
    "failed_jobs_warning": 1,
    "failed_jobs_high": 3,
    "failed_jobs_critical": 5,
    "stuck_job_hours_warning": 4,
    "stuck_job_hours_high": 8,
    "stuck_job_hours_critical": 24,
    "lookback_hours": 24
}
```

### Related Runbooks

- [RUNBOOK-001: Processing Job Failures](../runbooks/RUNBOOK-001_Processing_Job_Failures.md)
- [RUNBOOK-002: Production Job Failures](../runbooks/RUNBOOK-002_Production_Job_Failures.md)
- [RUNBOOK-003: Imaging Job Failures](../runbooks/RUNBOOK-003_Imaging_Job_Failures.md)

---

## Security Audit Monitor

**COMPLIANCE & SECURITY MONITORING**

The `security_audit_monitor.py` script monitors the Audit API for security-relevant events including brute force attacks, permission changes, large exports, and after-hours activity.

### Quick Start

```bash
python security_audit_monitor.py --config config.json --dry-run --verbose
python security_audit_monitor.py --config config.json
```

### What It Monitors

| Event Type | Alert Trigger |
|------------|---------------|
| Failed Logins | 5+ (WARNING), 20+ (HIGH), 50+ (CRITICAL) |
| Large Exports | 1000+ docs (WARNING), 5000+ (HIGH), 10000+ (CRITICAL) |
| Lockbox Changes | Any modification (CRITICAL) |
| Permission Changes | 5+ changes (WARNING) |
| After-Hours Exports | Any export outside business hours (HIGH) |
| Mass Operations | Mass delete/edit/move (HIGH) |

### Configuration Options

```json
{
    "lookback_minutes": 15,
    "failed_login_warning": 5,
    "failed_login_high": 20,
    "failed_login_critical": 50,
    "export_docs_warning": 1000,
    "export_docs_high": 5000,
    "export_docs_critical": 10000,
    "business_hours_start": 7,
    "business_hours_end": 19,
    "alert_after_hours_exports": true
}
```

### Recommended Polling Frequency

- **Every 5-15 minutes** for security events
- More frequent polling for high-security environments

### Related Runbooks

- [RUNBOOK-004: Security Alerts](../runbooks/RUNBOOK-004_Security_Alerts.md)
- [RUNBOOK-009: Audit & Compliance Monitoring](../runbooks/RUNBOOK-009_Audit_Compliance_Monitoring.md)
- [RUNBOOK-015: Data Export & Transfer](../runbooks/RUNBOOK-015_Data_Export_Transfer.md)

---

## Alert Manager Monitor

**META-MONITORING - MONITOR THE MONITORING**

The `alert_manager_monitor.py` script monitors the Alert Manager Agent - the agent responsible for native RelativityOne alerting. This is "meta-monitoring" - if this agent fails, native platform alerts stop working.

### Quick Start

```bash
python alert_manager_monitor.py --config config.json --dry-run --verbose
python alert_manager_monitor.py --config config.json
```

### Why This Matters

If the Alert Manager Agent fails:
- Native RelativityOne alerts will NOT be sent
- You won't know about problems unless you have external monitoring
- This script provides that external monitoring layer

### Alert Thresholds

| Level | Last Activity Age | Action |
|-------|-------------------|--------|
| OK | < 30 minutes | No alert |
| WARNING | 30-60 minutes | Monitor closely |
| HIGH | 60-120 minutes | Investigate |
| CRITICAL | > 120 minutes | Immediate action |

Also CRITICAL if agent is disabled or not responding.

### Related Runbook

- [RUNBOOK-006: Agent/Worker Health](../runbooks/RUNBOOK-006_Agent_Worker_Health.md)

---

## Complete Monitoring Suite

### Recommended Polling Schedule

| Script | Frequency | Priority |
|--------|-----------|----------|
| `telemetry_agent_monitor.py` | Every 1 minute | CRITICAL |
| `billing_agent_monitor.py` | Every 1 minute | CRITICAL |
| `alert_manager_monitor.py` | Every 1 minute | CRITICAL |
| `worker_health_monitor.py` | Every 1 minute | CRITICAL |
| `job_queue_monitor.py` | Every 5 minutes | HIGH |
| `security_audit_monitor.py` | Every 5-15 minutes | HIGH |

### Cron Configuration (All Scripts)

```bash
# Critical agents - every minute
* * * * * /usr/bin/python3 /opt/monitoring/telemetry_agent_monitor.py --config /opt/monitoring/config.json >> /var/log/relativity_monitor.log 2>&1
* * * * * /usr/bin/python3 /opt/monitoring/billing_agent_monitor.py --config /opt/monitoring/config.json >> /var/log/relativity_monitor.log 2>&1
* * * * * /usr/bin/python3 /opt/monitoring/alert_manager_monitor.py --config /opt/monitoring/config.json >> /var/log/relativity_monitor.log 2>&1
* * * * * /usr/bin/python3 /opt/monitoring/worker_health_monitor.py --config /opt/monitoring/config.json >> /var/log/relativity_monitor.log 2>&1

# Job queues - every 5 minutes
*/5 * * * * /usr/bin/python3 /opt/monitoring/job_queue_monitor.py --config /opt/monitoring/config.json >> /var/log/relativity_monitor.log 2>&1

# Security audit - every 5 minutes
*/5 * * * * /usr/bin/python3 /opt/monitoring/security_audit_monitor.py --config /opt/monitoring/config.json >> /var/log/relativity_monitor.log 2>&1
```

### Docker Compose (All Scripts)

```yaml
version: '3'
services:
  telemetry-monitor:
    build: .
    command: sh -c "while true; do python telemetry_agent_monitor.py --config config.json; sleep 60; done"
    env_file: .env
    restart: always

  billing-monitor:
    build: .
    command: sh -c "while true; do python billing_agent_monitor.py --config config.json; sleep 60; done"
    env_file: .env
    restart: always

  alert-manager-monitor:
    build: .
    command: sh -c "while true; do python alert_manager_monitor.py --config config.json; sleep 60; done"
    env_file: .env
    restart: always

  worker-health-monitor:
    build: .
    command: sh -c "while true; do python worker_health_monitor.py --config config.json; sleep 60; done"
    env_file: .env
    restart: always

  job-queue-monitor:
    build: .
    command: sh -c "while true; do python job_queue_monitor.py --config config.json; sleep 300; done"
    env_file: .env
    restart: always

  security-audit-monitor:
    build: .
    command: sh -c "while true; do python security_audit_monitor.py --config config.json; sleep 300; done"
    env_file: .env
    restart: always
```

### Requirements.txt

```
requests>=2.28.0
python-dateutil>=2.8.0
```

---

## API Permissions Required

All scripts require the OAuth client or user account to have:

| Script | Required Permissions |
|--------|---------------------|
| All agent monitors | View agents (Agent Manager) |
| Worker Health | View resource servers |
| Job Queue | Query processing/production/imaging objects |
| Security Audit | Query audit records, Audit API access |

---

## Troubleshooting

### Common Issues

**Authentication Errors:**
```
ERROR: Failed to get bearer token
```
- Verify client_id and client_secret are correct
- Check OAuth app permissions in RelativityOne
- Ensure host URL has no trailing slash

**Agent Not Found:**
```
CRITICAL: Agent not found!
```
- Verify agent_name_contains matches your agent name
- Check API permissions for viewing agents

**Rate Limiting:**
```
ERROR: 429 Too Many Requests
```
- Reduce polling frequency
- Stagger script execution times

**Connection Errors:**
```
ERROR: Failed to connect
```
- Check network connectivity
- Verify firewall allows outbound HTTPS
- Check if RelativityOne is accessible

---

## Future Scripts

Additional monitoring scripts planned:
- `workspace_health_monitor.py` - Monitor workspace availability and capacity
- `dtsearch_index_monitor.py` - Monitor dtSearch index health and fragmentation
- `analytics_job_monitor.py` - Monitor Structured Analytics jobs
