# RUNBOOK-010: RelativityOne Mass Operations Monitoring

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Mass Operation Alerts |
| **Severity** | CRITICAL (Deletions) / HIGH (Large Edits) / MEDIUM (Standard) |
| **Platform** | RelativityOne |
| **Detection** | Audit API + Object Manager API |
| **Response SLA** | Critical: Immediate / High: 30 min / Medium: 2 hours |
| **Escalation** | On-call → Team Lead → Legal (if legal hold affected) |

## Alert Conditions

### Mass Delete Alerts
```
IF MassDelete AND Document_Count > 100 THEN CRITICAL
IF MassDelete AND Legal_Hold_Documents > 0 THEN CRITICAL (IMMEDIATE)
IF MassDelete AND Unauthorized_User THEN CRITICAL
IF Delete_Rate > 50 docs/minute sustained THEN HIGH
```

### Mass Edit Alerts
```
IF MassEdit AND Document_Count > 1,000 THEN HIGH
IF MassEdit AND Field == "Privileged" THEN HIGH
IF MassEdit AND Field == "Responsive" THEN MEDIUM
IF Bulk_Tag_Change > 5,000 documents THEN MEDIUM
```

### Mass Move/Copy Alerts
```
IF MassCopy AND Document_Count > 10,000 THEN MEDIUM
IF MassMove AND Cross_Workspace THEN HIGH
IF MassMove AND Document_Count > 5,000 THEN MEDIUM
```

---

## Mass Operation Types

| Operation | Risk Level | Key Concerns |
|-----------|------------|--------------|
| **Mass Delete** | CRITICAL | Data loss, legal hold compliance |
| **Mass Edit** | HIGH | Coding integrity, audit trail |
| **Mass Tag** | MEDIUM | Review workflow impact |
| **Mass Move** | HIGH | Data organization, access control |
| **Mass Copy** | MEDIUM | Duplication, storage impact |
| **Mass Replace** | HIGH | Field value integrity |
| **Mass Print** | MEDIUM | Data exfiltration risk |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge in monitoring system
- [ ] Identify operation type and scope
- [ ] Determine if operation is in progress or completed
- [ ] Open tracking ticket

### Step 2: Critical Assessment

**For Mass Deletions - IMMEDIATE:**
1. Is the operation still in progress?
2. Can it be cancelled?
3. Are legal hold documents potentially affected?
4. Is this an authorized cleanup activity?

**Record the following:**
- Operation Type: ________________
- User: ________________
- Workspace: ________________
- Document Count: ________________
- Start Time: ________________
- Status (In Progress/Complete): ________________
- Authorization Reference: ________________

---

## Investigation Procedures

### Step 3: Query Mass Operation Audit

**Recent Mass Operations:**
```bash
curl -X POST "<host>/Relativity.REST/api/relativity.audit/v1/workspaces/<WORKSPACE_ID>/audits/query" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -" \
  -H "Content-Type: application/json" \
  -d '{
    "request": {
      "objectType": {"artifactTypeID": 1000042},
      "fields": [
        {"Name": "Timestamp"},
        {"Name": "User Name"},
        {"Name": "Action"},
        {"Name": "Details"},
        {"Name": "Object Type"}
      ],
      "condition": "'\''Action'\'' IN ['\''MassDelete'\'', '\''MassEdit'\'', '\''Mass Operation'\'']",
      "sorts": [{"FieldIdentifier": {"Name": "Timestamp"}, "Direction": "Descending"}],
      "length": 50
    }
  }'
```

### Step 4: Identify Affected Documents

**If Mass Delete - Get Document Details:**
```bash
# Query for recently deleted documents (if audit details available)
# Or query saved search that was used for mass operation
```

### Step 5: Check for Legal Hold Impact

**Query Legal Hold Status:**
```json
{
  "request": {
    "objectType": {"Name": "Document"},
    "fields": [
      {"Name": "Legal Hold"},
      {"Name": "Control Number"}
    ],
    "condition": "'Legal Hold' == true"
  }
}
```

**CRITICAL:** If legal hold documents were affected, escalate immediately to Legal.

### Step 6: Verify Authorization

Check for:
- Documented approval for mass operation
- User's role and permissions
- Project requirements justifying the operation
- Change management ticket (if applicable)

---

## Resolution Procedures

### Scenario A: Unauthorized Mass Delete (CRITICAL)

**Symptoms:** Mass deletion by unauthorized user or without approval

**Immediate Actions (First 5 Minutes):**
1. **If in progress:** Cancel operation immediately
2. **If completed:** Document scope and contact Relativity Support
3. **Notify Legal team** if legal hold documents potentially affected
4. **Preserve audit trail** - export audit records immediately

**Recovery Steps:**
1. Contact Relativity Support immediately:
   - Email: support@relativity.com
   - Note: Deletion recovery is time-sensitive
2. Provide:
   - Workspace ID
   - Approximate time of deletion
   - Estimated document count
   - Any document identifiers (if known)
3. Document everything for potential legal implications

**Investigation:**
- Review user's recent activity
- Check for credential compromise
- Determine how user gained access to perform operation

### Scenario B: Legal Hold Documents Affected (CRITICAL)

**Symptoms:** Mass operation affected documents under legal hold

**IMMEDIATE ESCALATION TO LEGAL TEAM**

**Documentation Required:**
- [ ] List of affected documents (control numbers)
- [ ] Legal hold names/identifiers
- [ ] Operation performed
- [ ] User who performed operation
- [ ] Timestamp
- [ ] Current document status

**Response:**
1. Halt any further operations on affected documents
2. Preserve all audit records
3. Engage legal counsel immediately
4. Document remediation steps
5. Prepare spoliation analysis if deletions occurred

### Scenario C: Large Mass Edit

**Symptoms:** MassEdit affecting >1,000 documents

**Investigation:**
1. Identify field(s) being edited
2. Determine old vs. new values
3. Verify alignment with project requirements

**Field Risk Assessment:**

| Field Type | Risk Level | Review Required |
|------------|------------|-----------------|
| Privileged | HIGH | Attorney review |
| Responsive | HIGH | QC review |
| Confidential | HIGH | Client approval |
| Custodian | MEDIUM | Data integrity |
| Custom coding | MEDIUM | Workflow impact |
| Administrative | LOW | Logging only |

**Response:**

```
IF Field is privileged/confidential AND unauthorized:
  → Attempt reversal via mass edit
  → Full audit and impact analysis
  → Client notification may be required

IF Field is standard coding AND authorized:
  → Log and monitor
  → Verify QC procedures followed
```

### Scenario D: Mass Operation Performance Issues

**Symptoms:** Mass operation running slowly or timing out

**Investigation:**
1. Check operation size (document count)
2. Review system resource utilization
3. Check for concurrent operations

**Resolution Options:**
- Wait for completion (may be normal for large operations)
- Cancel and retry during off-peak hours
- Break into smaller batches
- Check for system resource constraints

### Scenario E: Bulk Tag Operations

**Symptoms:** Large-scale tagging affecting review workflow

**Investigation:**
1. Identify tags being applied/removed
2. Determine workflow impact
3. Verify reviewer coordination

**Response:**
- If authorized and documented: Monitor completion
- If affecting active review: Coordinate with review manager
- If unauthorized: Pause and investigate

---

## Mass Operation Best Practices

### Pre-Operation Checklist
- [ ] Document business justification
- [ ] Obtain necessary approvals
- [ ] Verify saved search returns expected documents
- [ ] Check for legal hold conflicts
- [ ] Schedule during low-activity period
- [ ] Notify affected team members
- [ ] Create backup/export if critical data

### During Operation
- [ ] Monitor progress
- [ ] Watch for errors
- [ ] Be prepared to cancel if issues arise
- [ ] Document actual vs. expected results

### Post-Operation
- [ ] Verify completion
- [ ] Spot-check results
- [ ] Update documentation
- [ ] Notify stakeholders

---

## Rollback Procedures

### Mass Edit Reversal
1. Document original field values (from audit if available)
2. Create saved search for affected documents
3. Perform mass edit to restore original values
4. Verify restoration
5. Document rollback

### Mass Delete Recovery
**Time-sensitive - Contact Relativity Support immediately**

1. Gather information:
   - Workspace ID
   - Deletion timestamp
   - Document count
   - Any available document identifiers

2. Contact support:
   - Phone: Check Relativity Community for support number
   - Email: support@relativity.com
   - Priority: Urgent/Critical

3. Recovery depends on:
   - Time since deletion
   - Backup availability
   - RelativityOne data retention policies

### Mass Move Reversal
1. Identify destination folder(s)
2. Create saved search for moved documents
3. Mass move back to original location
4. Verify folder structure restored
5. Document rollback

---

## Monitoring Configuration

### Audit API Polling Queries

**Mass Deletions (Poll every 5 minutes):**
```json
{
  "condition": "'Action' == 'MassDelete' AND 'Timestamp' > '<5_MINUTES_AGO>'"
}
```

**Large Mass Edits (Poll every 15 minutes):**
```json
{
  "condition": "'Action' == 'MassEdit' AND 'Timestamp' > '<15_MINUTES_AGO>'"
}
```

### Alert Thresholds

| Operation | Warning | High | Critical |
|-----------|---------|------|----------|
| Mass Delete | >50 docs | >100 docs | >500 docs or legal hold |
| Mass Edit | >500 docs | >1,000 docs | >5,000 docs |
| Mass Tag | >1,000 docs | >5,000 docs | >10,000 docs |
| Mass Move | >1,000 docs | >5,000 docs | Cross-workspace |

---

## Escalation Procedures

### Escalation Matrix

| Scenario | Initial | Escalation | Legal |
|----------|---------|------------|-------|
| Unauthorized mass delete | Security Team | CISO | Always |
| Legal hold affected | Team Lead | Legal | Always/Immediate |
| Large unauthorized edit | Team Lead | Manager | If privileged fields |
| Performance issues | On-call | Team Lead | No |
| Authorized large operation | Log only | - | No |

### Information for Escalation

- [ ] Operation type and scope
- [ ] User and authorization status
- [ ] Affected documents (count, identifiers if available)
- [ ] Legal hold status
- [ ] Timeline
- [ ] Current status (in progress, completed, cancelled)
- [ ] Potential business impact

---

## Post-Incident Actions

### Immediate
- [ ] Verify operation status (completed, cancelled, reversed)
- [ ] Document outcome
- [ ] Notify affected parties

### Short-term (24-48 hours)
- [ ] Complete incident report
- [ ] Review authorization procedures
- [ ] Implement additional controls if needed
- [ ] User training if human error

### Long-term
- [ ] Review mass operation policies
- [ ] Enhance monitoring thresholds
- [ ] Update approval workflows
- [ ] Consider technical controls (confirmations, limits)

---

## Prevention Measures

### Technical Controls
- Implement confirmation dialogs for large operations
- Set system limits on mass operation size
- Require supervisor approval for operations above threshold
- Enable detailed audit logging

### Process Controls
- Documented approval workflow
- Pre-operation checklist requirement
- Post-operation verification requirement
- Regular access reviews

### Training
- Mass operation procedures
- Legal hold awareness
- Audit trail importance
- Escalation procedures

---

## API Reference

### Audit API for Mass Operations

```bash
# Query mass operations
POST /relativity.audit/{version}/workspaces/{workspaceID}/audits/query

# Get specific audit record details
GET /relativity.audit/{version}/workspaces/{workspaceID}/audits/{auditID}
```

### Object Manager for Verification

```bash
# Query documents by saved search
POST /Relativity.ObjectManager/{version}/workspace/{workspaceID}/object/query

# Get document field values
GET /Relativity.ObjectManager/{version}/workspace/{workspaceID}/object/{artifactID}
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
