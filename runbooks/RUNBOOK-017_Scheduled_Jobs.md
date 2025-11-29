# RUNBOOK-017: RelativityOne Scheduled Jobs Monitoring

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Scheduled Job Alerts |
| **Severity** | CRITICAL (Stopped/Failed) / HIGH (Errors) / MEDIUM (Delays) |
| **Platform** | RelativityOne |
| **Detection** | Multiple APIs + Audit |
| **Response SLA** | Critical: 15 min / High: 1 hour / Medium: 4 hours |
| **Escalation** | On-call → Team Lead → Relativity Support |

## Alert Conditions

```
IF Scheduled_Job_Status == "Stopped" THEN CRITICAL
IF Scheduled_Job_Status == "Failed" THEN CRITICAL
IF Next_Scheduled_Runtime == NULL (for enabled job) THEN CRITICAL
IF Consecutive_Failures > max_threshold THEN CRITICAL
IF Job_Completed_With_Errors THEN HIGH
IF Job_Duration > expected * 2 THEN MEDIUM
IF Job_Did_Not_Run_At_Scheduled_Time THEN HIGH
```

---

## Types of Scheduled Jobs

### Integration Points Scheduled Jobs
| Aspect | Details |
|--------|---------|
| **Purpose** | Automated data sync |
| **Scheduling** | Configurable intervals |
| **Failure Behavior** | Stops after max consecutive failures |
| **Key Indicator** | "Next Scheduled Runtime (UTC)" field |

### Automated Workflows
| Aspect | Details |
|--------|---------|
| **Purpose** | Business process automation |
| **Scheduling** | Trigger-based or scheduled |
| **Notification** | Can send emails via Send Email Checkpoint |
| **Scope** | Workspace-level |

### Agent-Based Scheduled Tasks
| Aspect | Details |
|--------|---------|
| **Examples** | dtSearch index updates, Analytics updates |
| **Control** | Agent configuration |
| **Monitoring** | Agent status, job history |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge in monitoring system
- [ ] Identify job type and name
- [ ] Determine business impact
- [ ] Open tracking ticket

### Step 2: Quick Status Check

**Determine:**
- What type of scheduled job?
- When was it last successful?
- What is the failure/issue?
- Who depends on this job?

**Record the following:**
- Job Name: ________________
- Job Type: ________________
- Workspace: ________________
- Last Success: ________________
- Last Failure: ________________
- Next Scheduled: ________________
- Error Message: ________________

---

## Investigation Procedures

### Step 3: Check Job-Specific Status

**For Integration Points:**
1. Navigate to workspace → Integration Points
2. Check "Next Scheduled Runtime (UTC)" field
3. Review Job History
4. Look for error messages

**Query for Integration Points Status:**
```bash
curl -X POST "<host>/Relativity.Rest/api/Relativity.ObjectManager/v1/workspace/<WORKSPACE_ID>/object/query" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -" \
  -H "Content-Type: application/json" \
  -d '{
    "request": {
      "objectType": {"Name": "Integration Point"},
      "fields": [
        {"Name": "Name"},
        {"Name": "Next Scheduled Runtime (UTC)"},
        {"Name": "Scheduler Enabled"}
      ],
      "condition": "'\''Scheduler Enabled'\'' == true"
    }
  }'
```

**For Automated Workflows:**
1. Navigate to workspace → Automated Workflows
2. Review workflow history
3. Check trigger status
4. Review checkpoint results

### Step 4: Review Job History

**For Integration Points Job History:**
```bash
curl -X POST "<host>/Relativity.Rest/api/Relativity.ObjectManager/v1/workspace/<WORKSPACE_ID>/object/query" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -" \
  -H "Content-Type: application/json" \
  -d '{
    "request": {
      "objectType": {"Name": "Job History"},
      "fields": [
        {"Name": "Job Status"},
        {"Name": "Start Time (UTC)"},
        {"Name": "End Time (UTC)"},
        {"Name": "Items Transferred"},
        {"Name": "Items with Errors"}
      ],
      "sorts": [{"FieldIdentifier": {"Name": "Start Time (UTC)"}, "Direction": "Descending"}],
      "length": 10
    }
  }'
```

### Step 5: Identify Failure Pattern

Check for:
- Single failure vs. recurring
- Specific error messages
- Time-based patterns
- Data-related issues
- Configuration changes

---

## Resolution Procedures

### Scenario A: Scheduled Job Stopped (Integration Points)

**Symptoms:** "Next Scheduled Runtime (UTC)" is blank, job no longer running

**Cause:** After maximum consecutive failed attempts, scheduled jobs stop automatically.

**Steps:**
1. Review Job History for failure pattern
2. Identify root cause:

| Failure Type | Common Causes |
|--------------|---------------|
| Validation failed | Configuration issue |
| Connection error | Endpoint/credential issue |
| Data errors | Source data problems |
| Timeout | Large data or performance |

3. **Fix root cause:**
   - Update credentials if expired
   - Fix configuration if changed
   - Address data issues
   - Optimize if performance issue

4. **Re-enable scheduled job:**
   - Open Integration Point
   - Go to Scheduler section
   - Verify settings
   - Save to re-enable

### Scenario B: Job Completed with Errors

**Symptoms:** Job runs but has item-level errors

**Steps:**
1. Review Job History Errors tab
2. Categorize error types
3. Determine acceptable error threshold
4. Address systematic issues

**Resolution by error rate:**

| Error Rate | Action |
|------------|--------|
| <1% | Document, may be acceptable |
| 1-5% | Investigate patterns, fix if possible |
| 5-10% | Major investigation needed |
| >10% | Stop and fix before continuing |

### Scenario C: Job Did Not Run

**Symptoms:** Expected job run time passed without execution

**Investigation:**
1. Check job schedule configuration
2. Verify job is enabled
3. Check for prerequisite failures
4. Review agent status

**Common causes:**

| Cause | Resolution |
|-------|------------|
| Job disabled | Re-enable |
| Agent down | Check agent status |
| Queue backed up | Wait or address queue |
| Configuration error | Fix schedule settings |
| Previous run still active | Wait or cancel |

### Scenario D: Job Running Long

**Symptoms:** Job duration exceeds normal

**Investigation:**
1. Is job still progressing?
2. Check for large data volumes
3. Review system resources
4. Check for blocking operations

**Response:**
```
IF Job is making progress THEN
  → Monitor and wait
  → Document for baseline

IF Job is stuck THEN
  → May need to cancel
  → Investigate root cause
  → Restart when fixed
```

### Scenario E: Recurring Failures

**Symptoms:** Same job failing repeatedly

**Pattern Analysis:**
```
IF Same error every run THEN
  → Configuration or data issue
  → Fix root cause before re-enabling

IF Intermittent failures THEN
  → May be timing or resource issue
  → Consider scheduling changes
  → Add error handling if possible
```

---

## Scheduled Job Best Practices

### Schedule Configuration

| Consideration | Recommendation |
|---------------|----------------|
| Timing | Schedule during off-peak hours |
| Frequency | Match business need, don't over-schedule |
| Overlap | Avoid overlapping job schedules |
| Dependencies | Account for job dependencies |
| Time zones | Use UTC for consistency |

### Error Handling

| Setting | Purpose |
|---------|---------|
| Max consecutive failures | Auto-stop prevents infinite failures |
| Retry logic | Built-in for some job types |
| Notification | Configure email alerts where available |

### Monitoring Checklist

- [ ] All scheduled jobs have monitoring
- [ ] "Next Scheduled Runtime" tracked
- [ ] Failure notifications configured
- [ ] Regular review of job history
- [ ] Duration baselines established

---

## Monitoring Configuration

### Key Queries for Scheduled Job Monitoring

**Integration Points - Stopped Jobs:**
```json
{
  "condition": "'Scheduler Enabled' == true AND 'Next Scheduled Runtime (UTC)' IS NULL"
}
```

**Integration Points - Recent Failures:**
```json
{
  "objectType": {"Name": "Job History"},
  "condition": "'Job Status' IN ['Error - Job Failed', 'Completed with Errors', 'Validation failed']"
}
```

### Alert Rules

```
# Stopped scheduled job (Critical)
IF Scheduler_Enabled == true
   AND Next_Scheduled_Runtime == NULL
THEN ALERT(CRITICAL)

# Job failure (High)
IF Job_Status IN ("Error - Job Failed", "Validation failed")
THEN ALERT(HIGH)

# Job with errors (Medium)
IF Job_Status == "Completed with Errors"
   AND Error_Rate > 5%
THEN ALERT(MEDIUM)

# Job overdue (High)
IF Expected_Run_Time < Now() - Tolerance
   AND Last_Run_Time < Expected_Run_Time
THEN ALERT(HIGH)
```

---

## Automated Workflows

### Workflow Monitoring

Automated Workflows can:
- Send email notifications (Send Email Checkpoint)
- Trigger on schedules or events
- Execute multi-step processes

**Monitoring points:**
- Workflow execution history
- Checkpoint status
- Email delivery confirmation

### Workflow Notifications

Use "Send Email Checkpoint" for:
- Job completion notifications
- Error alerts
- Status updates

**Configuration:**
1. Add Send Email Checkpoint to workflow
2. Configure recipients
3. Define trigger conditions
4. Set email content

---

## Escalation Procedures

### When to Escalate

| Condition | Level | Timeframe |
|-----------|-------|-----------|
| Business-critical job stopped | Team Lead | Immediate |
| Cannot determine root cause | Team Lead | 2 hours |
| Agent-related issues | Relativity Support | 30 min |
| Platform/infrastructure issue | Relativity Support | Immediate |
| Recurring unexplained failures | Team Lead | 24 hours |

### Information for Escalation

- [ ] Job name and type
- [ ] Schedule configuration
- [ ] Job history (last 10 runs)
- [ ] Error messages
- [ ] Root cause analysis attempted
- [ ] Business impact

---

## Post-Incident Actions

### Immediate
- [ ] Verify job is running/scheduled correctly
- [ ] Confirm next scheduled run
- [ ] Notify stakeholders

### Short-term (24 hours)
- [ ] Complete incident report
- [ ] Monitor next scheduled run
- [ ] Address any data gaps

### Long-term
- [ ] Review scheduling strategy
- [ ] Update monitoring coverage
- [ ] Document resolution

---

## Prevention Measures

### Proactive Monitoring
- Track all scheduled jobs
- Alert on stopped jobs
- Monitor job duration trends
- Regular job history review

### Schedule Management
- Document all scheduled jobs
- Review schedules quarterly
- Avoid scheduling conflicts
- Plan for maintenance windows

### Error Handling
- Configure appropriate failure thresholds
- Set up notification workflows
- Document expected error rates
- Regular review of job health

---

## API Reference

### Integration Points Queries

```bash
# Get Integration Points with schedule
POST /Relativity.ObjectManager/{version}/workspace/{workspaceID}/object/query

{
  "objectType": {"Name": "Integration Point"},
  "fields": [
    {"Name": "Name"},
    {"Name": "Scheduler Enabled"},
    {"Name": "Next Scheduled Runtime (UTC)"}
  ]
}

# Get Job History
{
  "objectType": {"Name": "Job History"},
  "fields": [
    {"Name": "Job Status"},
    {"Name": "Start Time (UTC)"},
    {"Name": "Items with Errors"}
  ]
}
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
