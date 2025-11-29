# RUNBOOK-016: RelativityOne Infrastructure Performance

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Infrastructure Performance Alerts |
| **Severity** | CRITICAL (Outage Risk) / HIGH (Degraded) / MEDIUM (Warning) |
| **Platform** | RelativityOne |
| **Detection** | Worker Monitoring + Instance Details + Performance Metrics |
| **Response SLA** | Critical: Immediate / High: 30 min / Medium: 4 hours |
| **Escalation** | On-call → Team Lead → Relativity Support |

## Alert Conditions

### SQL Performance
```
IF SQL_Read_Latency > 20ms THEN HIGH
IF SQL_Read_Latency > 8ms THEN MEDIUM (not best)
IF SQL_Write_Latency > 5ms THEN HIGH
IF SQL_Write_Latency > 3ms THEN MEDIUM
IF Page_Life_Expectancy < calculated_threshold THEN HIGH
```

### Worker Performance
```
IF Worker_Memory > 90% THEN HIGH
IF Worker_CPU > 90% sustained THEN HIGH
IF Worker_Tasks_Per_Minute < baseline * 0.5 THEN HIGH
IF Worker_Status == "Service not responding" THEN CRITICAL
```

### API Performance
```
IF API_Response_Time > 5000ms THEN HIGH
IF API_Response_Time > 2000ms THEN MEDIUM
IF API_Error_Rate > 5% THEN HIGH
IF API_Timeout_Rate > 1% THEN HIGH
```

---

## Performance Thresholds Reference

### SQL Server Performance (from Relativity documentation)

| Metric | Best | Acceptable | Warning | Critical |
|--------|------|------------|---------|----------|
| Disk Read Latency | <8ms | <20ms | 20-50ms | >50ms |
| Write Latency (Transaction Log) | <3ms | 3-5ms | 5-10ms | >10ms |
| Page Life Expectancy | See formula | -10% | -25% | -50% |

**Page Life Expectancy Formula:**
```
Expected PLE = (DataCacheSizeGB / 4GB) × 300 seconds
```

Example: 64GB data cache → Expected PLE = 4,800 seconds

### Worker Performance Thresholds

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Memory Usage | <70% | 70-90% | >90% |
| CPU Usage | <70% | 70-90% | >90% sustained |
| Tasks/Minute | Baseline | <75% baseline | <50% baseline |
| Threads in Use | Normal | High | Maxed out |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge in monitoring system
- [ ] Identify affected component(s)
- [ ] Determine user impact
- [ ] Open tracking ticket

### Step 2: Quick Status Check

**Via Instance Details:**
1. Navigate to **Instance Details** tab
2. Check **Alerts** section
3. Review **Queues** section status

**Via Worker Monitoring:**
1. Navigate to **Worker Monitoring** tab
2. Review all worker metrics:
   - Status
   - Memory
   - CPU
   - Tasks/minute

**Record the following:**
- Alert Type: ________________
- Affected Component: ________________
- Current Value: ________________
- Threshold Breached: ________________
- User Reports: ________________

---

## Investigation Procedures

### Step 3: Assess Overall System Health

**Check these areas in parallel:**

1. **Instance Details → Alerts:**
   - Disabled agents
   - Unresponsive servers
   - Queue status

2. **Worker Monitoring:**
   - Worker status (Running/Idle/Not Responding)
   - Resource utilization
   - Task throughput

3. **Queue Management:**
   - Queue depths
   - Stuck jobs
   - Processing rates

### Step 4: Identify Performance Bottleneck

**Performance Bottleneck Decision Tree:**

```
Is Worker "Service not responding"?
  YES → Escalate immediately to Relativity Support
  NO → Continue

Are multiple workers showing high resource usage?
  YES → Check for heavy concurrent operations
  NO → May be isolated issue

Is there a queue backup?
  YES → Identify blocking jobs
  NO → Check for user-facing issues

Are users reporting slowness?
  YES → Focus on their specific workflows
  NO → Monitor and document
```

### Step 5: Check for Concurrent Heavy Operations

Look for:
- Large processing jobs
- Multiple productions running
- Analytics operations
- Mass operations
- Large exports

**These operations consume significant resources and may cause temporary performance degradation.**

---

## Resolution Procedures

### Scenario A: Worker Resource Exhaustion

**Symptoms:** Memory >90%, CPU >90% sustained

**For RelativityOne (SaaS):**
1. **Do not attempt to restart workers** - Managed by Relativity
2. Document the issue
3. Identify contributing operations
4. Reduce concurrent load if possible

**Options to reduce load:**
- Pause non-critical jobs
- Lower job priorities
- Reschedule operations
- Cancel problematic jobs (with approval)

**Escalation:**
- If workers unresponsive: Escalate immediately
- If degradation persists >30 min: Escalate

### Scenario B: SQL Performance Degradation

**Symptoms:** High latency, slow queries, timeouts

**Note:** In RelativityOne, database is managed by Relativity

**Steps:**
1. Document symptoms:
   - Which operations are slow?
   - Are specific workspaces affected?
   - When did it start?

2. Check for contributing factors:
   - Large concurrent queries
   - Complex searches
   - Index rebuilding
   - Analytics operations

3. **Escalate to Relativity Support** with:
   - Specific workspace(s) affected
   - Operations experiencing issues
   - Timestamps
   - User impact

### Scenario C: API Performance Issues

**Symptoms:** Slow API responses, timeouts, errors

**For Custom Integrations:**
1. Check API rate limits (Object Manager: 1,000 req/min)
2. Review request patterns
3. Check for inefficient queries

**Optimization:**
- Implement caching
- Reduce polling frequency
- Batch requests where possible
- Use appropriate page sizes

**If Platform API:**
- Document affected endpoints
- Note error codes and messages
- Escalate to Relativity Support

### Scenario D: Queue Backup

**Symptoms:** Large queue depth, slow processing

**Steps:**
1. Identify which queue(s) affected
2. Review jobs in queue
3. Check for:
   - Stuck jobs
   - High-priority jobs waiting
   - Agent issues

**Resolution options:**
- Address stuck jobs (cancel if needed)
- Adjust priorities
- Verify agents are running
- Reduce concurrent job submission

### Scenario E: Intermittent Performance Issues

**Symptoms:** Sporadic slowness, inconsistent behavior

**Investigation:**
1. Identify timing patterns:
   - Specific times of day?
   - Correlated with specific operations?
   - Multiple users or isolated?

2. Check for:
   - Scheduled jobs coinciding
   - Peak usage periods
   - Large operations running

**Resolution:**
- Adjust scheduling to spread load
- Identify and optimize heavy operations
- Plan capacity for peak periods

---

## Performance Monitoring Setup

### Key Metrics to Monitor

| Category | Metric | Source | Poll Frequency |
|----------|--------|--------|----------------|
| Workers | Status, Memory, CPU | Worker Monitoring | 1 min |
| Queues | Depth, Stuck Jobs | Queue Management | 5 min |
| API | Response Time, Error Rate | Custom monitoring | 1 min |
| Jobs | Duration, Success Rate | Audit/Job APIs | 5 min |

### Baseline Establishment

1. **Collect baseline during normal operations:**
   - Worker utilization patterns
   - Queue depths
   - Job durations
   - Peak usage times

2. **Set thresholds based on baseline:**
   - Warning: +25% above baseline
   - High: +50% above baseline
   - Critical: +100% above baseline or service impact

---

## Capacity Planning

### Proactive Capacity Management

**Before Large Projects:**
1. Notify Relativity via "Incoming Project Details: RelativityOne" form
2. Provide details on:
   - Expected document volume
   - Processing requirements
   - Timeline
   - Special requirements

**This ensures adequate capacity for:**
- Imaging
- OCR
- Branding
- Productions

### Resource Pool Considerations

- Workspaces are assigned to resource pools
- Pool capacity affects performance
- Large projects may need dedicated resources
- Coordinate with Relativity for capacity

---

## Escalation Procedures

### When to Escalate

| Condition | Level | Timeframe |
|-----------|-------|-----------|
| Worker "Service not responding" | Relativity Support | Immediate |
| Database errors/timeouts | Relativity Support | 15 min |
| Widespread user impact | Team Lead + Support | Immediate |
| Degradation >30 min | Team Lead | 30 min |
| Capacity concerns | Account Team | Planning |

### Information for Escalation

- [ ] Affected components
- [ ] Performance metrics observed
- [ ] User impact description
- [ ] Timeline of issue
- [ ] Operations running during issue
- [ ] Screenshots of monitoring dashboards
- [ ] Error messages if any

---

## Post-Incident Actions

### Immediate
- [ ] Verify performance restored
- [ ] Confirm user experience normalized
- [ ] Document resolution

### Short-term (24-48 hours)
- [ ] Complete incident report
- [ ] Root cause analysis
- [ ] Review contributing factors

### Long-term
- [ ] Update baseline metrics
- [ ] Adjust monitoring thresholds
- [ ] Implement preventive measures
- [ ] Capacity planning review

---

## Prevention Measures

### Operational Best Practices
- Schedule heavy operations during off-peak
- Stagger large jobs across time
- Monitor before and during large operations
- Maintain communication with users

### Monitoring Enhancements
- Establish clear baselines
- Implement proactive alerting
- Regular performance reviews
- Track trends over time

### Capacity Management
- Quarterly capacity reviews
- Pre-project capacity planning
- Communicate with Relativity proactively
- Plan for growth

---

## Reference: Infrastructure Planning Considerations

### SQL Server Metrics Interpretation

**Disk Read Latency:**
- <8ms: Excellent
- 8-20ms: Acceptable
- >20ms: Investigation needed

**Write Latency (Transaction Logs):**
- <3ms: Excellent
- 3-5ms: Acceptable
- >5ms: Investigation needed

**Page Life Expectancy:**
Calculate expected value and compare to actual:
```
Expected = (DataCacheSizeGB / 4) × 300
Alert if actual < Expected × 0.75
```

---

## API Rate Limits Reference

| API | Limit | Notes |
|-----|-------|-------|
| Object Manager | 1,000 req/min per web server | Include X-Kepler-Referrer header |
| Processing | Standard | Check documentation |
| Production | Standard | Check documentation |
| Audit | Standard | Check documentation |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
