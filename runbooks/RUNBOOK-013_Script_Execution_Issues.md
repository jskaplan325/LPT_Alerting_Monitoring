# RUNBOOK-013: RelativityOne Script Execution Issues

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Relativity Script Issues |
| **Severity** | HIGH (Failure/Unauthorized) / MEDIUM (Performance) / LOW (Monitoring) |
| **Platform** | RelativityOne |
| **Detection** | Audit API (RelativityScriptExecution action) |
| **Response SLA** | High: 1 hour / Medium: 4 hours / Low: Next business day |
| **Escalation** | On-call → Team Lead → Relativity Support |

## Alert Conditions

```
IF Script_Execution_Failed THEN HIGH
IF Execution_Time > 30000ms THEN MEDIUM (performance)
IF Unauthorized_Script_Execution THEN HIGH
IF Script_Execution_Frequency > threshold THEN MEDIUM (investigate)
IF Script_Affects_Large_Document_Count THEN MEDIUM
```

---

## Script Monitoring via Audit

The primary method for monitoring script execution is the Audit application:
- Filter for **RelativityScriptExecution** action
- Review execution frequency, times, and impact

### Key Audit Fields

| Field | Purpose |
|-------|---------|
| Timestamp | When script ran |
| User Name | Who executed |
| Action | RelativityScriptExecution |
| Execution Time (ms) | Performance metric |
| Details | Script name, parameters |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge in monitoring system
- [ ] Identify script name and executor
- [ ] Determine if script is still running
- [ ] Open tracking ticket

### Step 2: Quick Assessment

**Questions to answer:**
- Is this an authorized script?
- Is the user authorized to run scripts?
- Is this part of normal operations?
- Is the execution time abnormal?

**Record the following:**
- Script Name: ________________
- User: ________________
- Workspace: ________________
- Execution Time (ms): ________________
- Timestamp: ________________
- Status (Success/Failed): ________________

---

## Investigation Procedures

### Step 3: Query Script Executions via Audit API

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
        {"Name": "Execution Time (ms)"},
        {"Name": "Details"}
      ],
      "condition": "'\''Action'\'' == '\''RelativityScriptExecution'\''",
      "sorts": [{"FieldIdentifier": {"Name": "Timestamp"}, "Direction": "Descending"}],
      "length": 50
    }
  }'
```

### Step 4: Analyze Execution Time

**Performance Thresholds:**

| Execution Time | Assessment | Action |
|----------------|------------|--------|
| < 5,000 ms | Normal | No action |
| 5,000 - 15,000 ms | Moderate | Monitor |
| 15,000 - 30,000 ms | Elevated | Investigate |
| > 30,000 ms | High | Performance tuning needed |
| > 60,000 ms | Critical | Immediate review |

### Step 5: Review Script Details

**Identify:**
- What does the script do?
- What data does it access/modify?
- How often is it run?
- Who has access to run it?

### Step 6: Check for Impact

**Potential impacts:**
- System performance degradation
- Data modification
- User experience issues
- Resource consumption

---

## Resolution Procedures

### Scenario A: Script Execution Failed

**Symptoms:** Script returned error or failed to complete

**Steps:**
1. Review error details in audit record
2. Common failure causes:

| Cause | Resolution |
|-------|------------|
| Permission error | Verify user permissions |
| Syntax error | Review script code |
| Data not found | Check object availability |
| Timeout | Optimize script or data scope |
| Resource error | Check system resources |

3. **For custom scripts:**
   - Review script code
   - Test in development environment
   - Fix and redeploy

4. **For system scripts:**
   - Check prerequisites
   - Verify configuration
   - Contact Relativity if persistent

### Scenario B: Long-Running Script (Performance)

**Symptoms:** Execution Time > 30,000 ms

**Investigation:**
1. Identify script and its purpose
2. Review recent execution history
3. Compare to baseline performance
4. Check concurrent system activity

**Resolution Options:**

| Cause | Resolution |
|-------|------------|
| Large data set | Add filters to reduce scope |
| Inefficient query | Optimize SQL/queries |
| Missing indexes | Add appropriate indexes |
| Resource contention | Schedule during off-peak |
| Script logic | Refactor for efficiency |

### Scenario C: Unauthorized Script Execution

**Symptoms:** Script run by unauthorized user

**SECURITY CONCERN - Escalate if suspicious**

**Steps:**
1. Verify user's authorization
2. Review what the script does
3. Check for data access/modification
4. Determine if intentional or error

**Response:**
```
IF User should not have script access THEN
  → Remove script permissions immediately
  → Review permission grants
  → Security incident investigation

IF Script is malicious or unauthorized THEN
  → Disable script
  → Full security review
  → Audit data impact
```

### Scenario D: Unusual Script Frequency

**Symptoms:** Script running more often than normal

**Investigation:**
1. Review execution pattern
2. Is this automated (scheduled)?
3. Is this user-initiated?
4. Check for infinite loops or misconfigurations

**Resolution:**
- If scheduled: Review schedule configuration
- If manual: Communicate with users
- If error: Fix triggering condition

---

## Script Performance Optimization

### Best Practices for Script Performance

| Practice | Benefit |
|----------|---------|
| Limit result sets | Faster execution |
| Use appropriate indexes | Query efficiency |
| Avoid cursor operations | SQL performance |
| Batch large operations | Memory management |
| Test before production | Identify issues early |

### Performance Monitoring Setup

**Audit Query for Slow Scripts:**
```json
{
  "condition": "'Action' == 'RelativityScriptExecution' AND 'Execution Time (ms)' > 30000"
}
```

**Alert Rule:**
```
IF Execution_Time > 30000 THEN MEDIUM
IF Execution_Time > 60000 THEN HIGH
IF Script_Frequency > normal_baseline * 2 THEN MEDIUM
```

---

## Script Security Considerations

### Permission Requirements
- Scripts require appropriate permissions to execute
- Review who can run scripts
- Audit script execution regularly

### Script Categories

| Category | Risk Level | Monitoring |
|----------|------------|------------|
| Read-only scripts | Low | Standard |
| Data modification | Medium | Enhanced |
| Admin/system scripts | High | Close monitoring |
| Custom scripts | Variable | Per script review |

### Security Review Triggers
- New script deployment
- Script permission changes
- Unusual execution patterns
- Failed executions
- Performance anomalies

---

## Escalation Procedures

### When to Escalate

| Condition | Level | Timeframe |
|-----------|-------|-----------|
| Unauthorized execution | Security Team | Immediate |
| Script causing system issues | Relativity Support | 30 min |
| Persistent failures | Team Lead | 2 hours |
| Performance degradation | Team Lead | 4 hours |
| Data corruption suspected | Security + Support | Immediate |

### Information for Escalation

- [ ] Script name and purpose
- [ ] User who executed
- [ ] Execution time and timestamp
- [ ] Error messages (if failed)
- [ ] Frequency pattern
- [ ] System impact observed

---

## Post-Incident Actions

### Immediate
- [ ] Verify script status (running, completed, failed)
- [ ] Document findings
- [ ] Address any immediate issues

### Short-term (24 hours)
- [ ] Complete incident report
- [ ] Review script permissions
- [ ] Optimize if performance issue

### Long-term
- [ ] Regular script audits
- [ ] Performance baseline updates
- [ ] Permission reviews

---

## Prevention Measures

### Script Governance
- Document all custom scripts
- Review before deployment
- Test in non-production
- Regular permission audits

### Performance Monitoring
- Track execution time trends
- Alert on threshold breaches
- Regular performance reviews
- Optimize high-frequency scripts

### Security Controls
- Principle of least privilege
- Regular permission reviews
- Audit log monitoring
- Change management for scripts

---

## API Reference

### Audit Query for Script Execution

```bash
POST /relativity.audit/{version}/workspaces/{workspaceID}/audits/query

# Filter for script executions
{
  "request": {
    "objectType": {"artifactTypeID": 1000042},
    "fields": [
      {"Name": "Timestamp"},
      {"Name": "User Name"},
      {"Name": "Action"},
      {"Name": "Execution Time (ms)"},
      {"Name": "Details"}
    ],
    "condition": "'Action' == 'RelativityScriptExecution'"
  }
}
```

### Performance Analysis Query

```json
{
  "condition": "'Action' == 'RelativityScriptExecution' AND 'Timestamp' > '<7_DAYS_AGO>'"
}
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
