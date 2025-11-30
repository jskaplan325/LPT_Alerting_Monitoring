# RUNBOOK-015: RelativityOne Data Export and Transfer Monitoring

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Data Export/Transfer Alerts |
| **Severity** | CRITICAL (Exfiltration Risk) / HIGH (Large Export) / MEDIUM (Standard) |
| **Platform** | RelativityOne |
| **Detection** | Audit API + Export API |
| **Response SLA** | Critical: Immediate / High: 30 min / Medium: 4 hours |
| **Escalation** | Security Team → CISO → Legal (if breach suspected) |

## Alert Conditions

### Export Volume Alerts
```
IF Export_Document_Count > 50,000 THEN CRITICAL
IF Export_Document_Count > 10,000 THEN HIGH
IF Export_Document_Count > 5,000 THEN MEDIUM
IF Multiple_Large_Exports_Same_User_24h THEN CRITICAL
```

### Data Transfer Alerts
```
IF ARM_Export_Size > threshold THEN HIGH
IF ARM_Export_To_External THEN CRITICAL
IF Transfer_After_Hours THEN HIGH
IF Unauthorized_Export_User THEN CRITICAL
```

### Export Failure Alerts
```
IF Export_Job_Failed THEN HIGH
IF Export_Timeout THEN MEDIUM
IF Export_Stuck > 2 hours THEN MEDIUM
```

---

## Export Types to Monitor

| Export Type | Risk Level | Primary Concern |
|-------------|------------|-----------------|
| Production Export | HIGH | Client delivery, data leakage |
| Load File Export | HIGH | Data extraction |
| Native Export | CRITICAL | Original files leaving platform |
| Image Export | HIGH | Document images |
| ARM (Archive) | CRITICAL | Full workspace/matter export |
| Report Export | LOW | Metadata only |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge in monitoring system
- [ ] Identify export type and size
- [ ] Determine user and authorization
- [ ] Open security ticket if suspicious

### Step 2: Quick Assessment

**Determine:**
- Is this an authorized export?
- Is there a production/project requiring this?
- Is the user authorized for exports?
- Is the destination internal or external?

**Record the following:**
- Export Type: ________________
- User: ________________
- Workspace: ________________
- Document Count: ________________
- Destination: ________________
- Timestamp: ________________
- Authorization Reference: ________________

---

## Investigation Procedures

### Step 3: Query Export Activity via Audit

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
      "condition": "'\''Action'\'' == '\''Export'\''",
      "sorts": [{"FieldIdentifier": {"Name": "Timestamp"}, "Direction": "Descending"}],
      "length": 50
    }
  }'
```

### Step 4: Review User Export History

```json
{
  "condition": "'Action' == 'Export' AND 'User Name' == '<SUSPECT_USER>' AND 'Timestamp' > '<7_DAYS_AGO>'"
}
```

**Analyze:**
- Export frequency
- Volume trends
- Timing patterns
- Destination patterns

### Step 5: Verify Authorization

Check for:
- Documented project requirement
- Client delivery request
- Production requiring export
- User's role and permissions
- Approval workflows followed

### Step 6: Determine Destination

**Internal vs External:**
- Internal transfer (within organization)
- External delivery (client, opposing counsel)
- Unknown destination (investigate)

---

## Resolution Procedures

### Scenario A: Large Unauthorized Export (CRITICAL)

**Symptoms:** Large export by unauthorized user or without approval

**Immediate Actions:**
1. **If in progress:** Attempt to cancel/stop
2. **If completed:** Document scope immediately
3. **Preserve audit records**
4. **Notify Security Team**

**Investigation:**
1. Identify all data exported
2. Determine destination
3. Assess data sensitivity:
   - Privileged documents included?
   - PII/PHI present?
   - Confidential client data?

**Response Matrix:**

| Finding | Action |
|---------|--------|
| Authorized but undocumented | Document and counsel user |
| Unauthorized user | Security incident, suspend access |
| External destination unauthorized | Potential breach, legal notification |
| Sensitive data exposed | Full incident response |

### Scenario B: Potential Data Exfiltration

**Symptoms:** Suspicious export patterns suggesting data theft

**Indicators:**
- Multiple large exports in short period
- After-hours export activity
- Export by departing employee
- Export to unknown destination
- Unusual file types or selections

**Response:**
1. **Immediate:** Suspend user access pending investigation
2. **Document:** Full export history
3. **Notify:** Security, Legal, HR as appropriate
4. **Investigate:** Interview user, review work context
5. **Assess:** Data sensitivity and exposure

**Legal Considerations:**
- Preserve all evidence
- Document chain of custody
- Engage legal counsel
- Consider notification requirements

### Scenario C: Export Job Failed

**Symptoms:** Export failed to complete

**Steps:**
1. Review error message
2. Common failures:

| Error | Cause | Resolution |
|-------|-------|------------|
| Timeout | Large export | Break into smaller batches |
| Permission error | Access issue | Verify permissions |
| Storage error | Disk space | Clear space or escalate |
| File error | Corrupt files | Identify and exclude |

3. **Retry or recreate export**
4. **Monitor for successful completion**

### Scenario D: ARM Export Monitoring

**ARM (Archive/Restore Manager) exports entire workspaces**

**Risk Level: CRITICAL - Full data extraction**

**Alert Conditions:**
```
IF ARM_Export_Initiated THEN HIGH
IF ARM_Export_Size > 50GB THEN CRITICAL
IF ARM_Export_Completed THEN LOG for audit
```

**Required Review:**
- Who initiated?
- What workspace/matter?
- What is the destination?
- Is this authorized matter closure?
- Is ARM export policy followed?

### Scenario E: After-Hours Export Activity

**Symptoms:** Export activity outside business hours

**Investigation:**
1. Verify user's time zone
2. Check if deadline-driven (legitimate)
3. Review what was exported
4. Compare to normal patterns

**Response:**
```
IF Legitimate deadline work THEN
  → Document and close
  → Note for pattern baseline

IF User cannot explain THEN
  → Detailed investigation
  → Review all after-hours activity
  → Consider credential compromise
```

---

## Export Monitoring Dashboard

### Key Metrics to Track

| Metric | Purpose | Alert Threshold |
|--------|---------|-----------------|
| Export volume (daily) | Trend monitoring | >2x normal |
| Export count by user | Identify outliers | Top 5 exporters |
| Large exports (>10k docs) | Review required | All occurrences |
| After-hours exports | Security monitoring | All occurrences |
| External destination exports | Data loss prevention | All occurrences |

### Daily Export Summary Query

```json
{
  "condition": "'Action' == 'Export' AND 'Timestamp' > '<24_HOURS_AGO>'"
}
```

---

## Data Loss Prevention (DLP) Integration

### Export Controls

| Control | Purpose |
|---------|---------|
| Export permissions | Limit who can export |
| Export size limits | Prevent bulk extraction |
| Approval workflows | Require authorization |
| Audit logging | Track all exports |
| Destination controls | Restrict external transfer |

### DLP Alert Rules

```
# Large export alert
IF Export AND Document_Count > 10000 THEN ALERT(HIGH)

# Frequency alert
IF Export_Count_By_User_24h > 5 THEN ALERT(MEDIUM)

# After-hours alert
IF Export AND Time NOT IN (BusinessHours) THEN ALERT(MEDIUM)

# External destination alert
IF Export AND Destination == External THEN ALERT(HIGH)
```

---

## Escalation Procedures

### Escalation Matrix

| Scenario | Initial | Escalation | Legal |
|----------|---------|------------|-------|
| Large unauthorized export | Security Team | CISO | If sensitive data |
| Suspected exfiltration | Security Team | CISO + Legal | Always |
| Export job failure | On-call | Team Lead | No |
| ARM export | Team Lead | Manager | For approval |
| External destination | Security Team | CISO | Review required |

### Information for Escalation

- [ ] Export type and size
- [ ] User identification
- [ ] Authorization status
- [ ] Data sensitivity assessment
- [ ] Destination details
- [ ] Full audit trail
- [ ] Potential impact

---

## Post-Incident Actions

### Immediate
- [ ] Verify export status
- [ ] Document findings
- [ ] Secure any exposed data

### Short-term (24-48 hours)
- [ ] Complete incident report
- [ ] Review export policies
- [ ] User training if needed
- [ ] Update access controls

### Long-term
- [ ] Policy review
- [ ] Technical controls enhancement
- [ ] Monitoring rule updates
- [ ] Training program updates

---

## Prevention Measures

### Technical Controls
- Implement export size limits
- Require approval for large exports
- Restrict export permissions
- Enable comprehensive audit logging
- Consider DLP tools integration

### Process Controls
- Documented export procedures
- Approval workflows
- Regular access reviews
- Export justification requirements

### User Training
- Export policy awareness
- Data handling procedures
- Reporting suspicious activity
- Consequences of policy violations

---

## API Reference

### Audit API for Exports

```bash
# Query export actions
POST /relativity.audit/{version}/workspaces/{workspaceID}/audits/query

{
  "condition": "'Action' == 'Export'"
}
```

### Export Statistics Query

```bash
# Get export summary by user
{
  "request": {
    "objectType": {"artifactTypeID": 1000042},
    "fields": [
      {"Name": "User Name"},
      {"Name": "Action"},
      {"Name": "Details"}
    ],
    "condition": "'Action' == 'Export' AND 'Timestamp' > '<24_HOURS_AGO>'"
  }
}
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
