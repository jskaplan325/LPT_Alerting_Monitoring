# RUNBOOK-004: RelativityOne Security Alerts

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Security Center Alerts |
| **Severity** | Varies (Critical/High/Medium/Low) |
| **Platform** | RelativityOne Security Center |
| **Detection** | Native push notifications + Audit API |
| **Response SLA** | Critical: Immediate / High: 1 hour / Medium: 4 hours |
| **Escalation** | Security Team → CISO → Relativity Support |

## Alert Types and Severity

RelativityOne Security Center provides native alerting for the following security events:

| Alert Type | Severity | Trigger Condition |
|------------|----------|-------------------|
| Brute Force Login | **Critical** | 50+ failed logins within 1 hour |
| Multiple Failed Logins | **High** | Multiple failed attempts (below brute force threshold) |
| Login Method Change | **High** | User's authentication method changed |
| New Login Location | **Medium** | Login from previously unseen location |
| Lockbox Setting Modified | **Critical** | Changes to lockbox configuration |
| Account Disabled | **Medium** | User account was disabled |
| Permission Elevation | **High** | User granted elevated privileges |
| Group Membership Change | **Medium** | User added to security-sensitive group |
| Inactive User Login | **Medium** | User inactive >30 days logged in |

---

## Alert States

| State | Meaning | Action Required |
|-------|---------|-----------------|
| **Unresolved** | New alert, requires investigation | Investigate immediately |
| **Dismissed** | False positive, no action needed | Document reason for dismissal |
| **Resolved** | Confirmed threat, remediation complete | May trigger automated remediation |

**IMPORTANT:** Some alerts trigger **automated remediation** when marked as "Resolved":
- Brute Force Login → Automatically disables affected user account
- Permission Elevation → May revert permission changes
- Group Membership Change → May remove unauthorized membership

---

## Security Notifications Configuration

### Prerequisites
Ensure proper Security Center configuration:

1. **Security Notifications Group:**
   - At least 2 administrators must be members
   - Members receive automated email notifications
   - Navigate to: **Instance Settings** → **Security Notifications**

2. **Enable Two-Factor Authentication:**
   - Required for all admin accounts
   - Reduces risk of credential compromise

3. **Alert Manager Agent:**
   - Must be running with 30-second interval (recommended)
   - Check: **Agents** tab → Filter "Alert Manager"

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Note alert type and severity from notification
- [ ] Open Security Center immediately
- [ ] Create security incident ticket

### Step 2: Access Security Center
1. Log into RelativityOne
2. Navigate to **Security Center**
3. Locate the triggered alert
4. Review alert details

### Step 3: Initial Assessment

**Record the following:**
- Alert Type: ________________
- Severity: ________________
- Affected User: ________________
- Timestamp: ________________
- Source IP (if available): ________________
- Location (if available): ________________
- Related Workspace: ________________

---

## Investigation Procedures by Alert Type

### Alert: Brute Force Login (CRITICAL)

**Definition:** 50+ failed login attempts within 1 hour for a single user

**Immediate Actions (0-15 minutes):**
1. **Do NOT mark as "Resolved" yet** (will disable account)
2. Identify the affected user account
3. Check if user is currently logged in
4. Review source IP addresses

**Investigation:**

**Via Audit API - Query Failed Logins:**
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
        {"Name": "Details"}
      ],
      "condition": "'\''Action'\'' == '\''Login Failed'\'' AND '\''Timestamp'\'' > '\''<24_HOURS_AGO>'\''"
    }
  }'
```

**Analysis Questions:**
- [ ] Is this a legitimate user making typos?
- [ ] Are attempts from a single IP or distributed?
- [ ] Is the IP internal or external?
- [ ] Does the timing suggest automated attack?
- [ ] Are multiple accounts being targeted?

**Response Decision Tree:**
```
IF source_ip is known/internal AND user confirms fat-finger:
  → Dismiss alert, document reason
  → Coach user on password management

IF source_ip is external/unknown OR user denies activity:
  → Mark as "Resolved" (auto-disables account)
  → Force password reset
  → Investigate source IP
  → Consider IP blocking at firewall
  → Check for lateral movement
```

**Post-Incident:**
- [ ] Review account re-enablement process
- [ ] Ensure strong password policy enforced
- [ ] Consider additional MFA requirements

---

### Alert: Multiple Failed Logins (HIGH)

**Definition:** Multiple failed login attempts below brute force threshold

**Immediate Actions:**
1. Identify affected user
2. Contact user to verify (if business hours)
3. Review recent login history

**Investigation:**
1. Check Audit trail for user
2. Compare against normal login patterns
3. Identify source IPs

**Response:**
```
IF user confirms legitimate (forgot password):
  → Dismiss alert
  → Offer password reset assistance

IF user denies activity:
  → Force password reset
  → Enable additional monitoring
  → Consider account suspension pending investigation
```

---

### Alert: Login Method Change (HIGH)

**Definition:** User's authentication method was modified

**Immediate Actions:**
1. Identify who made the change
2. Identify what changed (MFA method, password reset, etc.)
3. Contact affected user

**Investigation:**

**Check Audit for Permission/Settings Changes:**
```bash
# Query audit for user modification events
curl -X POST "<host>/Relativity.REST/api/relativity.audit/v1/workspaces/-1/audits/query" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -" \
  -H "Content-Type: application/json" \
  -d '{
    "request": {
      "objectType": {"artifactTypeID": 1000042},
      "fields": [{"Name": "Timestamp"}, {"Name": "User Name"}, {"Name": "Action"}, {"Name": "Details"}],
      "condition": "'\''Action'\'' IN ['\''Update'\'', '\''Permission Change'\'']"
    }
  }'
```

**Response:**
```
IF change was authorized (help desk ticket, user request):
  → Dismiss alert
  → Document authorization

IF change was unauthorized:
  → Revert changes immediately
  → Lock affected account
  → Investigate administrator who made change
  → Full security incident response
```

---

### Alert: New Login Location (MEDIUM)

**Definition:** User logged in from previously unseen geographic location

**Immediate Actions:**
1. Identify user and new location
2. Check if user is traveling (calendar, HR system)
3. Contact user to verify

**Investigation:**
- Is location consistent with known travel?
- Is login from VPN that might show different location?
- What actions were taken during this session?

**Response:**
```
IF user confirms travel/VPN:
  → Dismiss alert
  → Document travel/VPN use

IF user denies travel:
  → Force immediate logout
  → Force password reset
  → Lock account pending investigation
  → Check for data access during suspicious session
```

---

### Alert: Lockbox Setting Modified (CRITICAL)

**Definition:** Changes to lockbox configuration (sensitive data protection)

**Immediate Actions:**
1. Identify what setting changed
2. Identify who made the change
3. Determine business justification

**Investigation:**
- Was change request documented (change ticket)?
- Does administrator have authorization for lockbox changes?
- What data is affected by this lockbox?

**Response:**
```
IF change was authorized and documented:
  → Dismiss alert
  → Ensure change ticket is linked

IF change was unauthorized:
  → IMMEDIATELY revert lockbox settings
  → Lock administrator account
  → Escalate to CISO
  → Full security incident investigation
  → Audit all lockbox access during exposure window
```

---

### Alert: Permission Elevation (HIGH)

**Definition:** User was granted elevated privileges

**Immediate Actions:**
1. Identify user and new permissions
2. Identify who granted permissions
3. Check for authorization

**Investigation:**
- Is there a ticket/request for this access?
- Does user's role justify the access?
- Were proper approval workflows followed?

**Response:**
```
IF properly authorized:
  → Dismiss alert
  → Document authorization reference

IF unauthorized:
  → Mark as "Resolved" (may auto-revert)
  → Remove elevated permissions manually if not auto-reverted
  → Investigate granting administrator
  → Review principle of least privilege
```

---

## Audit API Queries for Security Monitoring

### Query for Large Data Exports
```bash
curl -X POST "<host>/Relativity.REST/api/relativity.audit/v1/workspaces/{workspaceID}/audits/query" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -" \
  -H "Content-Type: application/json" \
  -d '{
    "request": {
      "objectType": {"artifactTypeID": 1000042},
      "fields": [{"Name": "Timestamp"}, {"Name": "User Name"}, {"Name": "Action"}, {"Name": "Details"}],
      "condition": "'\''Action'\'' == '\''Export'\''"
    }
  }'
```

**Alert Rule:**
```
IF Export_Document_Count > 10000 THEN MEDIUM (review)
IF Export_Document_Count > 50000 THEN HIGH
IF Export to external destination THEN HIGH
```

### Query for Mass Deletions
```bash
# Query for Delete actions
"condition": "'Action' IN ['Delete', 'MassDelete']"
```

**Alert Rule:**
```
IF MassDelete_Count > 100 THEN HIGH
IF Delete by non-admin user THEN HIGH
```

### Query for Script Executions
```bash
# Query for script performance issues
"condition": "'Action' == 'RelativityScriptExecution'"
# Check "Execution Time (ms)" field
```

**Alert Rule:**
```
IF Execution_Time > 30000ms THEN WARNING (performance)
IF unauthorized_script_execution THEN HIGH
```

---

## Escalation Procedures

### Security Escalation Matrix

| Alert Type | Initial Response | Escalation | Timeframe |
|------------|------------------|------------|-----------|
| Brute Force | Security Team | CISO if external attack | 15 min |
| Lockbox Modified | Security Team | CISO | Immediate |
| Unauthorized Access | Security Team | CISO + Legal | 30 min |
| Data Exfiltration | Security Team | CISO + Legal + Client | Immediate |
| Account Compromise | Security Team | CISO | 1 hour |

### When to Involve Relativity Support
- Suspected platform vulnerability
- Evidence of compromise affecting multiple tenants
- Need for forensic log analysis beyond available APIs
- Lockbox functionality issues

### External Reporting Requirements
Consider regulatory notification requirements (GDPR, CCPA, etc.) if:
- PII was potentially exposed
- Legal hold data was compromised
- Client data breach suspected

---

## Automated Remediation Reference

**Alerts that trigger auto-remediation when marked "Resolved":**

| Alert | Auto-Remediation Action |
|-------|------------------------|
| Brute Force Login | Disables affected user account |
| Permission Elevation | May revert permission changes |
| Group Membership Change | May remove unauthorized membership |
| Lockbox Setting Modified | May revert lockbox configuration |

**CAUTION:** Be certain investigation is complete before marking as "Resolved" if auto-remediation will be triggered.

---

## Post-Incident Actions

### Immediate
- [ ] Document all actions taken
- [ ] Ensure threat is neutralized
- [ ] Notify affected parties if required

### Short-term (24 hours)
- [ ] Complete incident report
- [ ] Review for additional indicators of compromise
- [ ] Update alert thresholds if needed
- [ ] Conduct user awareness training if human error

### Long-term
- [ ] Review access control policies
- [ ] Implement additional security controls if gaps identified
- [ ] Update incident response procedures
- [ ] Schedule tabletop exercise if major incident

---

## Prevention and Hardening

### Security Center Configuration
- [ ] Maintain 2+ administrators in Security Notifications group
- [ ] Enable Two-Factor Authentication for all accounts
- [ ] Configure Alert Manager agent at 30-second intervals
- [ ] Review inactive users monthly (30+ days inactive)

### Access Control Best Practices
- [ ] Implement principle of least privilege
- [ ] Regular access reviews (quarterly)
- [ ] Documented approval process for elevated access
- [ ] Separate admin accounts from daily-use accounts

### Monitoring Enhancements
- [ ] Poll Audit API every 5-15 minutes for security events
- [ ] Create SIEM rules for:
  - Failed logins > 5 in 10 minutes
  - Exports > 10,000 documents
  - Mass operations > 100 documents
  - After-hours admin activity

---

## Compliance Considerations

### Audit Data Retention
- Ensure audit logs meet retention requirements
- Configure audit export schedules for compliance
- Document audit data handling procedures

### Incident Documentation
All security incidents should include:
- Timeline of events
- Affected users/data
- Root cause analysis
- Remediation actions
- Prevention measures implemented

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
