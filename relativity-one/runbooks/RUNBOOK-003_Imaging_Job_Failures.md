# RUNBOOK-003: RelativityOne Imaging Job Failures

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Imaging Job Failure |
| **Severity** | CRITICAL (Error) / HIGH (Completed with Errors) |
| **Platform** | RelativityOne |
| **Detection** | Imaging Job Manager API |
| **Response SLA** | 15 minutes (Critical) / 1 hour (High) |
| **Escalation** | On-call → Team Lead → Relativity Support |

## Alert Conditions

```
IF Status == "Error" THEN CRITICAL
IF Status == "Completed with Errors" THEN HIGH
IF # documents with errors > threshold THEN HIGH
IF Last Run Error != null THEN CRITICAL
IF Status == "Imaging" for > 4 hours (stuck) THEN WARNING
```

## Imaging Status Reference

| Status | Meaning | Alert Level |
|--------|---------|-------------|
| Staging | Job started, not submitted | Info |
| Preparing files | Splitting into batches | Info |
| Submitting | Documents going to queue | Info |
| Imaging | Active processing | Info (monitor duration) |
| Completed | Success | None |
| Completed with Errors | Partial success | HIGH |
| Error | Job failed | CRITICAL |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge in monitoring system
- [ ] Note workspace ID and imaging set name
- [ ] Open tracking ticket

### Step 2: Quick Status Check

**Via UI:**
1. Navigate to affected workspace
2. Go to **Imaging** → **Imaging Sets**
3. Select the failed imaging set
4. Note status and error count

**Record the following:**
- Imaging Set Name: ________________
- Workspace ID: ________________
- Status: ________________
- Total Documents: ________________
- Documents with Errors: ________________
- Imaging Profile: ________________
- Last Run Error: ________________

### Step 3: Check Queue Management
1. Navigate to **Queue Management** → **Processing and Imaging**
2. Locate imaging job
3. Check position in queue and priority

---

## Investigation Procedures (5-20 minutes)

### Step 4: Access Imaging Set Details

**Via API:**
```bash
# Get imaging set status
curl -X GET "<host>/Relativity.Rest/API/relativity-imaging/v1/workspaces/<WORKSPACE_ID>/imagingsets/<IMAGING_SET_ID>" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -"
```

**Response fields:**
```json
{
  "ImagingSetID": 12345,
  "Name": "Imaging Set Name",
  "Status": "Completed with Errors",
  "LastRunError": "Error details",
  "TotalDocuments": 10000,
  "DocumentsWithErrors": 150,
  "ImagingProfile": {...},
  "EmailNotificationRecipients": "user@example.com"
}
```

### Step 5: Get Document-Level Imaging Status

**Via API:**
```bash
# Get individual document imaging status
curl -X GET "<host>/Relativity.Rest/api/relativity-imaging/v1/workspaces/<WORKSPACE_ID>/documents/<DOCUMENT_ARTIFACT_ID>/status" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -"
```

### Step 6: Analyze Error Patterns

**Export error list from Imaging Set:**
1. Navigate to Imaging Set → **Errors** tab
2. Export to Excel for analysis
3. Categorize errors by type

**Common Imaging Error Types:**

| Error Type | Description | Frequency |
|------------|-------------|-----------|
| Password Protected | File requires password | High |
| Corrupt File | File cannot be read | Medium |
| Unsupported Format | File type not imageable | Medium |
| Timeout | Large/complex file exceeded time limit | Low |
| Memory Error | Document too large for available memory | Low |
| Font Error | Missing fonts in Office documents | Low |
| Rendering Error | Unable to render document | Medium |

### Step 7: Check Imaging Profile Settings

Review imaging profile for potential issues:

| Setting | Check For |
|---------|-----------|
| Native Types | Correct file types selected for native imaging |
| Basic Options | DPI, paper size, orientation settings |
| Spreadsheet Options | Row/column limits, print area settings |
| Email Options | Include attachments, show BCC |
| HTML Options | Remove active content settings |
| Word Options | Show tracked changes settings |
| Presentation Options | Show speaker notes settings |

---

## Resolution Procedures

### Scenario A: Job-Level Error (Status = "Error")

**Symptoms:** Entire imaging set failed, `Last Run Error` populated

**Steps:**
1. Review `Last Run Error` message
2. Common job-level failures:

| Error | Cause | Resolution |
|-------|-------|------------|
| "Agent not responding" | Imaging agent down | Check agent status, escalate |
| "Database error" | SQL connectivity | Escalate to support |
| "Storage error" | Disk full/unavailable | Escalate immediately |
| "Configuration error" | Invalid imaging profile | Review and fix profile |

3. **After fixing root cause:**
   - Navigate to Imaging Set
   - Click **Run** to restart imaging

### Scenario B: Completed with Errors (Partial Success)

**Symptoms:** Status = "Completed with Errors", `Documents with Errors` > 0

**Steps:**
1. Calculate error percentage: `(Documents with Errors / Total Documents) × 100`

2. **Decision Matrix:**

| Error % | Action |
|---------|--------|
| < 1% | Document errors, proceed if non-critical |
| 1-5% | Investigate top error types, retry if possible |
| 5-10% | Major investigation, may need profile adjustment |
| > 10% | Stop, investigate systemic issues |

3. **For password-protected files:**
   - Navigate to **Processing** → **Password Bank**
   - Add known passwords
   - Re-image affected documents

4. **For corrupt/unsupported files:**
   - Document in project records
   - Determine if documents are critical
   - Options: Placeholder, native-only, exclude

5. **Retry errored documents:**
   - Select imaging set
   - Click **Image Documents with Errors**

### Scenario C: Stuck Imaging Job

**Symptoms:** Status = "Imaging" for extended period (>4 hours)

**Steps:**
1. Check Queue Management for job status
2. Verify imaging workers are healthy:
   - Navigate to **Worker Monitoring**
   - Check threads in use, memory, CPU
   - Look for "Service not responding"

3. Check for blocking conditions:
   - Very large documents (>1GB)
   - Complex Office files with many embedded objects
   - Corrupted files causing worker hangs

4. **Options:**
   - Wait for timeout (system will handle)
   - Cancel and re-run (if deadline pressure)
   - Escalate if workers unresponsive

**Note:** Imaging Manager agent runs at default 3600-second (1 hour) intervals and automatically cleans up stuck jobs. Do NOT modify this interval.

### Scenario D: High Error Rate on Specific File Types

**Symptoms:** Errors concentrated on particular file types (e.g., all XLS, all MSG)

**Steps:**
1. Review imaging profile for that file type
2. Check profile settings:

**For Spreadsheets:**
- Adjust page width/column limits
- Check "Limit spreadsheet rows" setting
- Verify print area configuration

**For Emails:**
- Check MSG/PST handling settings
- Verify attachment imaging settings
- Review metadata rendering options

**For PDFs:**
- Check "Native imaging for PDFs" setting
- Verify corruption handling

3. Update imaging profile if needed
4. Re-image affected documents

---

## Native Email Notifications

**Imaging Sets support native email alerts.** Unlike other job types, you can configure automatic notifications.

**To Configure:**
1. Open Imaging Set
2. Locate **Email Notification Recipients** field
3. Enter semicolon-delimited email addresses:
   ```
   admin1@company.com;admin2@company.com;oncall@company.com
   ```
4. Emails sent on:
   - Completion (success)
   - Completion with errors
   - Failure

**Recommendation:** Configure this for all production imaging sets as a backup to SIEM alerting.

---

## Queue Management Operations

### From Queue Management Tab

| Operation | Description |
|-----------|-------------|
| Cancel | Stop imaging job |
| Resume | Continue paused job |
| Change Priority | Adjust queue position (1=highest, 10=lowest) |

### Via API

**Get Imaging Queue Status:**
```bash
curl -X GET "<host>/Relativity.Rest/API/relativity-imaging/v1/workspaces/<WORKSPACE_ID>/imagingsets/<IMAGING_SET_ID>/status" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -"
```

---

## Escalation Procedures

### When to Escalate

| Condition | Level | Timeframe |
|-----------|-------|-----------|
| Workers "Service not responding" | Relativity Support | Immediate |
| Database errors | Relativity Support | Immediate |
| Storage errors | Relativity Support | Immediate |
| Job stuck >4 hours | Team Lead | 4 hours |
| Error rate >10% | Team Lead | 1 hour |
| Not resolved in 2 hours | Team Lead | 2 hours |
| Deadline-critical imaging | Team Lead | Immediate |

### Information for Escalation

- [ ] Imaging Set name and ID
- [ ] Workspace ID
- [ ] Total documents and error count
- [ ] Error export (Excel)
- [ ] Imaging profile configuration
- [ ] Worker status screenshots
- [ ] Timeline and deadline info

---

## Post-Incident Actions

### Immediate
- [ ] Verify imaging completed (or errors acceptable)
- [ ] Spot-check imaged documents for quality
- [ ] Document resolution

### Short-term (24 hours)
- [ ] Complete incident report
- [ ] Review error patterns for prevention
- [ ] Update password bank if passwords discovered

### Long-term
- [ ] Tune imaging profiles based on lessons learned
- [ ] Document problematic file types per client
- [ ] Adjust monitoring thresholds

---

## Prevention Measures

### Pre-Imaging Checklist
- [ ] Review saved search document count
- [ ] Check for known problematic file types
- [ ] Verify imaging profile is appropriate
- [ ] Ensure password bank is populated
- [ ] Configure email notification recipients
- [ ] Schedule large jobs during off-peak hours

### Imaging Profile Best Practices
- Create client/matter-specific profiles
- Test profiles with sample documents first
- Document optimal settings for common file types
- Review and update profiles quarterly

### Monitoring Setup
- Alert on error rate >5%
- Alert on jobs stuck >4 hours
- Monitor imaging queue depth
- Track daily imaging throughput

---

## API Reference

### Imaging Job Manager Endpoints

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Get Imaging Set | GET | `/relativity-imaging/{version}/workspaces/{workspaceId}/imagingsets/{imagingSetId}` |
| Get Document Status | GET | `/relativity-imaging/{version}/workspaces/{workspaceId}/documents/{docId}/status` |
| Run Imaging Set | POST | `/relativity-imaging/{version}/workspaces/{workspaceId}/imagingsets/{imagingSetId}/run` |
| Image Error Documents | POST | `/relativity-imaging/{version}/workspaces/{workspaceId}/imagingsets/{imagingSetId}/imageerrors` |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
