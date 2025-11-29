# REVEAL-002: Stuck/Long-Running Jobs

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Stuck/Long-Running Job |
| **Severity** | **HIGH** (>4 hours) / **CRITICAL** (>24 hours) |
| **Platform** | Reveal AI |
| **Detection** | NIA API Job Duration Monitoring |
| **Response SLA** | 1 hour (HIGH) / 15 minutes (CRITICAL) |
| **Escalation** | On-call → Team Lead → Reveal Support |

---

## Alert Conditions

```
IF job_status == 2 (InProcess) AND duration > 4 hours THEN HIGH
IF job_status == 2 (InProcess) AND duration > 8 hours THEN HIGH (urgent)
IF job_status == 2 (InProcess) AND duration > 24 hours THEN CRITICAL
IF job_status IN (9, 10, 11, 12) AND duration > threshold THEN HIGH
```

### Duration Thresholds by Job Type

| Job Type | Warning | High | Critical |
|----------|---------|------|----------|
| AI Document Sync | 2 hours | 4 hours | 24 hours |
| Index Operations | 1 hour | 2 hours | 8 hours |
| Export Jobs | 30 min | 2 hours | 8 hours |
| Production Jobs | 1 hour | 4 hours | 24 hours |
| Bulk Updates | 30 min | 2 hours | 8 hours |
| AV Transcription | 4 hours | 8 hours | 48 hours |
| Deletion Jobs | 30 min | 2 hours | 8 hours |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge in monitoring system
- [ ] Note the job_id, job_type, and duration
- [ ] Assess business impact

### Step 2: Gather Information

**Record:**
- Job ID: ________________
- Job Type: ________________
- Start Time: ________________
- Current Duration: ________________
- Document Count: ________________
- Expected Duration: ________________
- Project/Case: ________________

### Step 3: Quick Assessment
- Is this job typically long-running?
- What's the document count/size?
- Are there concurrent jobs competing for resources?

---

## Investigation Procedures

### Step 4: Check Job Progress

**Via NIA API:**
```bash
curl -X GET "http://[server]:5566/nia/jobs/{job_id}" \
  -H "Content-Type: application/json"
```

**Check for progress indicators:**
- Documents processed vs total
- Percentage complete
- Last activity timestamp

### Step 5: Check Server Resources

| Resource | Check | Concern Level |
|----------|-------|---------------|
| CPU | > 90% sustained | High |
| Memory | > 85% used | High |
| Disk | < 10% free | Critical |
| Network | High latency | Medium |

### Step 6: Check for Blocking Conditions

Common causes of stuck jobs:

| Cause | Indicators | Resolution |
|-------|------------|------------|
| Resource Contention | Multiple large jobs running | Pause/reschedule other jobs |
| Database Lock | Waiting on DB operations | Check DB admin |
| Corrupt Document | Processing stopped at specific doc | Identify and skip document |
| Network Issue | Timeout errors in logs | Check connectivity |
| Service Crash | Process not running | Restart service |
| Disk Full | Write errors | Clear space |

### Step 7: Review Concurrent Jobs

```bash
# Check all running jobs
curl -X GET "http://[server]:5566/nia/jobs?status=2"
```

Are multiple resource-intensive jobs competing?

---

## Resolution Procedures

### Scenario A: Job Making Progress (Just Slow)

**Symptoms:** Job is progressing, just slower than expected

**Resolution:**
1. Monitor progress rate
2. Estimate completion time
3. If acceptable, let it continue
4. If SLA at risk, consider:
   - Pausing competing jobs
   - Adding resources (if possible)
   - Communicating new ETA to stakeholders

### Scenario B: Job Stalled (No Progress)

**Symptoms:** Progress counter not moving, last activity stale

**Resolution:**
1. Check server resources
2. Review service logs for errors
3. Attempt to identify blocking document/condition
4. If identifiable:
   - Cancel job
   - Exclude problematic items
   - Resubmit
5. If not identifiable:
   - Cancel job
   - Restart relevant services
   - Resubmit with smaller batch

### Scenario C: Resource Contention

**Symptoms:** Multiple jobs running, all slow

**Resolution:**
1. Identify least critical jobs
2. Pause or cancel lower-priority jobs
3. Let critical job complete
4. Reschedule paused jobs for off-peak

### Scenario D: System Issue

**Symptoms:** All jobs stuck, services unhealthy

**Resolution:**
1. Check service status
2. Restart affected services
3. If persists, **escalate to Reveal Support**

### Cancel a Stuck Job

**Via API (if supported):**
```bash
curl -X POST "http://[server]:5566/nia/jobs/{job_id}/cancel" \
  -H "Content-Type: application/json"
```

**Via Reveal UI:**
1. Navigate to Ops Center → Jobs
2. Find the stuck job
3. Click "Cancel"
4. Confirm cancellation

---

## Escalation Procedures

### When to Escalate

| Condition | Escalation Target |
|-----------|-------------------|
| Job stuck >24 hours | Team Lead |
| Cannot cancel job | Reveal Support |
| System-wide job issues | Reveal Support |
| Client SLA at risk | Project Manager |
| Database issues suspected | DBA/Infrastructure |

### Reveal Support Escalation

**Contact:** support@revealdata.com

**Provide:**
- Job ID and type
- Duration and progress
- System resource status
- Recent changes
- Steps attempted

---

## Post-Incident Actions

### Immediate
- [ ] Verify job completed or properly cancelled
- [ ] Resubmit if needed
- [ ] Confirm data integrity
- [ ] Update stakeholders

### Short-term
- [ ] Analyze root cause
- [ ] Review job sizing guidelines
- [ ] Update duration thresholds if needed

### Long-term
- [ ] Implement job size limits
- [ ] Add progress monitoring
- [ ] Schedule large jobs during off-peak
- [ ] Document expected durations by job type

---

## Prevention Measures

### Job Sizing Guidelines

| Document Count | Recommended Approach |
|----------------|---------------------|
| < 10,000 | Single job OK |
| 10,000 - 50,000 | Consider batching |
| 50,000 - 100,000 | Batch recommended |
| > 100,000 | Required batching |

### Scheduling Best Practices
- Schedule large jobs during off-peak hours
- Avoid overlapping resource-intensive jobs
- Monitor queue depth
- Set appropriate timeout values

### Monitoring Recommendations
- Track job duration trends
- Alert before critical thresholds
- Monitor progress percentage
- Track resource utilization during jobs

---

## API Reference

### Get Job Details
```bash
GET http://[server]:5566/nia/jobs/{job_id}
```

### List Running Jobs
```bash
GET http://[server]:5566/nia/jobs?status=2
```

### Cancel Job
```bash
POST http://[server]:5566/nia/jobs/{job_id}/cancel
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
