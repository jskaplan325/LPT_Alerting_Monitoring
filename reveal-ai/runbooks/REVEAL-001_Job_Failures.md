# REVEAL-001: Job Failures

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Job Failure (Status=4) |
| **Severity** | **CRITICAL** |
| **Platform** | Reveal AI |
| **Detection** | NIA API Job Status Polling |
| **Response SLA** | Immediate (15 minutes) |
| **Escalation** | On-call → Team Lead → Reveal Support |

---

## Alert Conditions

```
IF job_status == 4 (Error) THEN CRITICAL
IF job_status == 5 (Cancelled) THEN MEDIUM
IF multiple_jobs_failed_in_1_hour >= 3 THEN CRITICAL (systemic issue)
```

### Affected Job Types

| Job Type | Impact if Failed |
|----------|------------------|
| AI Document Sync | Clustering/threading incomplete |
| Index Operations | Search unavailable for new documents |
| Export Jobs | Client deliverables delayed |
| Production Jobs | Legal production delayed |
| Bulk Updates | Data inconsistency |
| AV Transcription | Media review impacted |
| Deletion Jobs | Compliance requirements unmet |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge in monitoring system
- [ ] Note the job_id and job_type
- [ ] Open incident ticket

### Step 2: Gather Basic Information

**Record:**
- Job ID: ________________
- Job Type: ________________
- Project/Case: ________________
- Start Time: ________________
- Error Time: ________________
- Error Details: ________________

### Step 3: Check for Systemic Issues
- Are multiple jobs failing?
- Is the NIA API healthy?
- Any recent platform changes?

---

## Investigation Procedures

### Step 4: Query Job Details

**Via NIA API:**
```bash
curl -X GET "http://[server]:5566/nia/jobs/{job_id}" \
  -H "Content-Type: application/json"
```

**Expected Response Fields:**
```json
{
  "jobId": "12345",
  "jobType": "AIDocumentSync",
  "status": 4,
  "statusName": "Error",
  "startTime": "2024-01-15T10:00:00Z",
  "endTime": "2024-01-15T10:30:00Z",
  "errorDetails": "Description of error...",
  "projectId": "project-123",
  "submittedBy": "user@company.com"
}
```

### Step 5: Check Job Error Details

Common error categories:

| Error Type | Typical Cause | Resolution Path |
|------------|---------------|-----------------|
| Document Processing Error | Corrupt file, unsupported format | Identify and exclude problem documents |
| Resource Exhaustion | Memory/disk full | Clear space, restart services |
| Timeout | Job too large, slow performance | Break into smaller batches |
| Permission Error | Insufficient access rights | Verify service account permissions |
| Connection Error | Network/database connectivity | Check infrastructure |
| Configuration Error | Invalid job parameters | Review job settings |

### Step 6: Review Related Jobs

Check if other jobs are affected:
```bash
# Get recent jobs with errors
curl -X GET "http://[server]:5566/nia/jobs?status=4&since=2024-01-15T00:00:00Z"
```

---

## Resolution Procedures

### Scenario A: Single Document Error

**Symptoms:** Job failed due to specific document(s)

**Resolution:**
1. Identify problem document(s) from error details
2. Review document for corruption/format issues
3. Options:
   - Fix the source document and retry
   - Exclude document from job and retry
   - Process document separately with different settings

### Scenario B: Resource Exhaustion

**Symptoms:** Out of memory, disk full errors

**Resolution:**
1. Check server resources (disk, memory, CPU)
2. Clear temporary files if disk full
3. Restart affected services if memory issue
4. Retry job with smaller batch size

### Scenario C: Timeout/Performance

**Symptoms:** Job timed out before completion

**Resolution:**
1. Review job size (document count, total size)
2. Break into smaller batches
3. Schedule during off-peak hours
4. Check for concurrent resource-intensive jobs

### Scenario D: Systemic Failure

**Symptoms:** Multiple jobs failing with same error

**Resolution:**
1. Check NIA service health
2. Review recent configuration changes
3. Check database connectivity
4. **Escalate to Reveal Support if infrastructure issue**

### Retry Failed Job

```bash
# Resubmit job via API (if supported)
curl -X POST "http://[server]:5566/nia/jobs/{job_id}/retry" \
  -H "Content-Type: application/json"
```

Or via Reveal UI:
1. Navigate to Ops Center → Jobs
2. Find failed job
3. Review error details
4. Click "Retry" or create new job

---

## Escalation Procedures

### When to Escalate

| Condition | Escalation Target |
|-----------|-------------------|
| Cannot determine cause | Team Lead |
| Infrastructure issue suspected | IT/Infrastructure |
| Multiple jobs failing systemically | Reveal Support |
| Client SLA at risk | Project Manager + Team Lead |
| No resolution after 1 hour | Team Lead |

### Reveal Support Escalation

**Contact:** support@revealdata.com

**Provide:**
- Job ID(s) affected
- Complete error messages
- Timeline of events
- Steps already attempted
- Impact assessment

---

## Post-Incident Actions

### Immediate (within 1 hour of resolution)
- [ ] Verify job completed successfully on retry
- [ ] Confirm data integrity
- [ ] Update incident ticket
- [ ] Notify affected users/stakeholders

### Short-term (within 24 hours)
- [ ] Complete incident report
- [ ] Root cause analysis
- [ ] Document workaround if applicable
- [ ] Update monitoring thresholds if needed

### Long-term
- [ ] Implement preventive measures
- [ ] Update runbook with lessons learned
- [ ] Review with team in retrospective

---

## Prevention Measures

### Proactive Monitoring
- Monitor job queue depth
- Track job duration trends
- Alert on jobs approaching timeout
- Monitor server resources

### Best Practices
- Test with small batches before large jobs
- Schedule resource-intensive jobs during off-peak
- Maintain adequate disk space (>20% free)
- Regular database maintenance
- Keep platform updated

---

## API Reference

### Get Job Status
```bash
GET http://[server]:5566/nia/jobs/{job_id}
```

### List Recent Jobs
```bash
GET http://[server]:5566/nia/jobs?limit=100&status=4
```

### Get Job Queue
```bash
GET http://[server]:5566/nia/jobs/queue
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
