# RUNBOOK-AIR-001: aiR for Review Job Failures

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | aiR for Review Job Failure |
| **Severity** | CRITICAL / HIGH |
| **Platform** | RelativityOne - aiR for Review |
| **Detection** | aiR for Review Jobs Tab / Object Manager API |
| **Response SLA** | 15 minutes (CRITICAL), 1 hour (HIGH) |
| **Escalation** | On-call → Team Lead → Relativity Support |

## Alert Conditions

This runbook is triggered when any of the following conditions are detected:

```
IF Job_Status == "Errored" THEN CRITICAL
IF (Docs_Errored / Doc_Count) > 0.10 THEN HIGH
IF (Docs_Errored / Doc_Count) > 0.05 THEN WARNING
IF Job_Status == "In Progress" AND Duration > 4 * Estimated_Run_Time THEN HIGH
IF Job_Status == "Queued" AND Wait_Time > 2 hours THEN WARNING
IF Job_Status == "Cancelling" for > 30 minutes THEN MEDIUM
```

## aiR for Review Overview

aiR for Review uses Azure OpenAI's GPT-4 Omni model to analyze documents against user-provided prompt criteria. Understanding its architecture helps diagnose failures:

| Component | Description | Failure Impact |
|-----------|-------------|----------------|
| **Prompt Criteria** | User-defined review instructions | Poor results, not system errors |
| **LLM Analysis** | GPT-4 Omni document processing | API errors, timeouts |
| **Citation Verification** | Validates up to 5 citations per doc | Hallucination detection |
| **Results Population** | Writes to document fields | Database/field mapping errors |

### Job Output Fields

| Field | Description |
|-------|-------------|
| **Citations** | Text excerpts supporting relevance |
| **Considerations** | Potential error explanations |
| **Recommendation** | Relevant / Not Relevant / Borderline |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge in monitoring system to prevent duplicate notifications
- [ ] Note the Job ID, Workspace, and timestamp from the alert
- [ ] Open a tracking ticket/incident

### Step 2: Access aiR for Review Jobs Tab

**Via Instance-Level Tab (recommended for initial triage):**
1. Log into RelativityOne
2. Navigate to **Instance Details** → **aiR for Review Jobs**
3. This shows the most recent 100 jobs across all workspaces
4. Locate the failed job by Job ID or timestamp

**Via Workspace-Level Tab:**
1. Navigate to the affected workspace
2. Go to **aiR for Review** → **Jobs**
3. All jobs for this workspace are displayed

### Step 3: Quick Status Assessment

**Record the following:**
- Job ID: ________________
- Project Name: ________________
- Workspace ID/Name: ________________
- Job Status: ________________
- Doc Count: ________________
- Docs Successful: ________________
- Docs Errored: ________________
- Docs Skipped: ________________
- Job Failure Reason: ________________
- Submitted Time: ________________

---

## Investigation Procedures (5-20 minutes)

### Step 4: Analyze Job Failure Reason

**Common Job Failure Reasons:**

| Failure Reason | Likely Cause | Investigation Path |
|----------------|--------------|-------------------|
| "Network error" | Azure OpenAI connectivity | Check platform status |
| "Timeout" | Large document or API latency | Review document sizes |
| "Rate limit exceeded" | Too many concurrent requests | Check instance capacity |
| "Invalid response" | LLM returned unexpected format | May require retry |
| "Internal error" | Platform issue | Escalate to Relativity |

### Step 5: Review Document-Level Errors

1. In the aiR for Review Jobs tab, click on the failed job
2. Review **Docs Errored** and **Docs Skipped** counts
3. Compare to total **Doc Count** to calculate error rate

**Error Rate Interpretation:**

| Error Rate | Assessment | Action |
|------------|------------|--------|
| < 1% | Normal | Document errors, proceed |
| 1-5% | Elevated | Review error patterns |
| 5-10% | Concerning | Investigate root cause |
| > 10% | Critical | Halt and investigate |

### Step 6: Identify Error Patterns

**Documents may be errored or skipped due to:**

| Category | Cause | Identification |
|----------|-------|----------------|
| **Cancellation** | Job was cancelled mid-run | Check for "Cancelling" history |
| **Network Errors** | Connectivity issues during processing | Clustered timestamps |
| **Partial Failure** | Some docs processed before failure | Check Docs Successful |
| **Document Content** | Empty/corrupt extracted text | Review document properties |
| **Size Limits** | Document exceeds processing limits | Check extracted text size |

### Step 7: Check Prompt Criteria

1. Click on the job to view **Prompt Criteria Name** and **Version**
2. Review the prompt criteria configuration
3. Verify analysis type matches intended use:
   - **Relevance**: Responsive document identification
   - **Key Documents**: "Hot" document discovery
   - **Issues**: Document categorization

**Note:** Prompt criteria issues typically cause poor results, not job failures. If the job errored, the issue is likely infrastructure-related.

---

## Resolution Procedures

### Scenario A: Job Status "Errored"

**Symptoms:** Job_Status == "Errored" with Job Failure Reason populated

**Steps:**
1. Review the Job Failure Reason field
2. Check RelativityOne Instance Alerts for platform issues
3. Verify Azure OpenAI service status (if available)

**Resolution by Failure Type:**

| Failure Type | Resolution |
|--------------|------------|
| Network/Timeout | Wait 15 minutes, retry job |
| Rate Limit | Reduce concurrent aiR jobs, retry |
| Internal Error | Contact Relativity Support |
| Invalid Response | Retry once; if persistent, escalate |

**To Retry:**
1. Return to the aiR for Review project
2. Navigate to the same Saved Search and prompt criteria
3. Submit a new job
4. Monitor progress

### Scenario B: High Document Error Rate (>10%)

**Symptoms:** (Docs_Errored / Doc_Count) > 0.10

**Steps:**
1. Export the error details if available
2. Identify common characteristics of errored documents:
   - File types
   - Document sizes
   - Source systems
3. Check for extracted text issues:
   - Empty extracted text
   - Extremely large extracted text (>170KB typically problematic)
   - Non-English content (if prompt is English-only)

**Resolution:**
1. Create a new Saved Search excluding problematic documents
2. Re-run aiR for Review on the filtered set
3. Handle excluded documents separately (manual review)

### Scenario C: Stuck Job (In Progress Too Long)

**Symptoms:** Job running significantly longer than estimated

**Steps:**
1. Check **Estimated Run Time** vs actual elapsed time
2. Review **Docs Pending** - should be decreasing
3. If Docs Pending is static for >30 minutes, job may be stuck

**Resolution:**
1. Cancel the job via the aiR for Review Jobs tab
2. Wait for "Cancelling" to complete
3. Note: Partial results are preserved and billed
4. Re-run with smaller document batches if needed

### Scenario D: Extended Queue Wait

**Symptoms:** Job_Status == "Queued" for >2 hours

**Steps:**
1. Check **Estimated Wait Time** in the Jobs tab
2. Review instance-level capacity via Instance Jobs tab
3. Identify if volume limits are being approached

**Resolution:**
1. Wait for queue to clear (no action needed)
2. If urgent, contact Relativity Support for capacity assistance
3. Consider scheduling large jobs during off-peak hours

### Scenario E: Skipped Documents

**Symptoms:** Docs_Skipped > 0 (expected to be minimal)

**Causes:**
- Job cancellation mid-processing
- Network errors during specific document processing
- Documents with no extracted text

**Resolution:**
1. Review skipped document characteristics
2. If due to cancellation, re-run job
3. If content issues, exclude from future runs

---

## Escalation Procedures

### When to Escalate to Relativity Support

| Condition | Action |
|-----------|--------|
| Job Failure Reason indicates "Internal error" | Immediate escalation |
| Multiple jobs failing with same error | Escalate within 30 minutes |
| Error rate >10% with no obvious cause | Escalate within 1 hour |
| Stuck job that won't cancel | Immediate escalation |
| Platform-wide aiR issues | Immediate escalation |

### Escalation Contacts

| Level | Contact | Response Time |
|-------|---------|---------------|
| Tier 1 | On-call engineer | 15 minutes |
| Tier 2 | Team Lead | 30 minutes |
| Tier 3 | Relativity Support (support@relativity.com) | Per SLA |

### Information to Gather Before Escalation

- [ ] Job ID
- [ ] Workspace ID and name
- [ ] Project Name and Prompt Criteria Name
- [ ] Job Failure Reason (exact text)
- [ ] Doc Count, Docs Successful, Docs Errored, Docs Skipped
- [ ] Submitted Time and failure time
- [ ] Screenshots of Jobs tab
- [ ] Error patterns if identified
- [ ] Recent changes to prompt criteria or saved search

---

## Post-Incident Actions

### Immediate (within 1 hour of resolution)
- [ ] Verify replacement job completed successfully
- [ ] Confirm results populated to document fields
- [ ] Document resolution in incident ticket
- [ ] Notify affected project team

### Short-term (within 24 hours)
- [ ] Complete incident report
- [ ] Review billing impact (partial runs are billed)
- [ ] Update prompt criteria if issues identified
- [ ] Review related workspaces for similar issues

### Long-term (within 1 week)
- [ ] Analyze error patterns for prevention
- [ ] Update monitoring thresholds if needed
- [ ] Document problematic document types for future exclusion
- [ ] Share lessons learned with team

---

## Prevention Measures

### Pre-Job Validation
- Run aiR on small sample sets first (Develop phase)
- Validate prompt criteria with diverse documents
- Check saved search for extracted text completeness
- Ensure documents are within size limits

### Capacity Planning
- Monitor instance-level job counts
- Schedule large jobs during off-peak hours
- Coordinate with other teams on aiR usage
- Track volume limits via Instance Jobs tab

### Best Practices
- Use Develop → Validate → Apply workflow
- Start with smaller document sets and scale up
- Document prompt criteria versions and results
- Maintain baseline metrics for typical error rates

---

## API Reference

### Query aiR for Review Jobs

```bash
# Instance-level job query
curl -X POST "<host>/Relativity.REST/api/Relativity.Objects/workspace/-1/object/query" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -" \
  -H "Content-Type: application/json" \
  -d '{
    "request": {
      "objectType": {"Name": "aiR for Review Job"},
      "fields": [
        {"Name": "Name"},
        {"Name": "Job Status"},
        {"Name": "Doc Count"},
        {"Name": "Docs Successful"},
        {"Name": "Docs Errored"},
        {"Name": "Docs Skipped"},
        {"Name": "Submitted Time"},
        {"Name": "Completed Time"},
        {"Name": "Job Failure Reason"},
        {"Name": "Workspace"},
        {"Name": "Prompt Criteria Name"}
      ],
      "condition": "'Job Status' == 'Errored'",
      "sorts": [{"FieldIdentifier": {"Name": "Submitted Time"}, "Direction": "Descending"}]
    },
    "start": 0,
    "length": 100
  }'
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-30 | - | Initial runbook |
