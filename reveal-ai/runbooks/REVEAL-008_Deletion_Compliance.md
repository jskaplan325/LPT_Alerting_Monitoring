# REVEAL-008: Deletion & Compliance

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Deletion Compliance Alert |
| **Severity** | **CRITICAL** |
| **Platform** | Reveal AI |
| **Detection** | NIA API Job Status (Status=7) |
| **Response SLA** | Immediate (15 minutes) |
| **Escalation** | On-call → Legal → Compliance |

---

## Alert Conditions

```
IF job_status == 7 (Deleted) THEN CRITICAL
IF deletion_job_submitted THEN CRITICAL
IF document_count_decreased_unexpectedly THEN CRITICAL
IF deletion_affects_legal_hold THEN CRITICAL (IMMEDIATE ESCALATION)
IF deletion_without_approval_record THEN CRITICAL
IF deletion_by_unauthorized_user THEN CRITICAL
```

### Deletion Risk Matrix

| Deletion Type | Risk Level | Required Approval |
|---------------|------------|-------------------|
| Single Document | HIGH | Documented reason |
| Batch Deletion (< 100) | CRITICAL | Manager + Legal |
| Mass Deletion (100+) | CRITICAL | Legal + Compliance |
| Legal Hold Documents | CRITICAL | **PROHIBITED** |
| Production Set Documents | CRITICAL | Legal approval |
| Privileged Documents | CRITICAL | Legal approval |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert - IMMEDIATE
- [ ] Acknowledge immediately - this is CRITICAL
- [ ] Deletion events are ALWAYS significant
- [ ] Open compliance incident ticket

### Step 2: Gather Information

**Record:**
- Job ID: ________________
- Deletion Type: ________________
- User Who Initiated: ________________
- Document Count: ________________
- Project/Case: ________________
- Time of Deletion: ________________
- Legal Hold Status: ________________
- Approval Reference: ________________

### Step 3: Legal Hold Check - CRITICAL

**IMMEDIATELY verify:**
- [ ] Are deleted documents on legal hold?
- [ ] Are deleted documents potentially responsive?
- [ ] Is there active litigation involving this data?

**If ANY legal hold concerns:**
→ STOP and escalate to Legal immediately

---

## Investigation Procedures

### Step 4: Query Deletion Details

**Via NIA API:**
```bash
curl -X GET "http://[server]:5566/nia/jobs/{job_id}" \
  -H "Content-Type: application/json"
```

**Capture:**
- Complete deletion parameters
- Document IDs affected
- User authorization
- Timestamp details

### Step 5: Verify Authorization

**Required Documentation:**
- [ ] Formal deletion request
- [ ] Manager approval
- [ ] Legal approval (if required)
- [ ] Compliance sign-off (if required)
- [ ] No legal hold applies

**Find approval in:**
- Change management system
- Email approval chain
- Project documentation
- Legal sign-off records

### Step 6: Check Legal Hold Status

**CRITICAL CHECK:**
```bash
# Check affected documents for holds
curl -X GET "https://[instance].revealdata.com/rest/api/v2/projects/{projectId}/documents/{docId}/holds" \
  -H "incontrolauthtoken: {token}"
```

**Legal hold sources:**
- Litigation holds
- Regulatory holds
- Investigation holds
- Preservation notices

### Step 7: Assess Compliance Impact

| Factor | Question | Impact if Yes |
|--------|----------|---------------|
| Active Litigation | Is data subject to litigation? | Potential spoliation |
| Regulatory Requirement | Subject to retention rules? | Compliance violation |
| Preservation Notice | Under preservation? | Spoliation risk |
| Audit Trail | Was deletion logged? | Compliance issue |
| Authorization | Proper approval obtained? | Process violation |

---

## Resolution Procedures

### Scenario A: Authorized Deletion (Compliant)

**All approvals documented, no legal holds**

**Actions:**
1. Verify approval chain is complete
2. Confirm no legal hold applies
3. Document in compliance log
4. Close alert as "Compliant Deletion"

### Scenario B: Unauthorized Deletion

**Deletion without proper approval**

**Immediate Actions:**
1. **STOP any ongoing deletion if possible**
2. Assess if recovery is possible
3. Document violation
4. Escalate to Legal and Compliance
5. Disable user permissions
6. Begin recovery procedures

### Scenario C: Legal Hold Violation - CRITICAL

**Documents on legal hold were deleted**

**IMMEDIATE ACTIONS:**
1. **ESCALATE TO LEGAL IMMEDIATELY**
2. **Notify outside counsel**
3. Preserve all evidence of deletion
4. Begin recovery procedures immediately
5. Do NOT destroy any logs or records
6. Document timeline precisely
7. Prepare spoliation assessment

**This is a potential litigation issue requiring immediate legal guidance.**

### Scenario D: Recovery Required

**Need to restore deleted documents**

**Recovery Steps:**
1. Identify backup containing deleted data
2. Engage Reveal Support for recovery:
   - support@revealdata.com
   - Priority: URGENT
3. Provide:
   - Job ID
   - Approximate deletion time
   - Document count/IDs if known
4. Restore to staging area first
5. Verify completeness
6. Document recovery chain of custody

---

## Escalation Procedures

### Immediate Escalation Required

| Condition | Escalate To | Timeline |
|-----------|-------------|----------|
| Any deletion event | Compliance review | Same day |
| Unauthorized deletion | Legal + Compliance | Immediate |
| Legal hold documents | Legal (outside counsel) | Immediate |
| Cannot verify authorization | Legal | 1 hour |
| Recovery needed | Legal + IT + Vendor | Immediate |

### Legal Escalation Protocol

**For potential spoliation:**

1. **Notify General Counsel immediately**
2. **Contact outside counsel**
3. Preserve ALL related evidence
4. Document everything with timestamps
5. Do not communicate about deletion outside legal guidance
6. Prepare for potential disclosure obligations

---

## Post-Incident Actions

### For Compliant Deletions
- [ ] Document in compliance log
- [ ] Archive approval records
- [ ] Update data inventory
- [ ] Close alert

### For Non-Compliant Deletions
- [ ] Complete incident report
- [ ] Root cause analysis
- [ ] Process improvement
- [ ] Training if needed
- [ ] Policy updates

### For Legal Hold Violations
- [ ] Full legal incident response
- [ ] Spoliation assessment
- [ ] Court notification (if required)
- [ ] Remediation plan
- [ ] Policy enforcement review

---

## Prevention Measures

### Technical Controls
- Legal hold enforcement (prevent deletion of held docs)
- Deletion approval workflow
- Soft delete before hard delete
- Mandatory backup before deletion
- Deletion audit logging

### Process Controls
- Formal deletion request process
- Multi-level approval requirements
- Legal review for sensitive deletions
- Regular legal hold reconciliation

### Compliance Controls
- Annual deletion policy review
- Regular legal hold audits
- Training on deletion procedures
- Compliance monitoring

### Monitoring Requirements

| Check | Frequency | Alert |
|-------|-----------|-------|
| Deletion jobs | Real-time | Any deletion |
| Document count | Every 15 min | Unexpected decrease |
| Legal hold integrity | Daily | Held docs modified |
| Deletion audit log | Daily | Missing entries |

---

## Data Retention Reference

### Retention Policy Integration

Before any deletion, verify against:
- Corporate retention policy
- Regulatory retention requirements
- Active legal holds
- Pending litigation
- Audit requirements

### Retention Categories

| Data Type | Typical Retention | Authority |
|-----------|-------------------|-----------|
| Litigation documents | Until case closed + X years | Legal |
| Regulatory records | Per regulation | Compliance |
| Project documents | Project + 3-7 years | Records Mgmt |
| Temporary/working | Per policy | Business unit |

---

## API Reference

### Get Deletion Job Details
```bash
GET http://[server]:5566/nia/jobs/{job_id}
```

### Check Document Legal Hold
```bash
GET https://[instance].revealdata.com/rest/api/v2/documents/{docId}/holds
```

### Get Project Document Count
```bash
GET https://[instance].revealdata.com/rest/api/v2/projects/{projectId}/stats
```

### Audit Log Query
```bash
GET https://[instance].revealdata.com/rest/api/v2/audit?action=delete&startDate={date}
```

---

## Chain of Custody Documentation

For any deletion event, maintain:

| Item | Requirement |
|------|-------------|
| Authorization | Written approval with signatures/approvals |
| Scope | Document count, criteria, project |
| Verification | Legal hold check confirmation |
| Execution | Who, when, method |
| Confirmation | Job completion, verification |
| Exceptions | Any issues or deviations |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
