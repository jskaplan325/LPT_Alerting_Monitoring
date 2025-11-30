# RUNBOOK-009: RelativityOne Audit and Compliance Monitoring

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Audit and Compliance Alerts |
| **Severity** | Varies by alert type |
| **Platform** | RelativityOne Audit API |
| **Detection** | Audit API polling (5-15 min intervals) |
| **Response SLA** | Per severity matrix |
| **Escalation** | Security Team → Compliance → Legal |

## Alert Categories

### Data Exfiltration Prevention
```
IF Export_Document_Count > 10,000 THEN MEDIUM (review required)
IF Export_Document_Count > 50,000 THEN HIGH
IF Export_To_External_Destination THEN HIGH
IF Multiple_Large_Exports_Same_User_24h THEN CRITICAL
```

### Suspicious Activity Detection
```
IF Mass_Delete_Count > 100 THEN HIGH
IF Mass_Edit_Count > 1,000 in 1 hour THEN MEDIUM
IF After_Hours_Activity AND Sensitive_Actions THEN HIGH
IF Unusual_Access_Pattern THEN MEDIUM
```

### Compliance Monitoring
```
IF Audit_Export_Failed THEN HIGH
IF Audit_Retention_Policy_Violated THEN CRITICAL
IF Legal_Hold_Modified THEN HIGH
IF Privileged_Document_Accessed THEN MEDIUM (log)
```

---

## Audit Action Types Reference

### High-Risk Actions (Always Alert)

| Action | Risk Level | Alert Threshold |
|--------|------------|-----------------|
| Export | High | >10,000 docs |
| MassDelete | Critical | >100 docs |
| MassEdit | Medium | >1,000 ops/hour |
| Delete | High | Unexpected deletions |
| Permission Change | High | Privilege elevation |

### Medium-Risk Actions (Monitor)

| Action | Risk Level | Alert Threshold |
|--------|------------|-----------------|
| Download | Medium | High volume patterns |
| Print | Medium | Bulk printing |
| View | Low | After-hours access |
| Login | Medium | Failed attempts |
| Copy | Medium | Bulk copy operations |

### Administrative Actions (Audit Trail)

| Action | Audit Purpose |
|--------|---------------|
| Create User | Access management |
| Modify User | Permission changes |
| Group Membership | Role assignments |
| Workspace Create/Delete | Environment changes |
| Script Execution | Automation tracking |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge in monitoring system
- [ ] Identify alert type and severity
- [ ] Note user, workspace, and action details
- [ ] Open security/compliance ticket

### Step 2: Quick Assessment

**Determine:**
- Is this authorized activity?
- Is there an active project justifying the activity?
- Does the user's role authorize this action?
- Is there a pattern of suspicious behavior?

**Record the following:**
- User Name: ________________
- Action Type: ________________
- Workspace: ________________
- Timestamp: ________________
- Affected Count: ________________
- Business Justification (if known): ________________

---

## Investigation Procedures

### Step 3: Query Audit Records

**Instance-Level Audit Query (workspaceID = -1):**
```bash
curl -X POST "<host>/Relativity.REST/api/relativity.audit/v1/workspaces/-1/audits/query" \
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
        {"Name": "Object Type"},
        {"Name": "Details"},
        {"Name": "Execution Time (ms)"}
      ],
      "condition": "'\''Timestamp'\'' > '\''2024-01-15T00:00:00Z'\''",
      "sorts": [{"FieldIdentifier": {"Name": "Timestamp"}, "Direction": "Descending"}],
      "length": 100
    }
  }'
```

**Workspace-Level Audit Query:**
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
        {"Name": "Details"}
      ],
      "condition": "'\''User Name'\'' == '\''suspicious.user@company.com'\''"
    }
  }'
```

### Step 4: Get Audit Metrics

```bash
curl -X GET "<host>/Relativity.REST/api/relativity.audit.metrics/workspaces/-1/audit-metrics/" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -"
```

### Step 5: Build User Activity Profile

Query user's recent activity:
```json
{
  "request": {
    "objectType": {"artifactTypeID": 1000042},
    "fields": [
      {"Name": "Timestamp"},
      {"Name": "Action"},
      {"Name": "Object Type"},
      {"Name": "Details"}
    ],
    "condition": "'User Name' == '<USER>' AND 'Timestamp' > '<7_DAYS_AGO>'"
  }
}
```

**Analyze:**
- Normal working hours vs. after-hours activity
- Typical actions vs. unusual actions
- Volume compared to peers
- Access to sensitive workspaces

---

## Alert Response Procedures

### Scenario A: Large Data Export

**Alert:** Export >10,000 documents

**Triage Questions:**
1. Is there an active production requiring export?
2. Is the user authorized for exports?
3. Is the export destination internal or external?
4. Is this part of normal workflow?

**Investigation:**
```json
{
  "condition": "'Action' == 'Export' AND 'User Name' == '<USER>'"
}
```

**Response Matrix:**

| Situation | Action |
|-----------|--------|
| Authorized production export | Log and close |
| Authorized but unusually large | Verify with project lead |
| Unauthorized user | Suspend export, escalate |
| External destination | Immediate security review |

**Escalation:**
- If unauthorized: Security Team → CISO
- If potential breach: Legal Team notification

### Scenario B: Mass Deletion

**Alert:** MassDelete >100 documents

**CRITICAL: Mass deletion may be irreversible**

**Immediate Actions:**
1. Identify user and workspace
2. Determine if deletion is in progress or completed
3. Check if this is authorized (e.g., data cleanup project)

**Investigation:**
```json
{
  "condition": "'Action' IN ['Delete', 'MassDelete'] AND 'Timestamp' > '<24_HOURS_AGO>'"
}
```

**Response:**

| Situation | Action |
|-----------|--------|
| Authorized cleanup | Verify scope, log |
| Unauthorized | Immediate escalation to support for potential recovery |
| Legal hold data | CRITICAL - Escalate to Legal immediately |

**Recovery:**
- Contact Relativity Support immediately for deletion recovery
- Time-sensitive: Deletions may be recoverable within limited window
- Document everything for potential legal implications

### Scenario C: After-Hours Suspicious Activity

**Alert:** Sensitive actions during non-business hours

**Investigation:**
1. Query user activity for time period
2. Compare to user's normal patterns
3. Check if user is in different timezone (legitimate)
4. Identify specific actions taken

```json
{
  "condition": "'User Name' == '<USER>' AND 'Timestamp' BETWEEN '<AFTER_HOURS_START>' AND '<AFTER_HOURS_END>'"
}
```

**Response:**
```
IF User confirms legitimate work THEN
  → Document and close

IF User denies activity OR cannot be reached THEN
  → Suspend account pending investigation
  → Full audit review
  → Potential credential compromise
```

### Scenario D: Permission Elevation

**Alert:** User granted elevated privileges

**Investigation:**
1. Who made the change?
2. What permissions were granted?
3. Is there documented authorization?

```json
{
  "condition": "'Action' == 'Permission Change' AND 'Details' LIKE '%<USER>%'"
}
```

**Response:**
```
IF Authorized (ticket/approval exists) THEN
  → Log and close
  → Verify principle of least privilege

IF Unauthorized THEN
  → Revert permissions immediately
  → Investigate granting user
  → Security incident procedures
```

### Scenario E: Audit Export/Retention Issues

**Alert:** Audit export failed or retention policy concern

**Impact:** Compliance and legal discovery obligations

**Investigation:**
1. Check audit export job status
2. Verify retention configuration
3. Identify affected time period

**Response:**
- If export failed: Retry immediately, investigate root cause
- If data missing: CRITICAL - Engage compliance team
- Document all gaps for potential legal disclosure

---

## Compliance Monitoring Queries

### Daily Compliance Check Queries

**Large Exports (Last 24 Hours):**
```json
{
  "condition": "'Action' == 'Export' AND 'Timestamp' > '<24_HOURS_AGO>'"
}
```

**Mass Operations (Last 24 Hours):**
```json
{
  "condition": "'Action' IN ['MassDelete', 'MassEdit'] AND 'Timestamp' > '<24_HOURS_AGO>'"
}
```

**Failed Logins:**
```json
{
  "condition": "'Action' == 'Login Failed' AND 'Timestamp' > '<24_HOURS_AGO>'"
}
```

**Permission Changes:**
```json
{
  "condition": "'Action' IN ['Permission Change', 'Group Membership Change'] AND 'Timestamp' > '<24_HOURS_AGO>'"
}
```

### Weekly Compliance Reports

Generate reports for:
- Export activity summary by user
- Access patterns by workspace
- Administrative actions summary
- Failed login trends
- Script execution audit

---

## Audit Data Retention

### Requirements
- Ensure audit data meets regulatory retention requirements
- Configure appropriate retention periods
- Regular verification of audit data integrity

### Export Schedule
- Daily: Incremental audit export to archive
- Weekly: Full audit report generation
- Monthly: Compliance review of audit trends
- Quarterly: Retention policy verification

### Audit Export Automation
Configure scheduled exports to:
- SIEM platform for real-time analysis
- Archive storage for long-term retention
- Compliance reporting system

---

## Escalation Procedures

### Escalation Matrix

| Alert Type | Initial | Escalation | Legal |
|------------|---------|------------|-------|
| Large Export | Security Team | CISO | If breach suspected |
| Mass Deletion | Security Team | CISO + Legal | Always for legal hold |
| Unauthorized Access | Security Team | CISO | If data compromised |
| Compliance Gap | Compliance | Legal | Always |
| Credential Compromise | Security Team | CISO | If data accessed |

### Information for Escalation

- [ ] Full audit trail for affected user/time period
- [ ] Specific actions and affected documents
- [ ] User's role and normal access patterns
- [ ] Business context (projects, deadlines)
- [ ] Potential data sensitivity/classification
- [ ] Timeline of events

---

## Post-Incident Actions

### Immediate
- [ ] Document all findings
- [ ] Implement immediate controls if needed
- [ ] Notify affected parties as required

### Short-term (24-72 hours)
- [ ] Complete incident report
- [ ] Review access controls
- [ ] Update monitoring rules if gaps found
- [ ] User communication/training if needed

### Long-term
- [ ] Policy review and updates
- [ ] Enhanced monitoring implementation
- [ ] Training program updates
- [ ] Compliance reporting updates

---

## Prevention and Monitoring

### Proactive Monitoring Setup

**Real-time Alerts (SIEM Integration):**
```
# Export monitoring
IF action == "Export" AND document_count > 10000 THEN alert(HIGH)

# Mass operation monitoring
IF action IN ("MassDelete", "MassEdit") AND count > 100 THEN alert(HIGH)

# After-hours monitoring
IF timestamp.hour NOT IN (8-18) AND action IN (sensitive_actions) THEN alert(MEDIUM)

# Failed login monitoring
IF action == "Login Failed" AND count_by_user_10min > 5 THEN alert(HIGH)
```

### Access Control Best Practices
- Implement principle of least privilege
- Regular access reviews (quarterly)
- Separate admin accounts from daily use
- Document all elevated access grants

### Audit Configuration
- Enable detailed audit logging
- Configure appropriate retention periods
- Regular audit export verification
- Test audit query capabilities

---

## API Reference

### Audit API Endpoints

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Query Audits | POST | `/relativity.audit/{version}/workspaces/{workspaceID}/audits/query` |
| Get Audit Metrics | GET | `/relativity.audit.metrics/workspaces/-1/audit-metrics/` |
| Export Audits | POST | `/relativity.audit/{version}/workspaces/{workspaceID}/audits/export` |

### Instance vs Workspace Queries
- **Instance-level (workspaceID = -1):** Cross-workspace queries, admin actions
- **Workspace-level:** Specific workspace activity

### Rate Limits
- Be mindful of query frequency
- Use appropriate time windows
- Implement caching for repeated queries

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
