# RUNBOOK-AIR-002: aiR for Privilege Pipeline Failures

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | aiR for Privilege Pipeline Failure |
| **Severity** | CRITICAL / HIGH |
| **Platform** | RelativityOne - aiR for Privilege |
| **Detection** | Pipeline Steps Status / Error Details |
| **Response SLA** | 15 minutes (CRITICAL), 1 hour (HIGH) |
| **Escalation** | On-call → Team Lead → Relativity Support |

## Alert Conditions

This runbook is triggered when any of the following conditions are detected:

```
IF Pipeline_Step_Status == "Run Failed" THEN CRITICAL
IF Pipeline_Step_Status == "Apply Annotations Failed" THEN HIGH
IF Project_Status == "Blocked" THEN CRITICAL
IF Error_Code == "PRP.RUN.VLD.6400" (concurrent project) THEN HIGH
IF Error_Code == "FAILED_TO_VALIDATE_*" THEN CRITICAL
IF Error_Code MATCHES "DOC.*.VLD.*" THEN HIGH
IF Pipeline_Step_Status == "Awaiting Annotations" AND Duration > 48 hours THEN WARNING
```

## aiR for Privilege Overview

aiR for Privilege uses a 6-step pipeline to analyze documents for privilege status. Understanding the pipeline is critical for troubleshooting:

### Pipeline Steps

| Step | Order | Run Action | Annotations | Typical Duration |
|------|-------|------------|-------------|------------------|
| **Prepare Project** | 1 | Yes | No | 1-5 minutes |
| **Classify Domains** | 2 | Yes | Yes | 10-20 minutes |
| **Match Equivalent Domains** | 3 | Yes | Yes | 5-10 minutes |
| **Validate Entities** | 4 | Yes | Yes | 15-30 minutes |
| **Confirm Privilege Status** | 5 | No | Yes | Manual review |
| **Populate Privilege Results** | 6 | Yes | No | 30-58 minutes |

**Key Characteristics:**
- Steps must complete in sequential order
- Prior step completion auto-triggers next step's Run action
- Average processing: ~10,700 documents per hour globally
- Single in-progress project per workspace constraint

### Brain System

| Brain | Scope | Purpose |
|-------|-------|---------|
| **Universal Brain** | Global | Public knowledge (no user data) |
| **Client Brain** | Client object | Cross-matter consistency |
| **Matter Brain** | Workspace | Links entities across projects |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge in monitoring system to prevent duplicate notifications
- [ ] Note the Project name, Workspace, and error code from the alert
- [ ] Open a tracking ticket/incident

### Step 2: Access aiR for Privilege Project

1. Log into RelativityOne
2. Navigate to the affected workspace
3. Go to **aiR for Privilege** → **Projects**
4. Open the project with the failure

### Step 3: Quick Status Assessment

**Record the following:**
- Project Name: ________________
- Workspace ID/Name: ________________
- Current Pipeline Step: ________________
- Step Status: ________________
- Error Code (if any): ________________
- Error Message: ________________
- Document Count: ________________
- Last Successful Step: ________________

---

## Investigation Procedures (5-20 minutes)

### Step 4: Identify Failed Pipeline Step

1. Open the project and navigate to **Pipeline Steps**
2. Identify which step shows "Run Failed" or "Apply Annotations Failed"
3. Check the **Error Details** field within Pipeline Steps category

**Status Meanings:**

| Status | Meaning | Action |
|--------|---------|--------|
| Not Started | Step hasn't begun | Normal for later steps |
| Running | AI analysis in progress | Wait for completion |
| Completed | Step successful | Proceed to next |
| Run Failed | AI analysis failed | **Investigate immediately** |
| Apply Annotations Failed | Save failed | **Investigate immediately** |
| Awaiting Annotations | User action needed | Notify annotators |

### Step 5: Check Error Details

1. Look for error codes in the format `XXX.XXX.VLD.XXXX`
2. Review the on-screen error message
3. Cross-reference with the Error Dictionary below

### Step 6: Review Notification Emails

If configured, check the **Notification Email Addresses** for automated error notifications sent by the system.

---

## Error Code Reference

### Document Validation Errors (DOC.*.VLD.*)

| Error Code | Message | Resolution |
|------------|---------|------------|
| `DOC.GET.VLD.6140` | Document text exceeds 170KB limit | Remove oversized documents from Saved Search |
| `DOC.GET.VLD.6600` | Documents lack Extracted Text | Remove documents without text content |
| `DOC.GET.VLD.6601` | Extracted Text Size field unpopulated | Populate field or remove documents |
| `DOC.GET.VLD.6602` | Record Type field unpopulated | Assign Record Type to all documents |
| `DOC.GET.VLD.6300` | Saved Search contains zero documents | Verify search returns documents |
| `DOC.GET.VLD.6301` | No Email Record Type documents | Include at least one email-type document |
| `DOC.GET.VLD.6130` | Document text below 0.05KB minimum | Remove undersized documents |
| `DOC.GET.VLD.6400` | Documents previously processed | Use Privilege Project field to filter |
| `DOC.GET.VLD.3120` | Too many documents in saved search | Reduce document count or split |
| `DOC.PRS.VLD.3100` | Emails lack actual email content | Update to aiR for Privilege Parsing Errors saved search |

### Project Configuration Errors (PRP.*.VLD.*)

| Error Code | Message | Resolution |
|------------|---------|------------|
| `PRP.RUN.VLD.1600` | Required settings fields incomplete | Complete General Settings (Priv) and project Settings |
| `PRP.RUN.VLD.6400` | Multiple projects running simultaneously | Complete or Abandon existing project |
| `PRP.RUN.VLD.6600` | Domains/Entities missing required fields | Complete Organization Name and person names |
| `PRP.PRS.VLD.6100` | Invalid Domain/Entity privilege status | Use approved Final Privilege Status values |

### Brain Configuration Errors (BRA.*.VLD.*)

| Error Code | Message | Resolution |
|------------|---------|------------|
| `BRA.PRS.VLD.1600` | Client Brain enabled but not selected | Select a client brain or set Use Client Brain to false |

### Known Attorneys Errors (KNA.*.VLD.*)

| Error Code | Message | Resolution |
|------------|---------|------------|
| `KNA.PRS.VLD.6600` | Known Attorneys missing Email, Name, or Role | Complete all required attorney fields |
| `KNA.PRS.VLD.6100` | Invalid date fields | Correct format; ensure Start Date precedes End Date |

### Known Law Firms Errors (KLF.*.VLD.*)

| Error Code | Message | Resolution |
|------------|---------|------------|
| `KLF.PRS.VLD.6600` | Known Law Firms incomplete | Populate Domain and Firm Name for all |

### Entity Errors (ENT.*.VLD.*, PCE.*.VLD.*)

| Error Code | Message | Resolution |
|------------|---------|------------|
| `ENT.PRS.VLD.6600` | Entity Artifact Type retrieval failed | Contact Relativity Support |
| `ENT.PRS.VLD.6601` | Legal Role entities incomplete | Populate First and Last Name |
| `PCE.PRS.VLD.6100` | Invalid Entity privilege status | Use approved Final Privilege Status values |
| `PCE.PRS.VLD.6600` | Privilege Conferring Entities incomplete | Populate First Name and Last Name |

### Domain Errors (PCD.*.VLD.*, DOM.*.VLD.*)

| Error Code | Message | Resolution |
|------------|---------|------------|
| `PCD.PRS.VLD.6100` | Invalid Final Privilege Status values | Use "Privilege Conferring", "Privilege Neutral", or "Privilege Breaking" |
| `PCD.PRS.VLD.6600` | Privilege Conferring Domains lack Organization Name | Add Organization Name to all domains |
| `DOM.PRS.VLD.6100` | Law Firm domains not annotated | Annotate all Law Firm AI predictions |

### System Errors

| Error Code | Message | Resolution |
|------------|---------|------------|
| `FAILED_TO_VALIDATE_SAVE_ACTION` | Save action validation failure | **Contact Relativity Support immediately** |
| (No code) | Services inaccessible | Retry; contact support if persistent |
| `MERGE_ENTITIES_SELECTION_VALIDATION` | Incorrect entity selection count | Select between 2 and 50 entities for merge |

### Annotation Access Errors

| Error Code | Message | Resolution |
|------------|---------|------------|
| `DOMAIN_NOT_OPEN_FOR_ANNOTATIONS` | Classify Domains step inactive | Wait for step to be ready |
| `ENTITY_NOT_OPEN_FOR_ANNOTATIONS` | Validate Entities step inactive | Wait for step to be ready |
| `EQUIVALENT_DOMAIN_NOT_OPEN_FOR_ANNOTATIONS` | Match Equivalent Domains step inactive | Wait for step to be ready |

---

## Resolution Procedures

### Scenario A: "Run Failed" Status

**Symptoms:** Pipeline step shows "Run Failed" status

**Steps:**
1. Identify the specific step that failed
2. Review Error Details field for error code
3. Reference Error Code table above for resolution

**General Resolution:**
1. Fix the underlying issue (data, configuration, etc.)
2. **Abandon the project** if unable to fix
3. Create new project with corrected configuration
4. If error persists, escalate to Relativity Support

### Scenario B: "Apply Annotations Failed" Status

**Symptoms:** Pipeline step shows "Apply Annotations Failed"

**Steps:**
1. Check for database connectivity issues
2. Verify workspace has sufficient storage
3. Check for field conflicts

**Resolution:**
1. Retry the Apply Annotations action
2. If persistent, check workspace health
3. Escalate to Relativity Support if unresolved

### Scenario C: Concurrent Project Conflict (PRP.RUN.VLD.6400)

**Symptoms:** Error indicates another project is in progress

**Steps:**
1. Navigate to **aiR for Privilege** → **Projects**
2. Identify the existing "In Progress" project
3. Determine if it should be completed or abandoned

**Resolution:**
```
IF Existing_Project is valid AND nearly complete THEN
  - Wait for completion
  - Then start new project

IF Existing_Project is stuck or invalid THEN
  - Abandon the existing project
  - Start new project
```

**To Abandon a Project:**
1. Open the in-progress project
2. Click **Abandon** action
3. Confirm abandonment
4. Create new project

### Scenario D: Document Validation Errors

**Symptoms:** Error codes matching `DOC.*.VLD.*`

**Steps:**
1. Identify the specific document issue from error code
2. Update the Saved Search to exclude problematic documents

**Common Fixes:**

| Issue | Fix |
|-------|-----|
| Text exceeds 170KB | Filter: `[Extracted Text Size] < 174080` |
| No extracted text | Filter: `[Extracted Text Size] > 0` |
| Missing Record Type | Populate Record Type field first |
| Previously processed | Filter: `[Privilege Project] IS NOT SET` |
| Zero documents | Verify search criteria returns results |

**After Fixing:**
1. Verify corrected Saved Search
2. Create new project with updated search
3. Proceed with pipeline

### Scenario E: Project Blocked

**Symptoms:** Project becomes blocked during pipeline

**Steps:**
1. Check Error Details for specific cause
2. Review if any annotations are incomplete

**Resolution:**
1. If fixable, address the blocking issue
2. If not fixable, **Abandon the blocked project**
3. Create new project with corrected configuration

**Important:** Some blocked projects cannot be unblocked and must be abandoned.

### Scenario F: Stale Annotations (>48 hours awaiting)

**Symptoms:** Step stuck in "Awaiting Annotations" for extended period

**Steps:**
1. Identify which annotators have pending work
2. Check annotation progress in the step

**Resolution:**
1. Contact annotators to complete work
2. Review if annotation workload is realistic
3. Consider splitting work across annotators

---

## Escalation Procedures

### When to Escalate to Relativity Support

| Condition | Action |
|-----------|--------|
| `FAILED_TO_VALIDATE_SAVE_ACTION` error | Immediate escalation |
| `ENT.PRS.VLD.6600` (Entity Artifact Type retrieval) | Immediate escalation |
| "Services inaccessible" persists after retry | Escalate within 30 minutes |
| Multiple projects failing with same error | Escalate within 30 minutes |
| Blocked project that cannot be abandoned | Immediate escalation |
| Pipeline hung with no error message | Escalate within 1 hour |

### Escalation Contacts

| Level | Contact | Response Time |
|-------|---------|---------------|
| Tier 1 | On-call engineer | 15 minutes |
| Tier 2 | Team Lead | 30 minutes |
| Tier 3 | Relativity Support (support@relativity.com) | Per SLA |

### Information to Gather Before Escalation

- [ ] Project Name
- [ ] Workspace ID and name
- [ ] Failed Pipeline Step
- [ ] Error Code (exact)
- [ ] Error Message (complete text)
- [ ] Document Count in Saved Search
- [ ] Saved Search name
- [ ] Screenshots of Pipeline Steps
- [ ] Screenshots of Error Details
- [ ] Brain configuration (Client Brain enabled?)
- [ ] Recent changes to Known Attorneys/Law Firms

---

## Post-Incident Actions

### Immediate (within 1 hour of resolution)
- [ ] Verify replacement project is progressing
- [ ] Confirm pipeline steps completing successfully
- [ ] Document resolution in incident ticket
- [ ] Notify affected project team

### Short-term (within 24 hours)
- [ ] Complete incident report
- [ ] Review if abandoned project affects billing
- [ ] Update Known Attorneys/Law Firms if issues found
- [ ] Verify Saved Search filters are documented

### Long-term (within 1 week)
- [ ] Analyze error patterns for prevention
- [ ] Update workspace templates with validated configurations
- [ ] Document problematic document types
- [ ] Update monitoring thresholds if needed

---

## Prevention Measures

### Pre-Project Validation
- Verify Saved Search returns expected document count
- Confirm all documents have Extracted Text and Record Type
- Check document sizes (exclude >170KB)
- Ensure no documents from prior aiR for Privilege runs

### Configuration Best Practices
- Complete all Known Attorneys with required fields
- Complete all Known Law Firms with Domain and Firm Name
- Set Final Privilege Status to valid values only
- Configure notification emails for pipeline alerts

### Capacity Planning
- Only one aiR for Privilege project per workspace at a time
- Coordinate project timing across teams
- Allow adequate time for annotation steps

### Brain Management
- If using Client Brain, ensure it's properly configured
- Review Matter Brain settings per workspace
- Document brain configuration in project notes

---

## Workflow Reference

### Roles and Responsibilities

| Role | Pipeline Steps | Responsibilities |
|------|----------------|------------------|
| **Project Manager** | 1-4 | Create searches, configure project, run pipeline |
| **Annotator** | 5 | Confirm AI predictions |
| **Case SME** | 6, 8-9 | Finalize classifications, QC decisions |

### Valid Final Privilege Status Values

Only these values are accepted:
- `Privilege Conferring`
- `Privilege Neutral`
- `Privilege Breaking`

Any other value will cause validation errors.

---

## API Reference

### Query aiR for Privilege Projects

```bash
# Query projects in workspace
curl -X POST "<host>/Relativity.REST/api/Relativity.Objects/workspace/<WORKSPACE_ID>/object/query" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -" \
  -H "Content-Type: application/json" \
  -d '{
    "request": {
      "objectType": {"Name": "aiR for Privilege Project"},
      "fields": [
        {"Name": "Name"},
        {"Name": "Status"},
        {"Name": "Current Step"},
        {"Name": "Document Count"},
        {"Name": "System Created On"},
        {"Name": "System Last Modified On"}
      ],
      "condition": "",
      "sorts": [{"FieldIdentifier": {"Name": "System Last Modified On"}, "Direction": "Descending"}]
    },
    "start": 0,
    "length": 50
  }'
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-30 | - | Initial runbook |
