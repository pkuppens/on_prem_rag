# WBSO Architecture: Privacy-Preserving AI Agent Communication

## Document Information

| Field | Value |
|-------|-------|
| Project | WBSO-AICM-2025-01 |
| Title | AI Agent Communicatie in een data-veilige en privacy-bewuste omgeving |
| Version | 1.0 |
| Date | 2025-12-28 |
| Status | Design Complete |

## Executive Summary

This document describes the Domain-Driven Design (DDD) architecture for implementing
privacy-preserving AI agent communication in a healthcare context. The architecture
addresses four WBSO technical uncertainties (knelpunten) through dedicated bounded
contexts with clear responsibilities and interfaces.

**Core Claim**: Users can query healthcare data using natural language while:
- Maintaining GDPR compliance (AVG)
- Preventing unauthorized data access
- Ensuring audit traceability without storing PII
- Protecting data integrity from destructive operations

## 1. Technical Uncertainties (Knelpunten)

The WBSO project addresses four technical uncertainties:

| # | Knelpunt (NL) | Challenge (EN) | Bounded Context |
|---|---------------|----------------|-----------------|
| 1 | Bevoegd datatoegang | Authorized data access from natural language | Access Control |
| 2 | Cloud LLM zonder privacylek | GDPR-safe cloud LLM usage | Privacy Guard |
| 3 | Privacyvriendelijke auditlogs | Privacy-preserving audit trails | Audit Trail |
| 4 | Data-integriteit | Data integrity protection | Data Integrity |

## 2. Bounded Context Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                 │
│                           (React Frontend)                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           QUERY ORCHESTRATOR                                │
│                    (Coordinates all guardrail checks)                       │
└─────────────────────────────────────────────────────────────────────────────┘
        │              │              │              │              │
        ▼              ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────┐
│   ACCESS     │ │   PRIVACY    │ │   AUDIT      │ │   DATA       │ │  CORE   │
│   CONTROL    │ │   GUARD      │ │   TRAIL      │ │   INTEGRITY  │ │  RAG    │
│              │ │              │ │              │ │              │ │         │
│ Knelpunt 1   │ │ Knelpunt 2   │ │ Knelpunt 3   │ │ Knelpunt 4   │ │ Existing│
│ RBAC/ABAC    │ │ PII Detect   │ │ Guardrail    │ │ Intent       │ │ Pipeline│
│ Jailbreak    │ │ Anonymize    │ │ Monitoring   │ │ Classify     │ │         │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └─────────┘
        │              │              │              │              │
        └──────────────┴──────────────┴──────────────┴──────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           IDENTITY CONTEXT                                   │
│                    (Auth Service - JWT/OAuth2)                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 3. Role-Permission Model

### 3.1 Conceptual Roles

The system defines four conceptual roles with non-overlapping responsibilities:

| Role | Purpose | Data Access | System Access | Audit Access |
|------|---------|-------------|---------------|--------------|
| **GP** | Healthcare provider | All patients | No | No |
| **Patient** | Self-service | Own records only | No | No |
| **Admin** | System management | No patient data | Full | No |
| **Auditor** | Compliance | Metadata only (no PII) | No | Full |

### 3.2 Mutual Accountability Constraints

```
┌─────────────────────────────────────────────────────────────────────────┐
│ CONSTRAINTS (Separation of Concerns)                                    │
├─────────────────────────────────────────────────────────────────────────┤
│ • GP cannot disable/bypass audit logging                                │
│ • Admin cannot view patient data or audit content                       │
│ • Auditor sees action metadata but NOT PII content                      │
│ • Patient isolation: user_id filter on ALL queries                      │
│ • Audit log is append-only (no role can delete)                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Code Reference

The role-permission model is implemented in:
- `src/backend/access_control/domain/value_objects.py`

Key classes:
- `Role`: Enum of system roles
- `Permission`: Enum of atomic permissions
- `RolePermissions`: Immutable permission sets
- `DataScope`: Query-level access restrictions

## 4. PII Taxonomy

### 4.1 Classification System

PII is classified by **traceability** - whether the data can identify a specific individual:

```
┌────────────────────────────────────────────────────────────────────────┐
│ DIRECT IDENTIFIERS (Never cloud-safe)                                  │
├────────────────────────────────────────────────────────────────────────┤
│ • Name (full, partial, maiden) → [PERSOON]                             │
│ • BSN (Burgerservicenummer) → [BSN]                                    │
│ • Date of Birth (exact) → [GEBOORTEDATUM]                              │
│ • Address (street, house number) → [ADRES]                             │
│ • Phone number → [TELEFOON]                                            │
│ • Email address → [EMAIL]                                              │
│ • Patient ID / Medical record number → [PATIENTNR]                     │
├────────────────────────────────────────────────────────────────────────┤
│ QUASI-IDENTIFIERS (Cloud-safe after transformation)                    │
├────────────────────────────────────────────────────────────────────────┤
│ • Age (exact) → Decade (72 → "70+")                                    │
│ • Postal code → Region ("1234 AB" → "12xx regio")                      │
│ • Specific dates → Relative ("14 maart" → "vorige week")               │
├────────────────────────────────────────────────────────────────────────┤
│ NON-PII (Cloud-safe as-is)                                             │
├────────────────────────────────────────────────────────────────────────┤
│ • Generic medical terms ("hypertensie", "diabetes")                    │
│ • Medication classes ("ACE-remmers")                                   │
│ • Lab value ranges ("bloeddruk verhoogd")                              │
│ • Clinical questions ("wat zijn bijwerkingen van X")                   │
└────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Transformation Example

```
ORIGINAL (NOT cloud-safe):
"Dhr. de Vries, geboren 14 februari 1953, BSN 123456789,
 wonend Hoofdstraat 45, 1234 AB Amsterdam, 72 jaar oud,
 heeft klachten van pijn op de borst."

ANONYMIZED (cloud-safe):
"Mannelijke patiënt, 70+, met klachten van pijn op de borst.
 Wat zijn de differentiaaldiagnoses?"
```

### 4.3 Code Reference

The PII taxonomy is implemented in:
- `src/backend/privacy_guard/domain/value_objects.py`

Key classes:
- `PIICategory`: Enum of PII types
- `CloudSafety`: Classification (NEVER/AFTER_TRANSFORM/SAFE)
- `PIIType`: Detection rules and transformation tokens
- `AnonymizedText`: Result of anonymization

## 5. Audit System

### 5.1 Purpose

The audit system is designed for **guardrail monitoring** - proving the security
system works. It is NOT a traditional "who did what" audit log.

**Primary WBSO Claim**: "Queries to cloud do NOT contain PII"

The audit system provides **evidence** for this claim.

### 5.2 Three Audit Logs

#### 5.2.1 Cloud Query Log (Primary Evidence)

Stores the **actual anonymized query text** sent to cloud LLM for inspection.

```
┌────────────────────────────────────────────────────────────────────────┐
│ CLOUD QUERY AUDIT ENTRY                                                │
├────────────────────────────────────────────────────────────────────────┤
│ STORED (Auditor can inspect):                                          │
│ • cloud_query_text: Exact text sent to cloud                           │
│ • pii_categories_detected: What PII types were found                   │
│ • transformations_applied: What anonymization was done                 │
│ • user_role: GP/Patient (not user identity)                            │
│                                                                        │
│ NOT STORED (Privacy preserved):                                        │
│ • Original query text (only hash for correlation)                      │
│ • User identity (only role and session hash)                           │
│ • Patient identifiers (only hashes)                                    │
└────────────────────────────────────────────────────────────────────────┘
```

#### 5.2.2 Guardrail Event Log

Records every security decision for system behavior evidence:

- `guardrail_type`: ACCESS/PII/INTEGRITY/ISOLATION/JAILBREAK
- `action_taken`: ALLOWED/BLOCKED/TRANSFORMED/ESCALATED
- `reason_code`: Machine-readable reason
- `confidence_score`: Detection confidence

#### 5.2.3 Patient Isolation Log

Verifies patient queries don't return other patients' data:

- Compares `requested_scope_hashes` vs `response_scope_hashes`
- Flags `mismatch_detected` if leakage would have occurred
- All identifiers stored as hashes (auditor cannot identify patients)

### 5.3 Auditor View Example

```
┌─────────────────────────────────────────────────────────────────────────┐
│ CLOUD QUERY AUDIT LOG - Entry #1247                                     │
├─────────────────────────────────────────────────────────────────────────┤
│ Timestamp: 2025-07-15 14:32:07 | Role: GP                               │
│                                                                         │
│ QUERY SENT TO CLOUD:                                                    │
│ "Mannelijke patiënt, 70+, met klachten van pijn op de borst en          │
│  kortademigheid. Voorgeschiedenis van hypertensie. Wat zijn de          │
│  differentiaaldiagnoses en aanbevolen vervolgstappen?"                  │
│                                                                         │
│ PII HANDLING:                                                           │
│ • Detected: name (1), dob_exact (1), bsn (1), address (1)               │
│ • Transformations:                                                      │
│   - "Dhr. de Vries" → "Mannelijke patiënt"                              │
│   - "14-02-1953" → "70+"                                                │
│   - BSN removed                                                         │
│   - Address removed                                                     │
│                                                                         │
│ VERDICT: ✓ Cloud-safe (no traceable PII)                               │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.4 Code Reference

The audit system is implemented in:
- `src/backend/audit_trail/domain/entities.py`
- `src/backend/audit_trail/domain/value_objects.py`

Key classes:
- `CloudQueryAuditEntry`: Primary WBSO evidence
- `GuardrailEventEntry`: Security decision records
- `PatientIsolationAuditEntry`: Data isolation verification
- `GuardrailEffectivenessReport`: WBSO summary statistics

## 6. Local LLM Pipeline

### 6.1 Architecture

The privacy screening uses a **local LLM as an intelligent guardrail**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     LOCAL LLM GUARDRAIL PIPELINE                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  User Query                                                             │
│      │                                                                  │
│      ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ STAGE 1: Pattern-Based Pre-Filter (Fast)                       │   │
│  │ • Regex for BSN, email, phone patterns                         │   │
│  │ • Dutch name/address keyword detection                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│      │                                                                  │
│      ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ STAGE 2: Local LLM Analysis (Intelligent)                      │   │
│  │ • PII_DETECTION_PROMPT → Identify contextual PII               │   │
│  │ • Dutch healthcare context awareness                           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│      │                                                                  │
│      ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ STAGE 3: Anonymization (Deterministic)                         │   │
│  │ • ANONYMIZATION_PROMPT → Restructure query                     │   │
│  │ • Preserve medical meaning                                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│      │                                                                  │
│      ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ STAGE 4: Verification (Double-Check)                           │   │
│  │ • VERIFICATION_PROMPT → Confirm no PII remains                 │   │
│  │ • Strict: when in doubt, reject                                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│      │                                                                  │
│      ├── if APPROVED → Cloud LLM                                       │
│      └── if NEEDS_REWORK → Fallback to local LLM only                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Prompt Templates

All prompts are designed for:
- **Dutch healthcare context** (BSN, Dutch names, addresses)
- **Strict verification** (false negatives are unacceptable)
- **JSON output** for reliable parsing
- **Detailed reasoning** for audit trail

### 6.3 Code Reference

The LLM prompts are implemented in:
- `src/backend/privacy_guard/infrastructure/llm_prompts.py`

Key prompts:
- `PII_DETECTION_PROMPT`: Stage 1+2 - Find PII
- `ANONYMIZATION_PROMPT`: Stage 3 - Transform query
- `VERIFICATION_PROMPT`: Stage 4 - Double-check
- `RESPONSE_FILTER_PROMPT`: Patient isolation for responses
- `INTENT_CLASSIFICATION_PROMPT`: Read vs mutation detection
- `JAILBREAK_DETECTION_PROMPT`: Prompt injection detection

## 7. Query Processing Pipeline

### 7.1 Complete Flow

```
1. Authentication (Identity Context)
   └── Validate JWT, extract user claims, establish session

2. Access Control Check (Access Control Context)
   ├── Extract intent and scope from natural language query
   ├── Evaluate RBAC/ABAC policies
   ├── Check for jailbreak attempts
   └── Output: AccessDecision (allow/deny + DataScope)

3. Intent Classification (Data Integrity Context)
   ├── Classify as READ_ONLY or MUTATING
   ├── Assign risk level (SAFE/LOW/MEDIUM/HIGH/BLOCKED)
   └── Output: IntentClassification

4. Privacy Screening (Privacy Guard Context)
   ├── Detect PII (pattern + LLM)
   ├── Anonymize/transform PII
   ├── Verify cloud safety
   └── Output: AnonymizedText + CloudEligibility

5. RAG Processing (Core RAG Context)
   ├── If cloud eligible: Send to cloud LLM
   ├── If not: Use local LLM
   └── Output: LLM Response

6. Response Filtering (Privacy Guard Context)
   ├── For Patient role: Filter other patients' data
   └── Output: Filtered Response

7. Audit Logging (Audit Trail Context)
   ├── Log CloudQueryAuditEntry (if cloud was used)
   ├── Log GuardrailEventEntry (for each guardrail)
   ├── Log PatientIsolationAuditEntry (if Patient role)
   └── Non-blocking, async
```

### 7.2 Guardrail Decision Points

| Stage | Guardrail | Possible Actions |
|-------|-----------|------------------|
| 2 | Access Control | ALLOW / DENY (insufficient permissions) |
| 2 | Jailbreak Detection | ALLOW / BLOCK (prompt injection) |
| 3 | Intent Classification | ALLOW / CONFIRM / BLOCK (destructive) |
| 4 | PII Screening | ALLOW_CLOUD / FORCE_LOCAL / BLOCK |
| 6 | Patient Isolation | PASS / FILTER (remove other patient data) |

## 8. File Structure

```
src/backend/
├── access_control/              # Knelpunt 1: Bevoegd datatoegang
│   ├── __init__.py
│   └── domain/
│       ├── __init__.py
│       └── value_objects.py     # Role, Permission, DataScope
│
├── privacy_guard/               # Knelpunt 2: Cloud LLM zonder privacylek
│   ├── __init__.py
│   ├── domain/
│   │   ├── __init__.py
│   │   └── value_objects.py     # PIICategory, PIIType, AnonymizedText
│   └── infrastructure/
│       ├── __init__.py
│       └── llm_prompts.py       # LLM prompt templates
│
├── audit_trail/                 # Knelpunt 3: Privacyvriendelijke auditlogs
│   ├── __init__.py
│   └── domain/
│       ├── __init__.py
│       ├── entities.py          # CloudQueryAuditEntry, GuardrailEventEntry
│       └── value_objects.py     # ActorReference, ResourceReference
│
├── data_integrity/              # Knelpunt 4: Data-integriteit (planned)
│   └── (to be implemented)
│
├── query_orchestrator/          # Central coordination (planned)
│   └── (to be implemented)
│
└── [existing modules...]        # auth_service, rag_pipeline, security
```

## 9. WBSO Work Package Alignment

| Work Package | Target Date | Bounded Context | Deliverables |
|--------------|-------------|-----------------|--------------|
| WP1 | 06-2025 | Access Control | Role-permission model, jailbreak detection |
| WP2 | 07-2025 | Privacy Guard | PII detection, anonymization, cloud routing |
| WP3 | 08-2025 | Audit Trail | Cloud query log, guardrail events, reports |
| WP4 | 08-2025 | Data Integrity | Intent classification, mutation guardrails |
| WP5 | 09-2025 | Query Orchestrator | Pipeline integration, API endpoints |
| WP6 | 09-2025 | All | Integration tests, documentation |

## 10. Experimental Validation

### 10.1 WBSO Evidence Requirements

For each knelpunt, the system must demonstrate:

1. **Access Control**: Jailbreak detection accuracy (false positive/negative rates)
2. **Privacy Guard**: PII detection recall (no PII reaches cloud)
3. **Audit Trail**: Complete traceability without PII exposure
4. **Data Integrity**: Intent classification accuracy

### 10.2 Metrics Collection

The `GuardrailEffectivenessReport` provides WBSO summary statistics:

```python
{
    "cloud_pii_protection": {
        "total_queries": 1000,
        "pii_detected_count": 342,
        "pii_transformed_count": 342,
        "protection_rate": "100.0%"  # Target: 100%
    },
    "patient_isolation": {
        "total_patient_queries": 500,
        "isolation_maintained": 500,
        "breaches_prevented": 0,
        "success_rate": "100.0%"  # Target: 100%
    }
}
```

## 11. References

### 11.1 Internal Documents

- [PLANNING.md](../../WBSO-AICM-2025-01/PLANNING.md) - WBSO project plan
- [DOMAIN_DRIVEN_DESIGN.md](./DOMAIN_DRIVEN_DESIGN.md) - Existing DDD documentation
- [SECURITY.md](./SECURITY.md) - Security components

### 11.2 Code Files

- `src/backend/access_control/domain/value_objects.py` - Role-permission model
- `src/backend/privacy_guard/domain/value_objects.py` - PII taxonomy
- `src/backend/privacy_guard/infrastructure/llm_prompts.py` - LLM prompts
- `src/backend/audit_trail/domain/entities.py` - Audit log entries

### 11.3 External References

- [AVG/GDPR](https://www.autoriteitpersoonsgegevens.nl/themas/basis-avg) - Privacy regulation
- [WBSO](https://www.rvo.nl/subsidies-financiering/wbso) - R&D tax credit program
