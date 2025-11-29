# RUNBOOK-011: RelativityOne OCR Job Failures

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | OCR Job Failure |
| **Severity** | HIGH (Job Failed) / MEDIUM (Errors) / WARNING (Performance) |
| **Platform** | RelativityOne |
| **Detection** | Queue Management + OCR Set Status |
| **Response SLA** | High: 1 hour / Medium: 4 hours / Warning: Next business day |
| **Escalation** | On-call → Team Lead → Relativity Support |

## Alert Conditions

```
IF OCR_Job_Status == "Error" THEN HIGH
IF OCR_Job_Status == "Completed with Errors" AND Error_Rate > 5% THEN HIGH
IF OCR_Job_Status == "Completed with Errors" THEN MEDIUM
IF OCR_Job_Duration > expected_threshold THEN WARNING
IF OCR_Queue_Depth > threshold THEN WARNING
```

---

## OCR Set Status Reference

| Status | Meaning | Alert Level |
|--------|---------|-------------|
| Waiting | Queued for processing | Info |
| Processing | Actively running OCR | Info |
| Completed | Success | None |
| Completed with Errors | Some documents failed | MEDIUM/HIGH |
| Error | Job-level failure | HIGH |
| Cancelled | Job was cancelled | Warning |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge in monitoring system
- [ ] Note workspace ID, OCR set name
- [ ] Open tracking ticket

### Step 2: Quick Status Check

**Via Queue Management:**
1. Navigate to **Queue Management** tab
2. Select **OCR** queue
3. Check job status and position

**Via Workspace:**
1. Navigate to affected workspace
2. Go to **OCR** → **OCR Sets**
3. Review set status and error count

**Record the following:**
- OCR Set Name: ________________
- Workspace ID: ________________
- Status: ________________
- Total Documents: ________________
- Documents with Errors: ________________
- OCR Profile: ________________

---

## Investigation Procedures

### Step 3: Review OCR Set Details

**Check OCR Set configuration:**
1. Navigate to OCR Set
2. Review:
   - Saved search (data source)
   - OCR profile settings
   - Destination text field
   - Error details

### Step 4: Analyze Error Patterns

**Common OCR Errors:**

| Error Type | Cause | Resolution |
|------------|-------|------------|
| Image quality too low | Poor scan quality | Re-scan or accept limitation |
| Unsupported format | File type not OCR-able | Document and exclude |
| Language not supported | Document in unsupported language | Check OCR profile language settings |
| File corrupt | Damaged image file | Re-process source file |
| Timeout | Complex/large document | May need manual handling |
| Password protected | Encrypted document | Provide password |

### Step 5: Check OCR Queue Health

**Via Queue Management:**
1. Review queue depth
2. Check processing rate
3. Identify any stuck jobs
4. Note priority settings

**Queue Management Operations Available:**
- Change priority

---

## Resolution Procedures

### Scenario A: Job-Level Error

**Symptoms:** OCR Set status = "Error"

**Steps:**
1. Review error message in OCR Set details
2. Common causes:

| Error | Cause | Resolution |
|-------|-------|------------|
| Agent error | OCR agent down | Check agent status |
| Profile error | Invalid OCR profile | Review profile settings |
| Field error | Destination field issue | Verify text field exists |
| Resource error | System resources | Escalate if persistent |

3. **After fixing root cause:**
   - Click **Run** on OCR Set to retry
   - Or create new OCR Set if configuration was issue

### Scenario B: Completed with Errors (High Error Rate)

**Symptoms:** >5% documents with errors

**Steps:**
1. Export error report
2. Categorize by error type
3. Identify patterns:
   - Same file type failing?
   - Same custodian?
   - Same date range?

4. **Resolution by pattern:**

| Pattern | Resolution |
|---------|------------|
| Image quality | Accept or re-scan |
| Language | Update OCR profile |
| File format | Document limitation |
| Specific files | Manual handling |

5. **Retry errored documents:**
   - Create saved search for failed documents
   - Create new OCR Set targeting those documents

### Scenario C: OCR Taking Too Long

**Symptoms:** Job running longer than expected

**Factors affecting OCR duration:**
- Document count
- Image quality
- Document complexity
- System load

**Steps:**
1. Check Queue Management for position and priority
2. Review document count and types
3. Check for concurrent heavy operations
4. Options:
   - Wait (may be normal)
   - Change priority if urgent
   - Cancel and retry during off-peak

### Scenario D: Poor OCR Quality

**Symptoms:** OCR completed but text quality is poor

**Investigation:**
1. Review source document quality
2. Check OCR profile settings:
   - Accuracy vs. speed setting
   - Language configuration
   - Auto-rotate settings

**Resolution:**
- Adjust OCR profile for accuracy
- Consider professional scanning for critical documents
- Document limitations for QC team

---

## OCR Profile Optimization

### Profile Settings Impact

| Setting | Impact |
|---------|--------|
| Accuracy mode | Better results, slower |
| Speed mode | Faster, may miss complex text |
| Auto-rotate | Helps with mixed orientations |
| Language pack | Essential for non-English |
| Despeckle | Helps with noisy images |

### Recommended Configurations

| Document Type | Recommended Settings |
|---------------|---------------------|
| Clean typed docs | Speed mode, auto-rotate |
| Handwritten notes | Accuracy mode |
| Mixed languages | Multi-language profile |
| Poor quality scans | Accuracy, despeckle |
| Legacy faxes | Accuracy, despeckle, auto-rotate |

---

## Queue Management

### Available Operations

| Operation | Use Case |
|-----------|----------|
| Change Priority | Expedite urgent jobs (1=highest) |

### Priority Guidelines
- **Priority 1:** Deadline-critical, client-facing
- **Priority 5:** Standard processing (default)
- **Priority 10:** Low priority, can wait

---

## Escalation Procedures

### When to Escalate

| Condition | Level | Timeframe |
|-----------|-------|-----------|
| All OCR jobs failing | Relativity Support | Immediate |
| Agent issues | Relativity Support | 30 min |
| Error rate >20% | Team Lead | 2 hours |
| Deadline impact | Team Lead | Immediate |
| Persistent queue backup | Team Lead | 4 hours |

### Information for Escalation

- [ ] OCR Set name and workspace ID
- [ ] Error messages
- [ ] Document count and error rate
- [ ] OCR profile configuration
- [ ] Sample failed documents (if possible)
- [ ] Queue status

---

## Post-Incident Actions

### Immediate
- [ ] Verify OCR completed successfully
- [ ] Spot-check OCR quality
- [ ] Document resolution

### Short-term (24 hours)
- [ ] Complete incident report
- [ ] Review OCR profiles
- [ ] Update for problem document types

### Long-term
- [ ] Optimize OCR profiles
- [ ] Document limitations
- [ ] Training on OCR best practices

---

## Prevention Measures

### Pre-OCR Checklist
- [ ] Verify document types are suitable for OCR
- [ ] Check saved search document count
- [ ] Select appropriate OCR profile
- [ ] Schedule during off-peak if large

### Quality Assurance
- Spot-check OCR results
- Compare against original documents
- Document error patterns
- Adjust profiles based on results

### Monitoring
- Alert on error rate >5%
- Monitor queue depth
- Track average OCR duration
- Review error patterns weekly

---

## API Reference

### Queue Monitoring
OCR queue is visible in Queue Management but has limited API exposure. Primary monitoring through:
- Queue Management UI
- OCR Set status in workspace

### Object Manager Query for OCR Sets
```bash
POST /Relativity.ObjectManager/{version}/workspace/{workspaceID}/object/query

{
  "request": {
    "objectType": {"Name": "OCR Set"},
    "fields": [
      {"Name": "Name"},
      {"Name": "Status"},
      {"Name": "Total Documents"},
      {"Name": "Documents with Errors"}
    ],
    "condition": "'Status' IN ['Error', 'Completed with Errors']"
  }
}
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
