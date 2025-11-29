# REVEAL-006: Authentication & Security

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Authentication Security Alert |
| **Severity** | **CRITICAL** (brute force) / **HIGH** (failed logins) |
| **Platform** | Reveal AI (Keycloak) |
| **Detection** | User Login Report / Keycloak Audit Logs |
| **Response SLA** | 15 minutes (brute force) / 1 hour (multiple failures) |
| **Escalation** | On-call → Security Team → CISO |

---

## Alert Conditions

```
IF failed_login_count_per_user > 5 in 15_minutes THEN HIGH
IF failed_login_count_per_user > 10 in 15_minutes THEN CRITICAL (brute force)
IF failed_login_count_total > 20 in 15_minutes THEN CRITICAL (credential stuffing)
IF login_from_unusual_location THEN HIGH
IF login_from_blocked_country THEN CRITICAL
IF login_after_account_termination THEN CRITICAL
IF login_outside_business_hours AND high_privilege_user THEN HIGH
```

### Authentication Risk Matrix

| Event | Risk Level | Action |
|-------|------------|--------|
| 5+ failed logins (same user) | HIGH | Alert + monitor |
| 10+ failed logins (same user) | CRITICAL | Alert + temp lock |
| 20+ failed logins (any users) | CRITICAL | Alert + investigate |
| Login from new country | HIGH | Verify with user |
| Login from blocked region | CRITICAL | Block + investigate |
| Login after termination | CRITICAL | Disable + investigate |
| Concurrent sessions limit exceeded | MEDIUM | Alert + review |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge immediately
- [ ] Brute force = CRITICAL priority
- [ ] Note username(s) and source IPs

### Step 2: Gather Information

**Record:**
- Username(s) Affected: ________________
- Source IP(s): ________________
- Failed Login Count: ________________
- Time Period: ________________
- Geographic Location: ________________
- Account Status: Active / Disabled / Terminated

### Step 3: Quick Classification

| Pattern | Classification |
|---------|---------------|
| Single user, multiple failures | Possible password issue or targeted attack |
| Multiple users, same IP | Credential stuffing attack |
| Multiple users, multiple IPs | Coordinated attack |
| Single unusual login | Verify user location |

---

## Investigation Procedures

### Step 4: Query Authentication Events

**User Login Report (Export from Reveal UI):**
1. Navigate to Admin → Reports → User Login Report
2. Set date range
3. Export to Excel
4. Filter for failed logins

**Keycloak Audit Logs (if accessible):**
```bash
# View recent authentication events
tail -500 /var/log/keycloak/audit.log | grep "LOGIN_ERROR"
```

### Step 5: Analyze Attack Pattern

**For Failed Logins:**
- Are attempts against valid usernames?
- Is the same password being tried?
- What's the source IP/range?
- Is this automated (consistent timing)?

**For Unusual Location:**
- Is user traveling?
- Is VPN/proxy being used?
- Does this match user's history?

### Step 6: Check User Account Status

**Verify account:**
```bash
curl -X GET "https://[instance].revealdata.com/rest/api/v2/users?email={email}" \
  -H "incontrolauthtoken: {token}"
```

**Check:**
- [ ] Account active?
- [ ] Employee still with company?
- [ ] Any recent password changes?
- [ ] MFA enabled?

### Step 7: IP Intelligence

**Check source IP:**
- Is it a known VPN/proxy?
- Geolocation match user's location?
- Is it on any threat lists?
- Has it been seen in other attacks?

---

## Resolution Procedures

### Scenario A: User Forgot Password

**Symptoms:** Single user, few failures, then stopped

**Actions:**
1. Verify user identity via secondary channel
2. Assist with password reset
3. Document as false positive
4. Close alert

### Scenario B: Brute Force Attack - Single Account

**Symptoms:** Many failures against one account, automated pattern

**Immediate Actions:**
1. **Temporarily lock the account**
   ```bash
   # Via Keycloak Admin or API
   curl -X PUT "https://[keycloak]/admin/realms/{realm}/users/{userId}" \
     -H "Authorization: Bearer {admin_token}" \
     -d '{"enabled": false}'
   ```
2. Block source IP at firewall if possible
3. Contact legitimate user via alternate channel
4. Preserve logs for investigation
5. Reset password when unlocking

### Scenario C: Credential Stuffing Attack

**Symptoms:** Many users, same IP/range, known credentials

**Immediate Actions:**
1. **Block attacking IP range** at firewall/WAF
2. Identify all targeted accounts
3. Force password reset for affected accounts
4. Enable MFA for affected accounts
5. Escalate to Security Team
6. Notify affected users

### Scenario D: Compromised Account

**Symptoms:** Successful login from unusual location/device

**Immediate Actions:**
1. **Immediately disable the account**
2. Terminate all active sessions
3. Contact user via phone/secondary email
4. Review recent account activity
5. Force password reset
6. Enable MFA before reactivation
7. Review data access during compromise

### Scenario E: Terminated Employee Access

**Symptoms:** Login attempt by terminated user

**Immediate Actions:**
1. **Verify account is disabled** (should be)
2. If login succeeded:
   - Disable immediately
   - Terminate sessions
   - Full security review
3. Review offboarding process
4. Escalate to HR and Security
5. Check for data exfiltration

### Scenario F: Unusual Location Login

**Symptoms:** Login from unexpected country/region

**Actions:**
1. Contact user via phone
2. Verify if user is traveling
3. Check if VPN is in use
4. If cannot verify:
   - Disable account temporarily
   - Require password reset + MFA

---

## Account Lockout Procedures

### Temporary Lock
```bash
# Lock account via Keycloak
PUT /admin/realms/{realm}/users/{userId}
{"enabled": false}
```

### Unlock After Verification
```bash
# Enable account
PUT /admin/realms/{realm}/users/{userId}
{"enabled": true}

# Require password change
PUT /admin/realms/{realm}/users/{userId}
{"requiredActions": ["UPDATE_PASSWORD"]}
```

### Force Session Termination
```bash
# Logout all sessions for user
POST /admin/realms/{realm}/users/{userId}/logout
```

---

## Escalation Procedures

### Escalation Triggers

| Condition | Escalate To |
|-----------|-------------|
| Brute force attack | Security Team |
| Successful compromise | Security Team + Management |
| Credential stuffing | Security Team + IT |
| Terminated employee access | Security + HR + Legal |
| Data accessed during compromise | Legal + Management |

### Security Team Escalation

**Contact:** [security@company.com]

**Provide:**
- Attack timeline
- Targeted accounts
- Source IPs
- Actions taken
- Potential data exposure

---

## Post-Incident Actions

### For False Positives
- [ ] Document in ticket
- [ ] Review alert thresholds
- [ ] Close alert

### For Real Attacks
- [ ] Complete security incident report
- [ ] Forensic analysis of logs
- [ ] Review all affected accounts
- [ ] Implement additional controls
- [ ] User awareness notification (if appropriate)

### For Compromises
- [ ] Full forensic investigation
- [ ] Data exposure assessment
- [ ] Notification per breach policy
- [ ] Remediation of vulnerabilities
- [ ] Post-incident review

---

## Prevention Measures

### Authentication Controls
- Implement MFA for all users
- Strong password policy
- Account lockout after failures
- Session timeout policies

### Monitoring
- Real-time failed login alerting
- Geographic login anomaly detection
- Concurrent session monitoring
- Integration with SIEM

### Keycloak Hardening
- Enable brute force protection
- Configure password policies
- Enable audit logging
- Regular security updates

### User Education
- Password hygiene training
- Phishing awareness
- Report suspicious activity

---

## API Reference

### Get Users
```bash
GET https://[instance].revealdata.com/rest/api/v2/users
```

### Keycloak User Management
```bash
# Get user
GET /admin/realms/{realm}/users/{userId}

# Disable user
PUT /admin/realms/{realm}/users/{userId}
{"enabled": false}

# Force password reset
PUT /admin/realms/{realm}/users/{userId}
{"requiredActions": ["UPDATE_PASSWORD"]}

# Logout user
POST /admin/realms/{realm}/users/{userId}/logout
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
