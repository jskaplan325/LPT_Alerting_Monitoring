# RUNBOOK-012: RelativityOne Branding Job Failures

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Branding Job Failure |
| **Severity** | HIGH (Job Failed) / MEDIUM (Errors) / WARNING (Performance) |
| **Platform** | RelativityOne |
| **Detection** | Queue Management (Branding Queue) |
| **Response SLA** | High: 1 hour / Medium: 4 hours / Warning: Next business day |
| **Escalation** | On-call → Team Lead → Relativity Support |

## Alert Conditions

```
IF Branding_Job_Status == "Error" THEN HIGH
IF Branding_Job_Status == "Completed with Errors" AND Error_Rate > 5% THEN HIGH
IF Branding_Job_Stuck > 2 hours THEN WARNING
IF Branding_Queue_Depth > threshold THEN WARNING
```

---

## Branding Agent Configuration

| Agent | Count | Purpose |
|-------|-------|---------|
| Branding Manager | Up to 4 per resource pool | Processes branding jobs |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge in monitoring system
- [ ] Note workspace ID and branding job details
- [ ] Check if this is blocking production
- [ ] Open tracking ticket

### Step 2: Quick Status Check

**Via Queue Management:**
1. Navigate to **Queue Management** tab
2. Select **Branding** queue
3. Review job status and progress
4. Note queue depth and job priority

**Via Instance Details:**
1. Check **Queues** section for Branding status

**Record the following:**
- Workspace: ________________
- Job Status: ________________
- Documents in Job: ________________
- Documents Completed: ________________
- Documents with Errors: ________________
- Priority: ________________
- Time in Queue: ________________

---

## Investigation Procedures

### Step 3: Review Branding Job Details

**Via Queue Management:**
1. Select the failed/stuck job
2. Review available details:
   - Job progress
   - Error information
   - Associated workspace

### Step 4: Check Branding Manager Agents

1. Navigate to **Agents** tab
2. Filter for "Branding Manager"
3. Verify agents are:
   - Enabled
   - Running or Idle
   - Recent last activity
4. Check that appropriate number per resource pool (up to 4)

### Step 5: Identify Error Patterns

**Common Branding Errors:**

| Error Type | Cause | Resolution |
|------------|-------|------------|
| Template error | Invalid branding template | Review production branding settings |
| Font error | Missing fonts | Check font availability |
| Image not found | Source image unavailable | Verify images are accessible |
| Field resolution | Placeholder field empty | Check document fields |
| Timeout | Complex documents | May need individual handling |
| Memory error | Large documents | Process in smaller batches |

---

## Resolution Procedures

### Scenario A: Branding Job Failed

**Symptoms:** Job shows error status in queue

**Steps:**
1. Identify error from Queue Management
2. Common causes:

| Error | Cause | Resolution |
|-------|-------|------------|
| Agent failure | Branding Manager down | Check agent status |
| Template invalid | Production branding config | Review production settings |
| Resource issue | Memory/disk | Escalate if infrastructure |

3. **Resolution:**
   - If agent issue: Verify agent status, re-enable if disabled
   - If template issue: Fix production branding configuration
   - After fixing: Retry from production or Queue Management

### Scenario B: Branding Errors on Documents

**Symptoms:** Some documents failed branding

**Steps:**
1. Export error list from Queue Management (if available)
2. Identify failing documents
3. Review document characteristics:
   - File type
   - Page count
   - Image quality

4. **Resolution by cause:**

| Cause | Resolution |
|-------|------------|
| No image | Run imaging first |
| Corrupt image | Re-image document |
| Large document | Process individually |
| Field empty | Populate branding field |

### Scenario C: Stuck Branding Job

**Symptoms:** Job in queue without progress for extended time

**Steps:**
1. Check Branding Manager agent status
2. Review queue for blocking jobs
3. Check job priority
4. Options:
   - Change priority (1=highest)
   - Wait for blocking jobs
   - Cancel and retry if needed

### Scenario D: Branding Quality Issues

**Symptoms:** Branding completed but appearance is incorrect

**Investigation:**
1. Review production branding settings:
   - Header/footer content
   - Font settings
   - Placement settings
   - Field placeholders

2. Check template rendering:
   - Are placeholders resolving correctly?
   - Is text readable?
   - Is positioning correct?

**Resolution:**
- Adjust production branding settings
- Re-run branding on affected documents
- Test with sample documents first

---

## Queue Management Operations

### Available Operations

| Operation | Use Case |
|-----------|----------|
| Change Priority | Expedite urgent jobs |
| Export List | Get list of documents in job |

### Priority Levels
- **1:** Highest priority (deadline-critical)
- **5:** Normal priority (default)
- **10:** Lowest priority

### Export List Feature
Use "Export list" to get document identifiers for troubleshooting specific document failures.

---

## Branding Dependencies

### Required for Branding
- Images must exist for documents
- Production must be properly configured
- Branding templates must be valid
- Required fields must be populated

### Branding Workflow
```
Production Created → Branding Configured → Documents Queued → Branding Applied → Production Completed
```

### Common Dependencies

| Dependency | Impact if Missing |
|------------|-------------------|
| Document images | Branding cannot be applied |
| Valid template | Jobs fail |
| Populated fields | Placeholders show blank |
| Available fonts | Text may not render |

---

## Escalation Procedures

### When to Escalate

| Condition | Level | Timeframe |
|-----------|-------|-----------|
| All branding agents down | Relativity Support | Immediate |
| Persistent template failures | Team Lead | 2 hours |
| Blocking production deadline | Team Lead | Immediate |
| Error rate >20% | Team Lead | 2 hours |
| Infrastructure issues | Relativity Support | 1 hour |

### Information for Escalation

- [ ] Queue status and job details
- [ ] Error messages
- [ ] Production configuration
- [ ] Agent status
- [ ] Document count affected
- [ ] Impact on deadlines

---

## Post-Incident Actions

### Immediate
- [ ] Verify branding completed successfully
- [ ] Spot-check branded documents
- [ ] Proceed with production if blocked

### Short-term (24 hours)
- [ ] Complete incident report
- [ ] Review production templates
- [ ] Update problematic configurations

### Long-term
- [ ] Optimize branding templates
- [ ] Document best practices
- [ ] Review agent allocation

---

## Prevention Measures

### Pre-Production Checklist
- [ ] Verify all documents are imaged
- [ ] Test branding on sample documents
- [ ] Validate template placeholders
- [ ] Confirm font availability
- [ ] Schedule during appropriate hours

### Template Best Practices
- Keep templates simple
- Test placeholders before large jobs
- Use standard fonts
- Document template configuration
- Version control templates

### Monitoring
- Alert on branding queue depth
- Monitor job duration
- Track error rates
- Watch agent health

---

## API Reference

### Queue Monitoring
Branding queue is available through Queue Management. API access is limited - primary monitoring through:
- Queue Management UI
- Instance Details queues section

### Production API Integration
Branding is part of production workflow:
```bash
# Production status includes branding status
GET /relativity-productions/{version}/workspaces/{workspaceId}/productions/{productionId}
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
