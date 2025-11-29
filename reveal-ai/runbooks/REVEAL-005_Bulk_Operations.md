# REVEAL-005: Bulk Operations

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Bulk Operation Alert |
| **Severity** | **HIGH** (bulk updates) / **CRITICAL** (mass deletions) |
| **Platform** | Reveal AI |
| **Detection** | NIA API Bulk Job Monitoring |
| **Response SLA** | 15 minutes (deletion) / 1 hour (updates) |
| **Escalation** | On-call → Team Lead → Legal (if compliance) |

---

## Alert Conditions

```
IF bulk_operation_type == "delete" THEN CRITICAL
IF bulk_operation_type == "delete" AND document_count > 100 THEN CRITICAL (immediate)
IF bulk_operation_type == "update" AND document_count > 1000 THEN HIGH
IF bulk_operation_type == "tag_modification" AND affects_privilege_tags THEN CRITICAL
IF bulk_operation_initiated_after_hours THEN HIGH
IF bulk_operation_affects_legal_hold_documents THEN CRITICAL
```

### Bulk Operation Types

| Operation | Risk Level | Alert Threshold |
|-----------|------------|-----------------|
| Mass Deletion | CRITICAL | Any deletion |
| Tag Bulk Update | HIGH | > 1,000 documents |
| Field Bulk Update | MEDIUM | > 1,000 documents |
| Coding Decision Update | HIGH | > 500 documents |
| Privilege Tag Change | CRITICAL | Any change |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge immediately
- [ ] For deletions: treat as CRITICAL
- [ ] Note job ID and user

### Step 2: Gather Information

**Record:**
- Job ID: ________________
- Operation Type: ________________
- User Who Initiated: ________________
- Document Count Affected: ________________
- Project/Case: ________________
- Time of Operation: ________________
- Operation Status: ________________

### Step 3: Immediate Assessment

For **DELETIONS:**
- Is this reversible?
- Are backups available?
- Does this affect legal hold documents?
- Was this authorized?

For **UPDATES:**
- What fields/tags are affected?
- Are privilege designations changing?
- Is this a known/expected operation?

---

## Investigation Procedures

### Step 4: Query Operation Details

**Via NIA API:**
```bash
curl -X GET "http://[server]:5566/nia/jobs/{job_id}" \
  -H "Content-Type: application/json"
```

**Capture:**
- Operation parameters
- Document selection criteria
- User authorization
- Before/after state

### Step 5: Verify Authorization

**Check:**
- [ ] User has permission for this operation
- [ ] Project manager approval obtained
- [ ] Operation documented in change request
- [ ] No legal hold restrictions

### Step 6: Assess Impact

| Impact Type | Check |
|-------------|-------|
| Document Loss | Are deleted docs recoverable? |
| Coding Impact | Will this affect production/export? |
| Privilege Impact | Are privilege tags changing? |
| Legal Hold | Are held documents affected? |
| Audit Trail | Is the change logged? |

### Step 7: Check Document Hold Status

**Critical:** Ensure no legal hold documents are affected
```bash
# Check if documents are on hold
curl -X GET "https://[instance].revealdata.com/rest/api/v2/projects/{projectId}/documents?filter=legalHold:true" \
  -H "incontrolauthtoken: {token}"
```

---

## Resolution Procedures

### Scenario A: Authorized Bulk Update

**Confirmation obtained:** Operation is legitimate

**Actions:**
1. Document authorization
2. Monitor completion
3. Verify results after completion
4. Close alert as verified

### Scenario B: Mass Deletion - Verify

**Any deletion requires verification**

**Immediate Actions:**
1. **If operation is still running and unverified:**
   - Attempt to pause/cancel if possible
   ```bash
   curl -X POST "http://[server]:5566/nia/jobs/{job_id}/cancel"
   ```
2. Contact user immediately
3. Contact project manager
4. Verify backup status
5. Document all communications

### Scenario C: Unauthorized Operation - Block

**Operation not authorized**

**Immediate Actions:**
1. **Cancel/block operation immediately**
2. Disable user account if needed
3. Assess damage if operation completed
4. Check backup availability
5. Escalate to Security/Legal
6. Preserve evidence

### Scenario D: Legal Hold Impact

**Documents on legal hold affected**

**Immediate Actions:**
1. **STOP the operation if possible**
2. Escalate to Legal Team immediately
3. Document impact scope
4. Assess spoliation risk
5. Engage outside counsel if needed
6. Preserve all evidence

### Scenario E: Privilege Tag Changes

**Privilege designations being modified in bulk**

**Actions:**
1. Verify with legal team
2. Confirm privilege review completed
3. Document authorization chain
4. If unauthorized, restore previous state
5. Escalate to Legal

---

## Data Recovery Procedures

### If Unauthorized Deletion Occurred

1. **Stop ongoing operations**
2. **Assess recovery options:**
   - Database backup restoration
   - Document-level recovery
   - Point-in-time recovery

3. **Contact Reveal Support** for recovery assistance:
   - support@revealdata.com
   - Provide: Job ID, time of deletion, document IDs if known

4. **Document chain of custody for any recovery**

### Recovery Verification
- Verify document count matches pre-deletion
- Spot check recovered documents
- Verify metadata intact
- Update audit logs

---

## Escalation Procedures

### Immediate Escalation Required

| Condition | Escalate To |
|-----------|-------------|
| Any mass deletion | Team Lead + Project Manager |
| Legal hold documents affected | Legal Team (IMMEDIATE) |
| Unauthorized operation | Security Team |
| Cannot cancel/block | Reveal Support |
| Privilege tags modified | Legal Team |

### Escalation Contacts

| Role | When |
|------|------|
| Project Manager | Any bulk operation verification |
| Legal Team | Legal hold/privilege impact |
| Security Team | Unauthorized operations |
| Reveal Support | Recovery assistance |

---

## Post-Incident Actions

### For Authorized Operations
- [ ] Verify operation completed successfully
- [ ] Confirm document counts
- [ ] Update project documentation
- [ ] Close alert

### For Blocked/Recovered Operations
- [ ] Complete incident report
- [ ] Root cause analysis
- [ ] Implement additional controls
- [ ] Review user permissions
- [ ] Update procedures if needed

### For Compliance Events
- [ ] Document all actions with timestamps
- [ ] Preserve evidence
- [ ] Complete compliance report
- [ ] Notify appropriate parties

---

## Prevention Measures

### Access Controls
- Require elevated permissions for deletions
- Implement approval workflow for bulk operations
- Separate delete permissions from edit permissions
- Regular permission audits

### Technical Controls
- Soft delete before hard delete
- Mandatory backup before bulk operations
- Legal hold check before deletions
- Batch size limits

### Process Controls
- Change request required for bulk operations
- Dual approval for deletions
- After-hours restriction on deletions
- Regular training on data handling

### Monitoring Recommendations

| Operation | Frequency | Alert |
|-----------|-----------|-------|
| Deletions | Real-time | Any deletion |
| Bulk Updates | Every 10 min | > 1,000 docs |
| Tag Changes | Every 10 min | Privilege tags |
| After-Hours | Real-time | Any bulk op |

---

## API Reference

### Get Bulk Jobs
```bash
GET http://[server]:5566/nia/jobs?jobType=BulkUpdate
```

### Cancel Job
```bash
POST http://[server]:5566/nia/jobs/{job_id}/cancel
```

### Get Job Details
```bash
GET http://[server]:5566/nia/jobs/{job_id}
```

### Check Document Legal Hold
```bash
GET https://[instance].revealdata.com/rest/api/v2/documents/{docId}/holds
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
