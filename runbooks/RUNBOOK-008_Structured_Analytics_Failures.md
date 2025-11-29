# RUNBOOK-008: RelativityOne Structured Analytics Failures

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Structured Analytics Job Failure |
| **Severity** | CRITICAL (Failed) / HIGH (Errors) / WARNING (Performance) |
| **Platform** | RelativityOne |
| **Detection** | Structured Analytics Job Manager API |
| **Response SLA** | Critical: 15 min / High: 1 hour / Warning: 4 hours |
| **Escalation** | On-call → Team Lead → Relativity Support |

## Alert Conditions

```
IF Status == "Failed" THEN CRITICAL
IF Status == "Cancelled" THEN HIGH
IF ErrorMessages != null THEN CRITICAL
IF PercentComplete stuck at same value > 30 min THEN WARNING
IF Job_Duration > expected_threshold THEN WARNING
```

## Structured Analytics Operations

| Operation | Purpose | Typical Duration |
|-----------|---------|------------------|
| **Email Threading** | Groups email conversations | Medium-Long |
| **Textual Near-Duplicate Detection** | Finds similar documents | Long |
| **Language Identification** | Detects document languages | Short |
| **Repeated Content Identification** | Finds boilerplate text | Medium |
| **Name Normalization** | Standardizes entity names | Short-Medium |
| **Clustering** | Groups conceptually similar docs | Long |

---

## Analytics Infrastructure Requirements

### Agent Requirements

| Agent | Count | RAM | Notes |
|-------|-------|-----|-------|
| Analytics Cluster Manager | 1 per Analytics server | - | Manages cluster operations |
| Content Analyst Index Manager | 1 per Analytics server | - | Manages CA indexes |
| Analytics Categorization Manager | 2 per Analytics server | - | Handles categorization |
| Structured Analytics Workers | Minimum 4 | 1 GB each | Process analytics jobs |

### MaxAnalyticsIndexIdleDays Setting
Automatically disables unused analytics indexes after specified days. Monitor for:
- Unexpectedly disabled indexes
- Indexes approaching idle threshold

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge in monitoring system
- [ ] Note workspace ID, analytics set name, operation type
- [ ] Open tracking ticket

### Step 2: Quick Status Check

**Via UI:**
1. Navigate to affected workspace
2. Go to **Structured Analytics Set**
3. Review current job status
4. Check for error messages

**Record the following:**
- Analytics Set Name: ________________
- Workspace ID: ________________
- Operation Type: ________________
- Status: ________________
- Percent Complete: ________________
- Error Messages: ________________
- Start Time: ________________

---

## Investigation Procedures (5-20 minutes)

### Step 3: Query Job Status via API

```bash
curl -X POST "<host>/Relativity.REST/api/relativity-structuredanalytics/v1/workspaces/<WORKSPACE_ID>/jobs/<JOB_ID>/status" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -" \
  -H "Content-Type: application/json"
```

**Response fields:**
```json
{
  "JobID": 12345,
  "Status": "Failed",
  "PercentComplete": 45,
  "ErrorMessages": ["Error details here"],
  "StartTime": "2024-01-15T10:00:00Z",
  "EndTime": null
}
```

### Step 4: Check Analytics Agents

1. Navigate to **Agents** tab
2. Check status of:
   - Analytics Cluster Manager
   - Content Analyst Index Manager
   - Analytics Categorization Manager

3. Verify agents are:
   - Enabled
   - Running or Idle
   - Recent last activity

### Step 5: Check Worker Health

1. Navigate to **Worker Monitoring**
2. Review Structured Analytics workers:
   - Minimum 4 workers required
   - Each should have 1 GB RAM allocated
   - Check status: Idle/Running (not "Service not responding")

### Step 6: Review Analytics Set Configuration

Check for configuration issues:
- Data source (saved search) returns expected documents
- Population settings are correct
- No circular references in configuration

---

## Resolution Procedures

### Scenario A: Job Failed (Status = "Failed")

**Symptoms:** Job status is "Failed", ErrorMessages populated

**Steps:**
1. Review error messages in detail
2. Common failure causes:

| Error | Cause | Resolution |
|-------|-------|------------|
| "Agent not responding" | Analytics agent down | Check agent status, escalate |
| "Insufficient resources" | Memory/CPU exhaustion | Reduce concurrent load |
| "Index error" | Content Analyst index issue | Rebuild CA index |
| "Database error" | SQL connectivity | Escalate to support |
| "Timeout" | Operation exceeded time limit | Break into smaller batches |

3. **After fixing root cause:**
   - Navigate to Structured Analytics Set
   - Click **Run** to restart operation

### Scenario B: Job Cancelled

**Symptoms:** Status = "Cancelled"

**Steps:**
1. Determine who/what cancelled:
   - Manual cancellation?
   - System cancellation due to error?
   - Timeout?

2. Review audit trail for cancellation event
3. If unintentional: Re-run the job
4. If system-cancelled: Investigate root cause

### Scenario C: Job Stuck (No Progress)

**Symptoms:** PercentComplete unchanged for >30 minutes

**Steps:**
1. Check worker status in Worker Monitoring
2. Verify analytics agents are processing
3. Check for:
   - Very large documents being analyzed
   - Resource contention
   - Agent issues

4. **Options:**
   - Wait (large operations take time)
   - Cancel and retry with smaller batch
   - Escalate if workers unresponsive

### Scenario D: Email Threading Failures

**Symptoms:** Email threading operation failed or incomplete

**Common Issues:**

| Issue | Identification | Resolution |
|-------|---------------|------------|
| Missing email headers | "Unable to identify conversation" | Check email metadata fields |
| Circular threading | "Circular reference detected" | Review data, may need cleanup |
| Large thread groups | Performance degradation | Consider batch processing |
| Non-email documents | "Not an email document" | Filter saved search to emails only |

**Steps:**
1. Verify saved search contains only email documents
2. Check that required email metadata fields are populated
3. Review threading settings
4. Re-run on corrected document set

### Scenario E: Near-Duplicate Detection Issues

**Symptoms:** Near-duplicate operation failed or produced unexpected results

**Common Issues:**

| Issue | Cause | Resolution |
|-------|-------|------------|
| Too many duplicates | Threshold too low | Adjust similarity threshold |
| No duplicates found | Threshold too high | Lower similarity threshold |
| Job timeout | Large document set | Process in smaller batches |
| Memory errors | Complex documents | Check worker resources |

**Threshold Guidance:**
- 90-100%: Very strict (nearly identical)
- 80-90%: Moderate (some variation allowed)
- <80%: Loose (may produce false positives)

### Scenario F: Content Analyst Index Issues

**Symptoms:** Operations failing with index-related errors

**Steps:**
1. Check Content Analyst Index status
2. Common issues:
   - Index not built
   - Index out of sync
   - Index corruption

3. **Resolution:**
   - Rebuild Content Analyst Index
   - Wait for rebuild to complete
   - Re-run analytics operation

---

## Analytics-Specific Agent Management

### Analytics Cluster Manager
- **Count:** 1 per Analytics server
- **Purpose:** Manages Analytics cluster operations
- **Impact if down:** All analytics operations affected

### Content Analyst Index Manager
- **Count:** 1 per Analytics server
- **Purpose:** Manages Content Analyst indexes
- **Impact if down:** Index operations fail

### Analytics Categorization Manager
- **Count:** 2 per Analytics server
- **Purpose:** Handles document categorization
- **Impact if down:** Categorization fails

### Structured Analytics Workers
- **Minimum:** 4 workers
- **RAM:** 1 GB each
- **Impact if insufficient:** Performance degradation, timeouts

---

## Performance Optimization

### Pre-Job Planning
- Estimate document set size
- Schedule during off-peak hours
- Ensure adequate worker resources
- Consider batch processing for large sets

### Resource Allocation

| Document Count | Recommended Workers | Expected Duration |
|---------------|---------------------|-------------------|
| <100,000 | 4 (minimum) | Hours |
| 100,000-500,000 | 6-8 | Hours to Day |
| 500,000-1,000,000 | 8-12 | Day to Days |
| >1,000,000 | 12+ | Days |

### Batch Processing
For very large document sets:
1. Divide into logical batches (by custodian, date range, etc.)
2. Process batches sequentially
3. Combine results as needed

---

## Escalation Procedures

### When to Escalate

| Condition | Level | Timeframe |
|-----------|-------|-----------|
| Workers "Service not responding" | Relativity Support | Immediate |
| Persistent agent failures | Relativity Support | 30 min |
| Database errors | Relativity Support | Immediate |
| Unresolved after 2 hours | Team Lead | 2 hours |
| Deadline-critical analytics | Team Lead | Immediate |

### Information for Escalation

- [ ] Analytics Set name and workspace ID
- [ ] Job ID and operation type
- [ ] Error messages (full text)
- [ ] Worker status screenshots
- [ ] Agent status
- [ ] Document count and set configuration
- [ ] Timeline and deadline info

---

## Post-Incident Actions

### Immediate
- [ ] Verify analytics job completed successfully
- [ ] Validate results (spot-check threading, duplicates, etc.)
- [ ] Document resolution

### Short-term (24 hours)
- [ ] Complete incident report
- [ ] Review analytics set configuration
- [ ] Check for similar issues in other workspaces

### Long-term
- [ ] Optimize analytics set configurations
- [ ] Adjust worker allocation if needed
- [ ] Update monitoring thresholds

---

## Prevention Measures

### Pre-Analytics Checklist
- [ ] Verify document count is reasonable
- [ ] Check saved search returns expected results
- [ ] Ensure workers have adequate resources
- [ ] Schedule during appropriate time window
- [ ] Notify team of large operations

### Monitoring Setup
- Alert on Failed status
- Alert on stuck jobs (no progress >30 min)
- Monitor worker resource utilization
- Track job duration trends

### Capacity Planning
- Review worker allocation quarterly
- Plan for large matters in advance
- Consider dedicated analytics windows

---

## API Reference

### Structured Analytics Job Manager

```bash
# Get job status
POST /Relativity.REST/api/relativity-structuredanalytics/{version}/workspaces/{workspaceID}/jobs/{jobID}/status

# Get analytics set details
GET /Relativity.REST/api/relativity-structuredanalytics/{version}/workspaces/{workspaceID}/analyticssets/{setID}
```

### Query for Failed Jobs

```bash
# Via Object Manager - query Analytics Job objects
POST /Relativity.Rest/api/Relativity.ObjectManager/{version}/workspace/{workspaceID}/object/query

{
  "request": {
    "objectType": {"Name": "Structured Analytics Job"},
    "fields": [
      {"Name": "Status"},
      {"Name": "Operation Type"},
      {"Name": "Error Messages"}
    ],
    "condition": "'Status' IN ['Failed', 'Cancelled']"
  }
}
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
