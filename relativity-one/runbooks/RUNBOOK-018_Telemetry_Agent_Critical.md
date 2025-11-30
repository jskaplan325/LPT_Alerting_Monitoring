# RUNBOOK-018: RelativityOne Telemetry Agent - CRITICAL

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Telemetry Agent Failure |
| **Severity** | **CRITICAL - BUSINESS IMPACT** |
| **Platform** | RelativityOne |
| **Detection** | Custom Polling Script (Required) |
| **Response SLA** | **IMMEDIATE** (0-5 minutes) |
| **Escalation** | On-call → Team Lead → Relativity Support (Immediate) |

## CRITICAL BUSINESS IMPACT

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚠️  WARNING: TELEMETRY AGENT FAILURE = USER LOGOUT EVENT  ⚠️   │
│                                                                 │
│  If the Telemetry Metrics Transmission Agent stops working:    │
│  • Users will be LOGGED OUT of RelativityOne                   │
│  • Active review sessions will be INTERRUPTED                  │
│  • Productions in progress may be AFFECTED                     │
│  • This is a BUSINESS-CRITICAL failure                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Alert Conditions

### Primary Alerts (CRITICAL)
```
IF Telemetry_Agent_Status == "Disabled" THEN CRITICAL (IMMEDIATE)
IF Telemetry_Agent_Status == "Not Responding" THEN CRITICAL (IMMEDIATE)
IF Last_Telemetry_Sync > 24 hours ago THEN CRITICAL
IF Last_Telemetry_Sync > 12 hours ago THEN HIGH (investigate)
IF Last_Telemetry_Sync > 6 hours ago THEN WARNING (monitor)
```

### Secondary Alerts
```
IF Telemetry_Agent_Enabled == false THEN CRITICAL
IF Telemetry_Agent_Last_Activity > 1 hour THEN WARNING
IF Telemetry_Agent_Message contains "Error" THEN HIGH
```

---

## Agent Specifications

| Attribute | Value |
|-----------|-------|
| **Agent Name** | Telemetry Metrics Transmission Agent |
| **Instance Type** | Single-instance (ONE per environment) |
| **Default Interval** | Check documentation (typically seconds) |
| **Purpose** | Transmits platform metrics to Relativity |
| **Failure Impact** | User session termination, platform instability |

---

## Monitoring Requirements

### Polling Frequency
| Check Type | Frequency | Rationale |
|------------|-----------|-----------|
| Agent Enabled Status | Every 1 minute | Catch disable events immediately |
| Agent Running Status | Every 1 minute | Detect failures quickly |
| Last Activity Check | Every 5 minutes | Ensure agent is actively syncing |
| Sync Timestamp Check | Every 15 minutes | Verify data transmission |

### Alert Thresholds
| Metric | Warning | High | Critical |
|--------|---------|------|----------|
| Last Activity | >30 min | >1 hour | >2 hours |
| Last Sync | >6 hours | >12 hours | >24 hours |
| Agent Status | - | - | Disabled/Not Responding |

---

## Initial Triage (0-2 minutes)

### Step 1: Acknowledge Alert - IMMEDIATELY
- [ ] Acknowledge in monitoring system
- [ ] This is CRITICAL - all other tasks are secondary
- [ ] Open P1/Sev1 incident ticket immediately

### Step 2: Verify Current State

**Via RelativityOne Admin:**
1. Log into RelativityOne immediately
2. Navigate to **Agents** tab
3. Filter for "Telemetry" or "Metrics Transmission"
4. Check:
   - Is agent **Enabled**?
   - What is the **Status**?
   - When was **Last Activity**?

**Record immediately:**
- Agent Status: ________________
- Enabled: Yes / No
- Last Activity: ________________
- Error Message (if any): ________________
- Time of Alert: ________________

### Step 3: Check User Impact
- Are users reporting logouts?
- Are there complaints coming in?
- Check support channels for reports

---

## Investigation Procedures (2-10 minutes)

### Step 4: Query Agent Status via API

```bash
curl -X GET "<host>/Relativity.REST/api/relativity-environment/v1/agents" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -" \
  -H "Content-Type: application/json" | jq '.[] | select(.Name | contains("Telemetry"))'
```

**Expected Response Fields:**
```json
{
  "ArtifactID": 12345,
  "Name": "Telemetry Metrics Transmission Agent",
  "Enabled": true,
  "Status": "Running",
  "LastActivityDate": "2024-01-15T14:30:00Z",
  "Server": {...},
  "Message": ""
}
```

### Step 5: Analyze Agent State

| Current State | Severity | Immediate Action |
|---------------|----------|------------------|
| Enabled=false | CRITICAL | Re-enable immediately |
| Status="Not Responding" | CRITICAL | Escalate to Relativity |
| Last Activity >2 hours | CRITICAL | Investigate + Escalate |
| Last Activity >1 hour | HIGH | Investigate cause |
| Message contains error | HIGH | Review error, escalate |

### Step 6: Check for Related Issues

1. **Instance Details → Alerts:**
   - Other agent issues?
   - Server problems?

2. **Other Single-Instance Agents:**
   - Billing Agent status
   - Workspace Delete Manager
   - Workspace Upgrade Manager
   - Alert Manager

3. **Recent Changes:**
   - Any maintenance performed?
   - Configuration changes?
   - Platform updates?

---

## Resolution Procedures

### Scenario A: Agent Disabled (CRITICAL)

**Symptoms:** Enabled = false

**IMMEDIATE ACTION:**
1. Navigate to Agents tab
2. Select Telemetry Metrics Transmission Agent
3. Click **Enable**
4. Monitor for 2 minutes
5. Verify Last Activity updates

**If agent won't stay enabled:**
- Check for error messages
- Review agent configuration
- **ESCALATE IMMEDIATELY to Relativity Support**

### Scenario B: Agent Not Responding (CRITICAL)

**Symptoms:** Status = "Not Responding" or "Service not responding"

**IMMEDIATE ESCALATION REQUIRED**

1. Document current state (screenshots)
2. **Contact Relativity Support immediately:**
   - Phone: [Your Relativity Support Number]
   - Email: support@relativity.com
   - Priority: **P1/Critical/Emergency**

3. Provide:
   - Agent status details
   - Last known good activity time
   - User impact description
   - Any error messages

**DO NOT attempt to restart services in RelativityOne SaaS**

### Scenario C: Stale Last Activity (>2 hours)

**Symptoms:** Agent enabled and "running" but Last Activity is old

**Steps:**
1. Verify agent configuration
2. Check if agent is truly processing
3. Review server health
4. Check for blocking conditions

**If no obvious cause:**
- Try disabling and re-enabling agent
- Monitor for 5 minutes
- If no improvement, escalate

### Scenario D: Sync Delay (>24 hours)

**Symptoms:** Agent running but data not syncing

**Investigation:**
1. Check network connectivity
2. Review any firewall changes
3. Check Relativity status page for outages
4. Verify no platform maintenance in progress

**Escalation:**
- Contact Relativity Support
- This may indicate infrastructure issues on Relativity side

---

## Escalation Procedures

### Immediate Escalation Triggers

| Condition | Action |
|-----------|--------|
| Agent disabled and won't re-enable | Call Relativity Support |
| Agent not responding | Call Relativity Support |
| Users actively being logged out | Call Relativity Support + Internal escalation |
| No resolution in 10 minutes | Escalate to Team Lead |

### Escalation Contacts

| Level | Contact | Trigger |
|-------|---------|---------|
| **Tier 1** | On-call engineer | Alert received |
| **Tier 2** | Team Lead | No resolution in 10 min |
| **Tier 3** | Relativity Support | Any CRITICAL condition |
| **Executive** | IT Director/Manager | User impact confirmed |

### Relativity Support Engagement

**For Telemetry Agent issues, always:**
1. Call support (don't just email for CRITICAL)
2. Request P1/Emergency priority
3. Emphasize user logout impact
4. Stay on line until acknowledged

**Information to provide:**
- [ ] Tenant/Instance identifier
- [ ] Agent current status
- [ ] Last known good timestamp
- [ ] User impact (number affected, symptoms)
- [ ] Screenshots of agent status
- [ ] Any recent changes

---

## Post-Incident Actions

### Immediate (within 1 hour of resolution)
- [ ] Verify agent is running normally
- [ ] Confirm Last Activity is updating
- [ ] Verify no users are experiencing issues
- [ ] Send all-clear communication

### Short-term (within 24 hours)
- [ ] Complete incident report
- [ ] Root cause analysis
- [ ] Review monitoring effectiveness
- [ ] Update alerting thresholds if needed

### Long-term
- [ ] Implement preventive measures
- [ ] Review with Relativity (if their issue)
- [ ] Update runbook with lessons learned
- [ ] Consider additional redundancy/monitoring

---

## Prevention Measures

### Automated Monitoring (REQUIRED)

**Deploy the Telemetry Agent Monitoring Script:**
- Poll every 1 minute
- Check enabled status
- Check last activity
- Alert on any anomaly

### Alert Configuration

| Check | Frequency | Alert If |
|-------|-----------|----------|
| Enabled | 1 min | Disabled |
| Status | 1 min | Not "Running" or "Idle" |
| Last Activity | 5 min | >1 hour stale |
| Sync Time | 15 min | >24 hours stale |

### Proactive Measures
- Daily visual check of agent status
- Include in morning operations checklist
- Review after any platform maintenance
- Monitor Relativity status page

---

## Monitoring Script Reference

See: `scripts/telemetry_agent_monitor.py`

The monitoring script should:
1. Query agent status via API
2. Check enabled/disabled state
3. Verify last activity timestamp
4. Calculate sync delay
5. Send alerts via configured channels
6. Log all checks for audit

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│           TELEMETRY AGENT QUICK RESPONSE                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. CHECK: Agents tab → Telemetry Metrics Transmission     │
│                                                             │
│  2. IF DISABLED:                                           │
│     → Enable immediately                                    │
│     → Monitor 2 minutes                                     │
│     → If fails, call Relativity                            │
│                                                             │
│  3. IF NOT RESPONDING:                                      │
│     → CALL Relativity Support immediately                  │
│     → P1/Emergency priority                                 │
│     → Do NOT attempt restart                               │
│                                                             │
│  4. IF STALE (>2 hours):                                   │
│     → Disable/Re-enable                                     │
│     → If no improvement in 5 min, escalate                 │
│                                                             │
│  RELATIVITY SUPPORT: support@relativity.com                │
│  PRIORITY: Always P1/Critical for this agent               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook for critical telemetry monitoring |
