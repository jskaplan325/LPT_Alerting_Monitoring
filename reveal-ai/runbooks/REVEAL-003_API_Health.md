# REVEAL-003: API Health Failures

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | API Health Failure |
| **Severity** | **CRITICAL** |
| **Platform** | Reveal AI |
| **Detection** | HTTP Health Check Polling |
| **Response SLA** | Immediate (15 minutes) |
| **Escalation** | On-call → Team Lead → Reveal Support |

---

## Alert Conditions

```
IF /nia/version response_code != 200 THEN CRITICAL
IF /nia/version response_time > 5 seconds THEN CRITICAL
IF /nia/version connection_timeout THEN CRITICAL
IF REST_API_v2 health_check fails THEN CRITICAL
IF consecutive_failures >= 3 THEN CRITICAL (confirmed outage)
```

### Health Check Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `http://[server]:5566/nia/version` | NIA API health | 200 OK + version info |
| `https://[instance].revealdata.com/rest/api/v2/health` | REST API health | 200 OK |
| `https://[server]/StoryEngineWebApi/api/health` | NexLP API health | 200 OK |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge immediately - this is CRITICAL
- [ ] This affects ALL platform operations
- [ ] Open P1/Sev1 incident ticket

### Step 2: Verify the Outage

**Manual Health Check:**
```bash
# Check NIA API
curl -v -m 10 "http://[server]:5566/nia/version"

# Check REST API
curl -v -m 10 "https://[instance].revealdata.com/rest/api/v2/health" \
  -H "incontrolauthtoken: {token}"
```

**Record:**
- Response Code: ________________
- Response Time: ________________
- Error Message: ________________
- Time of Alert: ________________

### Step 3: Assess Impact
- [ ] Can users access the platform?
- [ ] Are jobs running?
- [ ] What operations are affected?

---

## Investigation Procedures

### Step 4: Check Service Status

**For On-Premise Deployments:**

| Service | Check Command | Expected |
|---------|---------------|----------|
| NIA Service | `systemctl status nia` | Active (running) |
| Web Services | `systemctl status nginx/iis` | Active (running) |
| Database | `systemctl status sql/postgres` | Active (running) |
| Keycloak | `systemctl status keycloak` | Active (running) |

**For Cloud Deployments:**
- Contact Reveal Support immediately
- Check internal status communications

### Step 5: Check Server Resources

```bash
# CPU and Memory
top -b -n 1 | head -20

# Disk space
df -h

# Network connectivity
ping [database-server]
ping [other-services]
```

### Step 6: Review Logs

**NIA Logs:**
```bash
tail -100 /var/log/nia/nia.log
# or
Get-Content C:\NIA\logs\nia.log -Tail 100
```

**Look for:**
- Error messages
- Connection failures
- Out of memory errors
- Stack traces

### Step 7: Check Network Connectivity

```bash
# Test database connection
telnet [db-server] 1433

# Test internal services
curl -v http://localhost:5566/nia/version
```

---

## Resolution Procedures

### Scenario A: Service Stopped

**Symptoms:** Service not running, clean stop

**Resolution:**
1. Start the service:
   ```bash
   systemctl start nia
   # or
   net start "Reveal NIA Service"
   ```
2. Verify health endpoint responds
3. Monitor for stability

### Scenario B: Service Crashed

**Symptoms:** Service stopped unexpectedly, errors in logs

**Resolution:**
1. Review crash logs for root cause
2. Check for resource exhaustion (memory, disk)
3. Clear temporary files if disk issue
4. Restart service
5. Monitor for repeat crashes
6. If persists, **escalate to Reveal Support**

### Scenario C: Database Connectivity

**Symptoms:** Database connection errors in logs

**Resolution:**
1. Verify database server is running
2. Check network connectivity
3. Verify credentials haven't expired
4. Check connection pool settings
5. Restart service after database is confirmed healthy

### Scenario D: Resource Exhaustion

**Symptoms:** Out of memory, disk full errors

**Resolution:**
1. Identify resource constraint
2. For disk full:
   - Clear log files
   - Remove temporary files
   - Expand storage if needed
3. For memory:
   - Restart service to free memory
   - Review memory settings
   - Check for memory leaks
4. Restart services

### Scenario E: Network Issue

**Symptoms:** Connection timeouts, network errors

**Resolution:**
1. Check firewall rules
2. Verify DNS resolution
3. Check load balancer health
4. Review network path to services
5. Engage network team if needed

### Scenario F: Cloud Platform Issue

**Symptoms:** Cloud-hosted instance unreachable

**Resolution:**
1. **Immediately contact Reveal Support**
2. Check for any maintenance notifications
3. Verify your network can reach Reveal cloud
4. Document timeline and symptoms

---

## Escalation Procedures

### Immediate Escalation Required

This is a CRITICAL alert - escalate immediately if:
- Cannot identify cause within 10 minutes
- Service won't start
- Cloud deployment is down
- Multiple services affected

### Escalation Path

| Time | Action |
|------|--------|
| 0 min | On-call engineer begins investigation |
| 10 min | Escalate to Team Lead if no progress |
| 15 min | Contact Reveal Support |
| 30 min | Management notification |

### Reveal Support Escalation

**Contact:** support@revealdata.com (or support hotline)

**Request Priority:** P1/Emergency

**Provide:**
- Instance/server details
- Timeline of outage
- Error messages/logs
- Impact assessment
- Steps already attempted

---

## Post-Incident Actions

### Immediate (within 1 hour of resolution)
- [ ] Verify all services healthy
- [ ] Confirm users can access platform
- [ ] Verify jobs are processing
- [ ] Send all-clear communication

### Short-term (within 24 hours)
- [ ] Complete incident report
- [ ] Root cause analysis
- [ ] Review monitoring effectiveness
- [ ] Update alerting thresholds if needed

### Long-term
- [ ] Implement additional health checks
- [ ] Add redundancy where possible
- [ ] Review disaster recovery plan
- [ ] Schedule regular health check reviews

---

## Prevention Measures

### Monitoring Recommendations

| Check | Frequency | Alert Threshold |
|-------|-----------|-----------------|
| API Health | Every 1 minute | Any failure |
| Response Time | Every 1 minute | > 5 seconds |
| Disk Space | Every 5 minutes | < 10% free |
| Memory | Every 5 minutes | > 90% used |
| CPU | Every 5 minutes | > 95% sustained |

### Proactive Maintenance
- Regular log rotation
- Scheduled restarts during maintenance windows
- Database maintenance (index optimization)
- Certificate renewal tracking
- Capacity planning reviews

### High Availability Considerations
- Load balancer health checks
- Database failover configuration
- Service restart automation
- Backup monitoring systems

---

## API Reference

### NIA Health Check
```bash
GET http://[server]:5566/nia/version
# Expected: 200 OK
```

### REST API Health
```bash
GET https://[instance].revealdata.com/rest/api/v2/health
# Expected: 200 OK
```

### Service Status (Linux)
```bash
systemctl status nia
systemctl status nginx
```

### Service Status (Windows)
```powershell
Get-Service "Reveal*"
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
