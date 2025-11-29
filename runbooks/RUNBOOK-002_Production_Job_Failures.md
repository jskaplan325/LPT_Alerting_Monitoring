# RUNBOOK-002: RelativityOne Production Job Failures

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Production Job Failure |
| **Severity** | CRITICAL |
| **Platform** | RelativityOne |
| **Detection** | Production Queue Manager API |
| **Response SLA** | 15 minutes |
| **Escalation** | On-call → Team Lead → Relativity Support |

## Alert Conditions

This runbook is triggered when any of the following conditions are detected:

```
IF Errors array length > 0 THEN CRITICAL
IF Status == "Failed" OR "Error" OR "Cancelled" THEN CRITICAL
IF Job in queue > 4 hours without progress THEN WARNING
IF Same JobID appears for > 2 hours THEN WARNING (stuck job investigation)
```

## Production Stages Reference

| Stage | Description | Common Failure Points |
|-------|-------------|----------------------|
| **Staging** | Job queued, not started | Queue backup, agent issues |
| **Running** | Actively processing documents | Resource constraints, numbering errors |
| **Branding** | Applying headers/footers | Template errors, font issues |
| **Complete** | Successfully finished | - |
| **Complete with Errors** | Finished with some failures | Document-level issues |
| **Error/Failed** | Job-level failure | System errors, configuration issues |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge in monitoring system
- [ ] Note workspace ID, production name, and job ID
- [ ] Open tracking ticket/incident

### Step 2: Access Production Queue
1. Log into RelativityOne admin portal
2. Navigate to **Queue Management** tab
3. Select **Production** queue
4. Locate the failed production job

### Step 3: Quick Status Check

**Record the following:**
- Production Name: ________________
- Workspace ID: ________________
- Job ID: ________________
- Status: ________________
- Priority: ________________
- Documents in Production: ________________
- Error Count: ________________
- Time in Queue: ________________

---

## Investigation Procedures (5-20 minutes)

### Step 4: Access Production Details

**Via UI:**
1. Navigate to the affected workspace
2. Go to **Production** → **Production Sets**
3. Click on the failed production
4. Review **Status** and **Errors** sections

**Via API - Get All Jobs in Queue:**
```bash
curl -X GET "<host>/Relativity.REST/api/relativity-productions/v1/production-queue" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -" \
  -H "Content-Type: application/json"
```

**Response fields to examine:**
```json
{
  "JobID": 12345,
  "ProductionID": 67890,
  "WorkspaceID": 11111,
  "Status": "Error",
  "Errors": ["Error message details"],
  "Priority": 5,
  "SubmittedDate": "2024-01-15T10:30:00Z"
}
```

### Step 5: Identify Error Type

**Check Production Set → Errors tab for specific messages:**

| Error Category | Example Messages | Root Cause |
|----------------|------------------|------------|
| **Numbering Conflicts** | "Duplicate Bates number detected" | Overlapping ranges, previous production |
| **Document Errors** | "Unable to image document" | Corrupt file, imaging failure |
| **Branding Errors** | "Failed to apply branding" | Template issue, font missing |
| **Placeholder Errors** | "Placeholder generation failed" | Native file issues |
| **Storage Errors** | "Insufficient disk space" | Storage capacity |
| **Timeout Errors** | "Operation timed out" | Large documents, resource constraints |

### Step 6: Review Production Configuration

Check these settings for misconfigurations:

**Numbering:**
- [ ] Bates prefix/suffix format valid
- [ ] Starting number doesn't conflict with existing productions
- [ ] Number of digits sufficient for document count

**Branding:**
- [ ] Header/footer templates exist and are valid
- [ ] Fonts are available
- [ ] Placeholders resolve correctly

**Document Selection:**
- [ ] Saved search returns expected results
- [ ] No circular references in document selection
- [ ] Include/exclude family settings correct

### Step 7: Check Related Systems

**Imaging Status:**
- Are source documents imaged?
- Any documents with "Imaging Errors"?

**Native Files:**
- Are natives available for placeholder generation?
- Any missing native files?

---

## Resolution Procedures

### Scenario A: Numbering Conflicts

**Symptoms:** "Duplicate Bates number" or "Number already in use"

**Steps:**
1. Review existing productions in workspace
2. Check the Bates number range used
3. Query for conflicting numbers:

```sql
-- Via Object Manager API, query Document object
-- Filter: Bates Number LIKE 'PREFIX%'
```

4. **Resolution Options:**
   - Adjust starting number to non-conflicting range
   - Update prefix to be unique
   - If duplicate exists in error, delete and re-run

**Fix and Retry:**
1. Navigate to Production Set
2. Edit **Numbering** settings
3. Update starting number or prefix
4. Click **Retry** from Queue Management

### Scenario B: Document-Level Errors

**Symptoms:** "Complete with Errors" status, Errors array populated

**Steps:**
1. Export error report from Production → Errors
2. Categorize by error type
3. Common document issues:

| Issue | Identification | Resolution |
|-------|---------------|------------|
| No image available | "Document has no images" | Run imaging first, or include placeholder |
| Corrupt image | "Invalid image data" | Re-image document |
| Native missing | "Native file not found" | Re-process or exclude |
| Password protected | "Cannot open document" | Provide password, re-image |

4. **Decision Point:**
   - If <1% errors and non-critical: Document and proceed
   - If critical documents: Resolve individually and re-run
   - If systemic issue: Cancel, fix root cause, re-run

### Scenario C: Branding Failures

**Symptoms:** "Failed to apply branding" errors

**Steps:**
1. Navigate to **Production** → **Branding**
2. Verify branding template configuration
3. Check for:
   - Missing or invalid font references
   - Incorrect field placeholders
   - Template syntax errors

4. **Test branding:**
   - Select a small document set
   - Run preview/test production
   - Verify branding appears correctly

5. **Fix and Retry:**
   - Correct template issues
   - Re-run production on failed documents

### Scenario D: Stuck Jobs (No Progress)

**Symptoms:** Job in queue >2 hours, no status change

**Steps:**
1. Check Queue Management for job position
2. Verify Production agents are running:
   - Navigate to **Agents** tab
   - Filter for "Production Manager" agents
   - Check status and last activity

3. Check for blocking jobs:
   - Higher priority jobs consuming resources
   - Large jobs ahead in queue

4. **Options:**
   - **Change Priority:** Elevate stuck job (1=highest)
   - **Cancel and Retry:** Cancel, investigate, re-run
   - **Agent Restart:** If agents unresponsive (escalate first)

**Via API - Change Priority:**
```bash
curl -X POST "<host>/Relativity.REST/api/relativity-productions/v1/production-queue/priority" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -" \
  -H "Content-Type: application/json" \
  -d '{
    "jobId": <JOB_ID>,
    "priority": 1
  }'
```

### Scenario E: System/Infrastructure Errors

**Symptoms:** Generic system errors, database errors, storage errors

**Steps:**
1. Check Instance Details → Alerts for infrastructure issues
2. Review Worker Monitoring for resource utilization
3. Check recent maintenance or deployments

4. **Immediate Actions:**
   - If storage full: Escalate immediately
   - If database errors: Escalate to Relativity Support
   - If agent errors: Check agent status, escalate if down

---

## Queue Management Operations

### Available Mass Operations

| Operation | Use Case | Via API |
|-----------|----------|---------|
| **Retry** | Failed jobs that can be re-attempted | POST /retry |
| **Cancel** | Jobs that should be stopped | POST /cancel |
| **Change Priority** | Reorder queue execution | POST /priority |

### Retry Failed Production

**Via UI:**
1. Queue Management → Production
2. Select failed job
3. Click **Retry**

**Via API:**
```bash
curl -X POST "<host>/Relativity.REST/api/relativity-productions/v1/production-queue/retry" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -" \
  -H "Content-Type: application/json" \
  -d '{"jobId": <JOB_ID>}'
```

### Cancel Production Job

**Via API:**
```bash
curl -X POST "<host>/Relativity.REST/api/relativity-productions/v1/production-queue/cancel" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -" \
  -H "Content-Type: application/json" \
  -d '{"jobId": <JOB_ID>}'
```

---

## Escalation Procedures

### When to Escalate

| Condition | Escalation Level | Timeframe |
|-----------|------------------|-----------|
| Database errors in logs | Relativity Support | Immediate |
| Storage capacity issues | Relativity Support | Immediate |
| Production agents down | Relativity Support | 15 minutes |
| Unresolved after 1 hour | Team Lead | 1 hour |
| Recurring failures (3+ same error) | Root cause analysis | 24 hours |
| Deadline-critical production | Team Lead | Immediate |

### Information for Escalation

- [ ] Production name and workspace ID
- [ ] Job ID from queue
- [ ] Full error messages (copy/screenshot)
- [ ] Production configuration export
- [ ] Document count and production size
- [ ] Timeline and deadline information
- [ ] Steps already attempted

---

## Post-Incident Actions

### Immediate
- [ ] Verify production completed successfully after retry
- [ ] Validate Bates numbering is correct
- [ ] Spot-check branded documents
- [ ] Document resolution in ticket

### Short-term (24 hours)
- [ ] Complete incident report
- [ ] Review production for quality issues
- [ ] Notify stakeholders of completion

### Long-term
- [ ] Update production templates if template issues found
- [ ] Document problematic document types
- [ ] Adjust monitoring thresholds if needed

---

## Prevention Measures

### Pre-Production Checklist
- [ ] Verify Bates range doesn't conflict with existing productions
- [ ] Ensure all documents are imaged (or placeholders configured)
- [ ] Test branding on sample documents
- [ ] Verify saved search returns expected count
- [ ] Confirm sufficient storage capacity
- [ ] Schedule large productions during off-peak hours

### Monitoring Best Practices
- Set alert threshold for jobs in queue >2 hours
- Monitor production agent health daily
- Track production success/failure rates weekly

---

## API Reference

### Production Queue Manager Endpoints

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Get All Jobs | GET | `/relativity-productions/{version}/production-queue` |
| Retry Job | POST | `/relativity-productions/{version}/production-queue/retry` |
| Cancel Job | POST | `/relativity-productions/{version}/production-queue/cancel` |
| Change Priority | POST | `/relativity-productions/{version}/production-queue/priority` |
| Get Production Status | GET | `/relativity-productions/{version}/workspaces/{workspaceId}/productions/{productionId}` |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
