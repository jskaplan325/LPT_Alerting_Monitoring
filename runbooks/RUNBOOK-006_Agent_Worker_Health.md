# RUNBOOK-006: RelativityOne Agent and Worker Health

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Agent/Worker Health Issues |
| **Severity** | CRITICAL (Unresponsive) / HIGH (Disabled) / WARNING (Performance) |
| **Platform** | RelativityOne |
| **Detection** | Instance Details, Worker Monitoring, Agent Manager API |
| **Response SLA** | Critical: Immediate / High: 30 min / Warning: 4 hours |
| **Escalation** | On-call → Team Lead → Relativity Support |

## Alert Conditions

```
IF Worker_Status == "Service not responding" THEN CRITICAL
IF Critical_Agent_Disabled THEN CRITICAL
IF Agent_Status == "Disabled" (non-maintenance) THEN HIGH
IF Worker_Memory > 90% THEN WARNING
IF Worker_CPU > 90% sustained THEN WARNING
IF Worker_Tasks_Per_Minute < threshold THEN WARNING
IF Agent_Last_Activity > 30 minutes THEN WARNING
```

---

## Agent Categories

### Single-Instance Agents (One per Environment)
These agents are critical - only one instance exists:

| Agent | Purpose | Impact if Down |
|-------|---------|----------------|
| Telemetry Metrics Transmission | Platform telemetry | Metrics collection stops |
| Billing Agent | Usage tracking | Billing data missing |
| Workspace Delete Manager | Workspace cleanup | Deletions queue up |
| Workspace Upgrade Manager | Workspace upgrades | Upgrades blocked |

### Resource Pool Agents (Per Pool/Server)

| Agent | Count | Purpose |
|-------|-------|---------|
| Branding Manager | Up to 4 per pool | Document branding |
| Analytics Cluster Manager | 1 per Analytics server | Analytics operations |
| Content Analyst Index Manager | 1 per Analytics server | Content indexing |
| Analytics Categorization Manager | 2 per Analytics server | Document categorization |

### Processing Agents

| Agent | Notes |
|-------|-------|
| Server Manager | **Required** for processing agent status visibility |
| Processing Agent | Handles document processing |

### Other Key Agents

| Agent | Interval | Notes |
|-------|----------|-------|
| Alert Manager | 30 sec (recommended) | Security alerting |
| Imaging Manager | 3600 sec (do not modify) | Stuck job cleanup |
| Production Manager | Default | Production processing |
| Integration Points | Auto-deployed | Data sync |
| dtSearch Index | Default | Search indexing |

---

## Worker Status Reference

| Status | Meaning | Alert Level |
|--------|---------|-------------|
| Idle | No active tasks | Normal |
| Running | Processing tasks | Normal |
| Service not responding | Worker failure | **CRITICAL** |

## Worker Metrics

| Metric | Description | Warning Threshold |
|--------|-------------|-------------------|
| Threads in Use | Active processing threads | Context-dependent |
| Memory (MB) | Current memory consumption | >90% of allocated |
| CPU Activity | Processor utilization | >90% sustained |
| Tasks per Minute | Throughput | Below baseline |
| Last Activity | Most recent task completion | >30 min with jobs |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge in monitoring system
- [ ] Note which agent(s) or worker(s) affected
- [ ] Open tracking ticket

### Step 2: Access Instance Details
1. Log into RelativityOne admin portal
2. Navigate to **Instance Details** tab
3. Check **Alerts** section for:
   - Disabled agents
   - Unresponsive servers
4. Note any correlated infrastructure alerts

### Step 3: Quick Status Check

**For Agents:**
1. Navigate to **Agents** tab
2. Filter for affected agent type
3. Note status and last activity

**For Workers:**
1. Navigate to **Worker Monitoring** tab
2. Identify affected worker
3. Note status and metrics

**Record the following:**
- Affected Component: ________________
- Type (Agent/Worker): ________________
- Status: ________________
- Last Activity: ________________
- Server/Pool: ________________
- Related Alerts: ________________

---

## Investigation Procedures (5-20 minutes)

### Step 4: Check Agent Status

**Via UI:**
1. Navigate to **Agents** tab
2. Filter by:
   - Agent Type
   - Status (Enabled/Disabled)
   - Server
3. Review agent details:
   - Current status
   - Last activity timestamp
   - Message (if any)
   - Run interval

**Via API:**
```bash
# Get agent status using Agent Manager API
curl -X GET "<host>/Relativity.REST/api/relativity-environment/v1/agents" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -"
```

### Step 5: Check Worker Monitoring

**Via UI:**
1. Navigate to **Worker Monitoring** tab
2. Review metrics for each worker:
   - Status (Idle/Running/Service not responding)
   - Threads in use
   - Memory (MB)
   - CPU activity
   - Tasks per minute
   - Last activity

### Step 6: Correlate with Job Issues

Check if agent/worker issues are causing job failures:
1. **Queue Management** → Check for stuck jobs
2. **Processing History** → Look for "Paused" jobs (indicates agent issues)
3. Review job error messages for agent-related failures

### Step 7: Check for Patterns

| Pattern | Possible Cause |
|---------|----------------|
| All workers affected | Infrastructure issue |
| Single worker affected | Worker-specific problem |
| Specific agent type affected | Agent configuration issue |
| Intermittent issues | Resource contention |
| After deployment/change | Configuration change impact |

---

## Resolution Procedures

### Scenario A: Worker "Service Not Responding" (CRITICAL)

**Symptoms:** Worker status shows "Service not responding"

**IMPORTANT:** Do NOT attempt to restart workers without vendor guidance. RelativityOne is a managed SaaS platform.

**Steps:**
1. **Document the issue:**
   - Screenshot of Worker Monitoring
   - Note affected worker(s)
   - Note timeline

2. **Check for broader issues:**
   - Are multiple workers affected?
   - Check status.relativity.com for platform issues

3. **Escalate immediately:**
   - Contact Relativity Support
   - Provide documentation
   - Note: RelativityOne's SRE team monitors stuck jobs and may already be aware

4. **Workaround (if available):**
   - Jobs may automatically redistribute to healthy workers
   - Monitor queue for progress on other workers

### Scenario B: Agent Disabled (HIGH)

**Symptoms:** Agent status shows "Disabled"

**Steps:**
1. **Determine if intentional:**
   - Check for maintenance windows
   - Verify with team if anyone disabled it
   - Review change management tickets

2. **If unintentional:**
   - Note which agent is disabled
   - Check for error messages in agent details

3. **Re-enable agent:**
   - Navigate to Agents tab
   - Select the disabled agent
   - Click **Enable**
   - Monitor for 5 minutes to confirm it starts processing

4. **If agent won't stay enabled:**
   - Check for configuration errors
   - Review agent run interval settings
   - Escalate if persistent

### Scenario C: Processing Agents Not Visible

**Symptoms:** Cannot see processing agent status

**Cause:** Server Manager agent must be running for processing agent visibility.

**Steps:**
1. Navigate to **Agents** tab
2. Filter for "Server Manager"
3. Verify Server Manager is:
   - Enabled
   - Running
   - Last activity recent

4. If Server Manager is down:
   - Re-enable if disabled
   - Escalate if unresponsive

### Scenario D: Jobs Showing "Paused" Status

**Symptoms:** Jobs in queue showing "Paused" status

**Cause:** "Paused" status typically indicates agent issues.

**Steps:**
1. Identify which job type is paused (Processing, Imaging, etc.)
2. Check corresponding agent:
   - Processing jobs → Processing agents
   - Imaging jobs → Imaging agents
   - Production jobs → Production Manager

3. Verify agent status:
   - Is it enabled?
   - Is it responding?
   - Any error messages?

4. If agent is healthy but jobs still paused:
   - Check resource constraints
   - Review job priority settings
   - Escalate if persistent

### Scenario E: Worker Performance Degradation (WARNING)

**Symptoms:** High memory/CPU, low tasks per minute

**Steps:**
1. **Check resource utilization:**
   - Memory >90%: Possible memory pressure
   - CPU >90% sustained: Overloaded

2. **Identify cause:**
   - Large/complex documents being processed?
   - Too many concurrent jobs?
   - Resource-intensive operations?

3. **Mitigation options:**
   - Reduce concurrent job load
   - Prioritize critical jobs
   - Schedule heavy operations for off-peak

4. **Escalate if:**
   - Resource exhaustion persists
   - Unable to identify cause
   - Impact to production workloads

---

## Agent Configuration Reference

### Recommended Agent Intervals

| Agent | Recommended Interval | Notes |
|-------|---------------------|-------|
| Alert Manager | 30 seconds | For timely security alerts |
| Most agents | 5 seconds (default) | Standard check-in |
| Imaging Manager | 3600 seconds | **Do not modify** |

### Agent Count Guidelines

| Agent Type | Recommended Count |
|------------|-------------------|
| Branding Manager | Up to 4 per resource pool |
| Analytics Cluster Manager | 1 per Analytics server |
| Content Analyst Index Manager | 1 per Analytics server |
| Analytics Categorization Manager | 2 per Analytics server |
| Structured Analytics Workers | Minimum 4 (1 GB RAM each) |

---

## Monitoring Dashboard Access

### Instance Details Tab
- **Alerts section:** Disabled agents, unresponsive servers
- **Queues section:** Production, Branding, OCR, Imaging queue status
- Navigation links to Agents tab for troubleshooting

### Queue Management Tab
- Processing and Imaging queue status
- Production queue status
- OCR queue status
- dtSearch indexing status
- Branding job progress

### Worker Monitoring Tab
- Real-time worker metrics
- Status, threads, memory, CPU
- Tasks per minute
- Last activity timestamp

---

## Escalation Procedures

### When to Escalate to Relativity Support

| Condition | Action |
|-----------|--------|
| Worker "Service not responding" | Immediate escalation |
| Multiple agents disabled unexpectedly | Escalate within 15 min |
| Agent won't stay enabled after restart | Escalate within 30 min |
| Suspected infrastructure issue | Immediate escalation |
| Performance degradation affecting SLAs | Escalate within 1 hour |

### Information for Escalation

- [ ] Screenshots of Worker Monitoring
- [ ] Screenshots of Agents tab (filtered to affected)
- [ ] Instance Details alerts
- [ ] Timeline of when issue started
- [ ] Impact description (which jobs affected)
- [ ] Any recent changes or deployments
- [ ] Current queue status

---

## Post-Incident Actions

### Immediate
- [ ] Verify agents/workers are healthy
- [ ] Confirm queued jobs are processing
- [ ] Document resolution

### Short-term (24 hours)
- [ ] Complete incident report
- [ ] Review if jobs completed successfully
- [ ] Check for data integrity issues

### Long-term
- [ ] Analyze root cause
- [ ] Implement additional monitoring if gaps found
- [ ] Update runbook with new scenarios

---

## Prevention Measures

### Daily Monitoring Checklist
- [ ] Check Instance Details for alerts
- [ ] Review Worker Monitoring metrics
- [ ] Verify critical agents are running
- [ ] Check queue depths

### Proactive Steps
- Notify Relativity via "Incoming Project Details: RelativityOne" form before large projects
- Schedule resource-intensive jobs during off-peak hours
- Monitor trends in worker utilization

### Configuration Management
- Document any agent configuration changes
- Follow change management procedures
- Keep agent intervals at recommended values

---

## API Reference

### Agent Manager API

```bash
# Get all agents
GET /Relativity.REST/api/relativity-environment/v1/agents

# Enable agent
POST /Relativity.REST/api/relativity-environment/v1/agents/{agentId}/enable

# Disable agent
POST /Relativity.REST/api/relativity-environment/v1/agents/{agentId}/disable
```

### Worker Monitoring
Worker metrics are available through the UI. For programmatic access, use the Instance Details or custom applications leveraging the platform SDK.

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
