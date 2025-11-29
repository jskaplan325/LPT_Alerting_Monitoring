# RUNBOOK-005: RelativityOne Integration Points Job Failures

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Integration Points Job Failure |
| **Severity** | CRITICAL (Job Failed) / HIGH (Errors) / WARNING (Validation) |
| **Platform** | RelativityOne |
| **Detection** | Object Manager API (Job History RDO) |
| **Response SLA** | Critical: 15 min / High: 1 hour / Warning: 4 hours |
| **Escalation** | On-call → Team Lead → Relativity Support |

## Alert Conditions

```
IF Job Status == "Error - Job Failed" THEN CRITICAL
IF Job Status == "Validation failed" THEN CRITICAL
IF Job Status == "Completed with Errors" AND Items with Errors > 100 THEN HIGH
IF Job Status == "Completed with Errors" THEN MEDIUM
IF Job Status == "Pending" for > 30 minutes THEN WARNING
IF Next Scheduled Runtime (UTC) is blank THEN CRITICAL (scheduled job stopped)
```

## Integration Points Status Reference

| Status | Meaning | Alert Level |
|--------|---------|-------------|
| Pending | Waiting for agent | Warning if >30 min |
| Validation | Being validated | Info |
| Validation failed | Configuration error | **CRITICAL** |
| Processing | Running | Info |
| Completed | Success | None |
| Completed with Errors | Item-level errors | HIGH |
| Error - Job Failed | Job-level failure | **CRITICAL** |
| Suspending | Being suspended | Warning |
| Suspended | Paused for update | Warning |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge in monitoring system
- [ ] Note workspace ID, Integration Point name
- [ ] Check if this is a scheduled job
- [ ] Open tracking ticket

### Step 2: Quick Status Check

**Via UI:**
1. Navigate to affected workspace
2. Go to **Integration Points** application
3. Select the failed Integration Point
4. Click **Job History** tab
5. Review most recent job status

**Record the following:**
- Integration Point Name: ________________
- Workspace ID: ________________
- Job Status: ________________
- Items Transferred: ________________
- Items with Errors: ________________
- Start Time (UTC): ________________
- End Time (UTC): ________________
- Is Scheduled Job: Yes / No
- Next Scheduled Runtime: ________________

---

## Investigation Procedures (5-20 minutes)

### Step 3: Query Job History via API

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
        {"Name": "Integration Point"},
        {"Name": "Items Transferred"},
        {"Name": "Items with Errors"},
        {"Name": "Total Items"}
      ],
      "condition": "'\''Job Status'\'' IN ['\''Error - Job Failed'\'', '\''Completed with Errors'\'', '\''Validation failed'\'']",
      "sorts": [{"FieldIdentifier": {"Name": "Start Time (UTC)"}, "Direction": "Descending"}],
      "length": 10
    }
  }'
```

### Step 4: Review Job History Errors

**Via UI:**
1. Navigate to Integration Point → **Job History**
2. Click on failed job
3. Select **Job History Errors** tab
4. Review error details

**Error Types:**

| Error Type | Description | Level |
|------------|-------------|-------|
| Job-level errors | Entire job failed | Critical |
| Item-level errors | Individual records failed | High |
| Validation errors | Configuration issues | Critical |

### Step 5: Identify Error Category

**Common Integration Points Failures:**

| Category | Example Errors | Root Cause |
|----------|---------------|------------|
| **Authentication** | "401 Unauthorized", "Invalid credentials" | Expired tokens, wrong credentials |
| **Connectivity** | "Connection refused", "Timeout" | Network issues, firewall, endpoint down |
| **Configuration** | "Field not found", "Invalid mapping" | Mapping errors, missing fields |
| **Data** | "Invalid format", "Constraint violation" | Data quality issues |
| **Permission** | "Access denied to workspace" | Insufficient permissions |
| **Capacity** | "Rate limit exceeded" | Throttling by source/destination |

### Step 6: Check Integration Point Configuration

**Review these settings:**

| Setting | Check For |
|---------|-----------|
| Source/Destination | Correct workspace or provider selected |
| Credentials | Valid and not expired |
| Field Mappings | All required fields mapped correctly |
| Settings | Correct overwrite behavior, scheduler config |

---

## Resolution Procedures

### Scenario A: Validation Failed (CRITICAL)

**Symptoms:** Job Status = "Validation failed"

**Common Causes:**
1. Invalid field mappings
2. Missing required configuration
3. Source/destination connectivity issues
4. Permission problems

**Steps:**
1. Open Integration Point configuration
2. Review error message in Job History Errors
3. Check field mappings:
   - Navigate to **Field Mappings** section
   - Verify all required fields are mapped
   - Ensure field types match
4. Validate source/destination connectivity
5. Verify service account permissions

**Fix and Retry:**
1. Correct configuration issue
2. Click **Save** on Integration Point
3. Click **Run** to execute job

### Scenario B: Error - Job Failed (CRITICAL)

**Symptoms:** Entire job failed at job level

**Investigation:**
1. Check Job History Errors for specific message
2. Common job-level failures:

| Error Message | Cause | Resolution |
|---------------|-------|------------|
| "Agent not responding" | IP agent down | Check agent status |
| "Authentication failed" | Credential issue | Update credentials |
| "Connection timeout" | Network/endpoint issue | Verify connectivity |
| "Database error" | SQL issue | Escalate to support |
| "Maximum retry exceeded" | Persistent failures | Investigate root cause |

3. **Agent Check:**
   - Navigate to **Agents** tab
   - Filter for "Integration Points" agents
   - Verify agent status (should be "Idle" or "Running")
   - Integration Points Agents auto-deploy during app installation

**Resolution:**
1. Fix root cause (credentials, connectivity, etc.)
2. Re-run Integration Point job

### Scenario C: Completed with Errors (HIGH)

**Symptoms:** Job completed but `Items with Errors > 0`

**Steps:**
1. Calculate error rate: `(Items with Errors / Total Items) × 100`

2. **Decision Matrix:**

| Error % | Action |
|---------|--------|
| < 1% | Document, may be acceptable |
| 1-5% | Investigate, retry if fixable |
| > 5% | Major investigation required |

3. Review Job History Errors:
   - Export error list if available
   - Categorize by error type
   - Identify patterns

**Common Item-Level Errors:**

| Error | Cause | Resolution |
|-------|-------|------------|
| "Duplicate identifier" | Record already exists | Check overwrite settings |
| "Invalid date format" | Data format mismatch | Fix source data or mapping |
| "Required field null" | Missing data | Update source data |
| "Field value too long" | Data exceeds field limit | Truncate or increase field size |

4. **Retry options:**
   - Fix source data issues
   - Adjust field mappings
   - Re-run with corrected configuration

### Scenario D: Scheduled Job Stopped (CRITICAL)

**Symptoms:** `Next Scheduled Runtime (UTC)` is blank, no recent jobs

**Cause:** After maximum consecutive failed attempts, scheduled jobs stop automatically.

**Steps:**
1. Check Job History for failure pattern
2. Identify and fix root cause
3. Re-enable scheduled job:
   - Open Integration Point
   - Navigate to **Scheduler** section
   - Verify schedule configuration
   - Click **Save** to re-enable

**IMPORTANT:** Scheduled jobs halt entirely when consecutive failures exceed the maximum threshold. This requires manual intervention to restart.

### Scenario E: Pending Job (WARNING)

**Symptoms:** Job Status = "Pending" for extended period (>30 minutes)

**Steps:**
1. Check Integration Points Agent status
2. Review queue for blocking jobs
3. Verify agent is picking up work

**If Agent Issues:**
1. Navigate to **Agents** tab
2. Check Integration Points agent status
3. If disabled, re-enable
4. If "Service not responding", escalate

---

## Integration Points Agent Information

**Agent Behavior:**
- Auto-deploys during application installation
- Processes jobs in queue order
- Job status progression: Pending → Validation → Processing → Completed/Failed

**Agent States:**

| State | Meaning | Action |
|-------|---------|--------|
| Idle | No jobs in queue | Normal |
| Running | Processing a job | Normal |
| Disabled | Manually disabled | Re-enable if appropriate |
| Service not responding | Agent failure | Escalate |

---

## API Reference

### Query Integration Points Job History

```bash
POST /Relativity.Rest/api/Relativity.ObjectManager/{version}/workspace/{workspaceID}/object/query

# Request body for failed jobs
{
  "request": {
    "objectType": {"Name": "Job History"},
    "fields": [
      {"Name": "Job Status"},
      {"Name": "Start Time (UTC)"},
      {"Name": "Integration Point"},
      {"Name": "Items Transferred"},
      {"Name": "Items with Errors"}
    ],
    "condition": "'Job Status' IN ['Error - Job Failed', 'Completed with Errors', 'Validation failed']"
  }
}
```

### Monitor for Stopped Scheduled Jobs

```bash
# Query Integration Points with blank Next Scheduled Runtime
{
  "request": {
    "objectType": {"Name": "Integration Point"},
    "fields": [
      {"Name": "Name"},
      {"Name": "Next Scheduled Runtime (UTC)"},
      {"Name": "Scheduler Enabled"}
    ],
    "condition": "'Scheduler Enabled' == true AND 'Next Scheduled Runtime (UTC)' IS NULL"
  }
}
```

---

## Escalation Procedures

### When to Escalate

| Condition | Level | Timeframe |
|-----------|-------|-----------|
| Agent not responding | Relativity Support | Immediate |
| Database errors | Relativity Support | Immediate |
| Persistent failures (5+ consecutive) | Team Lead | 2 hours |
| Data sync critical path blocked | Team Lead | 30 minutes |
| Scheduled jobs stopped for >24 hours | Team Lead | Immediate |

### Information for Escalation

- [ ] Integration Point name and workspace ID
- [ ] Job History with error details
- [ ] Field mapping configuration
- [ ] Agent status
- [ ] Timeline of failures
- [ ] Source/destination system status

---

## Post-Incident Actions

### Immediate
- [ ] Verify job completed successfully after fix
- [ ] Check data integrity in destination
- [ ] Document resolution

### Short-term (24 hours)
- [ ] Review error patterns
- [ ] Update monitoring for detected patterns
- [ ] Verify scheduled jobs are running

### Long-term
- [ ] Improve field mapping documentation
- [ ] Update credential management procedures
- [ ] Consider retry/error handling improvements

---

## Prevention Measures

### Configuration Best Practices
- Document all Integration Point configurations
- Use descriptive naming conventions
- Test mappings with small data sets first
- Keep credentials current with rotation schedule

### Monitoring Recommendations
- Alert on any "Error - Job Failed" status
- Alert on "Validation failed" immediately
- Monitor for blank "Next Scheduled Runtime"
- Track error rates over time

### Scheduling Considerations
- Schedule jobs during off-peak hours
- Allow adequate time between scheduled runs
- Consider dependencies between Integration Points

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
