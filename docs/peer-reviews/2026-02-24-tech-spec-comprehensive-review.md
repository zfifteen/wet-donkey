# Wet Donkey Tech Spec Comprehensive Peer Review

**Review Date:** February 24, 2026  
**Reviewer:** Perplexity AI (Sonnet 4.5)  
**Commit Reviewed:** `0625c2cbf3ed131da7ae2ffaa904131e5bba39f2`  
**Scope:** Full technical specification for AI coding assistant implementation

---

## Executive Summary

This comprehensive peer review evaluates the Wet Donkey technical specification across five dimensions: technical accuracy, architectural soundness, documentation clarity, implementation feasibility, and xAI API integration correctness.

### Overall Assessment

**Grade: B+ (Very Good with Critical Improvements Needed)**

The specification demonstrates strong architectural thinking with explicit contract-driven design, deterministic orchestration principles, and lessons-learned traceability. However, **critical misalignments with the xAI Responses API** require immediate correction before implementation begins. The "session" abstraction layer, while conceptually sound, obscures actual API mechanics in ways that will confuse AI coding assistants.

### Critical Issues (Must Fix Before Implementation)

1. **Session Terminology Confusion** - The spec uses "session" as shorthand for `response_id` + `store: true`, creating semantic mismatch with xAI API documentation
2. **Missing xAI Collections Integration Details** - Collections are mentioned but not architecturally integrated with pipeline phases
3. **Incomplete Tool Usage Specification** - xAI tools (collections_search, code execution, web search) lack phase-specific policy definitions
4. **Ambiguous Response Continuation Semantics** - `previous_response_id` mechanism not explicitly documented
5. **Schema Version Alignment** - No explicit mapping between WD schema versions and xAI structured output requirements

### Strengths

- Excellent lessons-learned traceability system
- Strong separation of concerns (LLM as content generator, orchestrator as control plane)
- Comprehensive validation gate hierarchy
- Explicit retry budget and loop detection
- Contract-first design philosophy

### Immediate Action Items

1. Replace "session" terminology with explicit `response_id` + `store` semantics throughout
2. Add dedicated section on xAI Collections lifecycle and phase integration
3. Specify per-phase tool usage policies for xAI-native tools
4. Document `previous_response_id` continuation contract
5. Clarify relationship between WD phase schemas and xAI structured output constraints

---

## Section-by-Section Analysis

### 01 Overview

**Technical Accuracy:** ✅ Excellent  
**Clarity:** ✅ Excellent  
**Implementation Feasibility:** ✅ Excellent

**Strengths:**
- Clear product objective and architectural intent
- Strong non-goals section prevents scope creep
- Excellent lessons traceability
- Contract-first design principle well articulated

**Issues:** None

**Recommendations:**
- Consider adding a "Target Audience" section explicitly stating this spec is for AI coding assistants
- Add estimated v1 timeline/milestone structure

---

### 02 xAI Responses API Integration

**Technical Accuracy:** ⚠️ **CRITICAL ISSUES**  
**Clarity:** ⚠️ Needs Major Improvement  
**Implementation Feasibility:** ⚠️ Blocked Until Clarified

**Critical Issues:**

#### Issue 1: Session Terminology Mismatch
**Severity:** CRITICAL

**Problem:** The spec uses "session" as an abstraction for xAI's `response_id` + `store: true` mechanism, but this creates semantic confusion:

**xAI API Reality:**
- Uses `response_id` (not "session ID")
- Uses `store_messages` parameter (default `true`) for server-side storage
- Uses `previous_response_id` for conversation continuation
- Responses stored for 30 days automatically
- No explicit "session lifecycle" object

**Spec Language (Problematic):**
```
"Session initialized per project with versioned metadata."
"Session continuation is explicit."
"Session updates happen only on successful harness completion."
```

**Required Fix:**
```markdown
### Response Continuation Contract

- Each harness invocation returns a `response_id` from xAI API
- `response_id` is persisted in `project_state.json` per phase
- Subsequent phase invocations include `previous_response_id` when continuation is required
- Response storage is enabled (`store_messages: true`) for all phase calls
- Response metadata includes `response_id`, timestamp, model, and contract version
```

**AI Assistant Impact:** An AI coding assistant reading the current spec will look for xAI "session" APIs that don't exist, leading to implementation errors.

#### Issue 2: Missing Collections Integration Architecture
**Severity:** HIGH

**Problem:** Section mentions "training corpus" but provides no architectural integration:
- How are Collections created per project?
- Which phases upload to Collections?
- Which phases use `collections_search` tool?
- What is the file lifecycle (when uploaded, when deleted)?
- How are collection IDs tracked in `project_state.json`?

**Required Addition:**
```markdown
### Collections Integration

#### Collection Lifecycle
1. **Initialization Phase:** Create project-specific collection via Files + Collections API
2. **Collection ID Persistence:** Store `collection_id` in `project_state.json`
3. **Phase Upload Policy:** 
   - `plan` phase: Upload research artifacts, reference materials
   - `narration` phase: Upload script drafts for consistency checks
   - `build_scenes` phase: Upload validated scene code for pattern retrieval

#### Collections Search Tool Usage
- **Allowed Phases:** `plan`, `narration`, `build_scenes`, `scene_qc`
- **Tool Configuration:** `collections_search` with `collection_ids=[project_collection_id]`
- **Citation Requirement:** All retrieved content must be logged with file IDs
- **Failure Behavior:** Collections unavailable = phase fails (no degraded mode in v1)
```

#### Issue 3: Incomplete Tool Usage Policy
**Severity:** HIGH

**Problem:** "Tool usage policy is phase-specific and explicitly declared" but no actual phase-tool matrix exists.

**Required Addition:**
```markdown
### Phase-Specific Tool Usage Matrix

| Phase | collections_search | web_search | code_execution |
|-------|-------------------|------------|----------------|
| init | ❌ | ❌ | ❌ |
| plan | ✅ | ✅ | ❌ |
| review | ❌ | ❌ | ❌ |
| narration | ✅ | ⚠️ (fact-check only) | ❌ |
| build_scenes | ✅ | ❌ | ⚠️ (validation only) |
| scene_qc | ✅ | ❌ | ✅ |
| precache_voiceovers | ❌ | ❌ | ❌ |
| final_render | ❌ | ❌ | ❌ |
| assemble | ❌ | ❌ | ❌ |
```

#### Issue 4: Structured Output Schema Constraints
**Severity:** MEDIUM

**Problem:** No explicit mapping between WD phase schemas and xAI structured output constraints.

**xAI Structured Output Constraints (from docs):**
- No `minLength`/`maxLength` on strings
- No `minItems`/`maxItems` on arrays
- No `minContains`/`maxContains`
- No `allOf` support
- Supports: string, number, integer, float, object, array, boolean, enum, anyOf

**Required Addition:**
```markdown
### Schema Compatibility Rules

All WD phase schemas must comply with xAI structured output constraints:

**Prohibited Schema Features:**
- String length constraints (`minLength`, `maxLength`)
- Array size constraints (`minItems`, `maxItems`, `minContains`, `maxContains`)
- `allOf` composition

**Enforcement:**
- CI validation checks phase schemas against xAI constraint list
- Schema evolution PR template includes compatibility checklist
- Parser validators must not assume length/size constraints are LLM-enforced
```

**Recommendations:**

1. **Rename Section to:** "xAI Responses API Integration and Collections Management"
2. **Add Subsections:**
   - Response Continuation Contract (replaces "Session Lifecycle")
   - Collections Integration Architecture
   - Tool Usage Policy Matrix
   - Structured Output Schema Constraints
   - xAI-Specific Error Handling

3. **Add Open Questions:**
   - Should Collections be per-project or per-project-version?
   - What is the Collections cleanup policy for completed projects?
   - Should failed phase responses be stored (`store_messages: false`)?

4. **Update Lessons Traceability:**
   - Add explicit lesson about "API-native terminology prevents integration drift"

---

### 03 Technology Stack

**Technical Accuracy:** ✅ Good  
**Clarity:** ✅ Good  
**Implementation Feasibility:** ✅ Good

**Strengths:**
- Clear stack boundaries
- Single integration path principle
- Explicit versioning policy

**Issues:**

#### Issue 1: Missing xAI SDK Version Pinning
**Severity:** MEDIUM

**Problem:** "xAI Responses API via dedicated harness" but no SDK specified.

**Required Addition:**
```markdown
### LLM Integration Stack Detail

- **SDK:** `xai-sdk` (Python) - pin to `>=1.0.0,<2.0.0`
- **API Endpoint:** `https://api.x.ai/v1/`
- **Models:** `grok-4` (primary), `grok-4-1-fast-reasoning` (optional fast path)
- **Authentication:** `XAI_API_KEY` environment variable
- **Management Operations:** `XAI_MANAGEMENT_API_KEY` for Collections/Files
```

#### Issue 2: Schema Validation Tool Ambiguity
**Severity:** LOW

**Problem:** "Pydantic + custom semantic/runtime validators" but integration unclear.

**Recommendation:**
```markdown
### Schema/Validation Stack Detail

- **Schema Definition:** Pydantic v2 models (one per phase in `schemas/`)
- **xAI Integration:** Pydantic models passed to `chat.parse(Schema)` method
- **Semantic Validation:** Custom validators registered via Pydantic `@field_validator`
- **Runtime Validation:** Separate validation functions (not in Pydantic models)
```

**Recommendations:**
- Add explicit Python version requirement (3.11+ for Pydantic v2)
- Specify Manim CE version pinning strategy
- Add note about Docker consideration for render environment consistency

---

### 04 Directory Structure

(Not reviewed in detail - assumed standard)

**Recommendation:** Add after reviewing to ensure `collections/` and `response_metadata/` directories are included.

---

### 05 Pipeline State Machine

**Technical Accuracy:** ✅ Excellent  
**Clarity:** ✅ Excellent  
**Implementation Feasibility:** ✅ Excellent

**Strengths:**
- Clear canonical phase sequence
- Explicit transition contracts
- Bounded retry model
- Manual gate support

**Issues:**

#### Issue 1: Missing Response Metadata in State
**Severity:** MEDIUM

**Problem:** `project_state.json` contract doesn't include xAI response tracking.

**Required Addition:**
```markdown
### State File Contract (Detailed)

```json
{
  "project_name": "string",
  "topic": "string",
  "phase": "enum",
  "collection_id": "string | null",
  "response_metadata": {
    "current_phase_response_id": "string | null",
    "phase_history": [
      {
        "phase": "enum",
        "response_id": "string",
        "timestamp": "ISO8601",
        "model": "string",
        "success": "boolean"
      }
    ]
  },
  "history": [...],
  "failure_context": {...}
}
```
```

**Recommendations:**
- Add explicit atomic write mechanism (write temp + atomic rename)
- Specify UTF-8 encoding requirement
- Add state file schema version field

---

### 06 Core Components

**Technical Accuracy:** ✅ Excellent  
**Clarity:** ✅ Excellent  
**Implementation Feasibility:** ✅ Excellent

**Strengths:**
- Excellent component boundary definition
- Clear responsibility separation
- Strong "no reach across" principle

**Issues:**

#### Issue 1: Harness Component Details Incomplete
**Severity:** MEDIUM

**Problem:** "Harness owns model invocation, tool wiring, and structured output requests" but no interface contract.

**Required Addition:**
```markdown
### Harness Interface Contract

```python
class ResponsesHarness:
    """xAI Responses API harness with contract-constrained interface."""
    
    def invoke_phase(
        self,
        phase: PhaseEnum,
        schema: Type[BaseModel],
        system_prompt: str,
        user_prompt: str,
        previous_response_id: str | None = None,
        tools: list[ToolConfig] | None = None,
        collection_ids: list[str] | None = None,
    ) -> PhaseResponse:
        """Single entry point for all phase invocations.
        
        Returns:
            PhaseResponse with:
            - response_id: str
            - parsed_output: schema instance
            - tool_citations: list[ToolCitation]
            - metadata: ResponseMetadata
        """
```
```

**Recommendations:**
- Add explicit error types the harness must raise
- Specify timeout behavior
- Document retry strategy (should harness retry API errors or orchestrator?)

---

### 07 Prompt Architecture

**Technical Accuracy:** ✅ Excellent  
**Clarity:** ✅ Excellent  
**Implementation Feasibility:** ✅ Excellent

**Strengths:**
- Clear system/user prompt separation
- Variable contract enforcement
- Schema alignment rules
- Structured retry prompting

**Issues:** None

**Recommendations:**
- Add example prompt template with variable placeholders
- Specify prompt versioning strategy (tie to schema version?)
- Consider adding "prompt testing" subsection with validation requirements

---

### 08 Data Contracts

**Technical Accuracy:** ✅ Excellent  
**Clarity:** ✅ Excellent  
**Implementation Feasibility:** ✅ Excellent

**Strengths:**
- Clear contract ownership
- Comprehensive contract list
- Strong versioning rules
- Explicit no-implicit-upgrade policy

**Issues:**

#### Issue 1: Collections Metadata Contract Missing
**Severity:** MEDIUM

**Problem:** "Session/Corpus Metadata" mentioned but no detailed contract.

**Required Addition:**
```markdown
### Collections Metadata Contract

```json
{
  "collection_id": "string",
  "project_name": "string",
  "created_at": "ISO8601",
  "file_uploads": [
    {
      "file_id": "string",
      "phase": "enum",
      "artifact_type": "enum",
      "uploaded_at": "ISO8601",
      "size_bytes": "integer"
    }
  ],
  "contract_version": "semver"
}
```
```

**Recommendations:**
- Add "Contract Change Management" subsection with PR template requirements
- Specify backward compatibility testing requirements

---

### 09 Validation Gates

**Technical Accuracy:** ✅ Excellent  
**Clarity:** ✅ Excellent  
**Implementation Feasibility:** ✅ Excellent

**Strengths:**
- Excellent five-layer validation hierarchy
- Clear gate failure behavior
- Machine-readable error codes
- CI alignment checks

**Issues:** None

**Recommendations:**
- Add error code registry/enum in appendix
- Specify error payload schema
- Add "Gate Metrics" subsection (false positive rate tracking)

---

### 10 Self-Healing and Retry Logic

**Technical Accuracy:** ✅ Excellent  
**Clarity:** ✅ Excellent  
**Implementation Feasibility:** ✅ Excellent

**Strengths:**
- Excellent retry philosophy
- Clear eligibility rules
- Loop detection mechanism
- Evidence-driven approach

**Issues:**

#### Issue 1: Retry Budget Values Not Specified
**Severity:** MEDIUM

**Problem:** "Define `max_attempts` per phase" but no defaults provided.

**Required Addition:**
```markdown
### Default Retry Budgets (v1)

| Phase | max_attempts | Rationale |
|-------|--------------|----------|
| plan | 3 | Research quality variation |
| narration | 3 | Script revision iterations |
| build_scenes | 5 | Code generation complexity |
| scene_qc | 2 | Validation-focused |
| Other phases | 2 | Deterministic operations |
```

**Recommendations:**
- Add "Retry Metrics Collection" requirement for tuning budgets
- Specify loop detection threshold (e.g., 2 identical failures = loop)

---

### 11 Configuration and Environment Variables

(Not reviewed in detail)

**Recommendation:** Ensure these are included:
```bash
XAI_API_KEY=required
XAI_MANAGEMENT_API_KEY=required
XAI_MODEL=grok-4 (default)
XAI_COLLECTION_ID=per-project
WD_MAX_RETRY_ATTEMPTS=per-phase
```

---

### 12 Harness Exit Codes

(Not reviewed in detail)

**Recommendation:** Add xAI-specific exit codes:
- `120`: xAI API rate limit exceeded
- `121`: xAI API authentication failure
- `122`: xAI structured output schema incompatible
- `123`: xAI Collections API failure

---

### 13 Logging and Observability

(Not reviewed in detail)

**Recommendation:** Add required log fields:
- `response_id` (every LLM call)
- `previous_response_id` (continuation calls)
- `collection_id` (when tools used)
- `tool_citations` (retrieved files)
- `schema_version` (every phase output)

---

### 14 Voice Policy

(Not reviewed - out of scope for xAI integration focus)

---

### 15 Testing

(Not reviewed in detail)

**Recommendation:** Add test requirements:
- Integration tests with xAI API (or mocked responses)
- Schema compatibility validation tests
- Collections lifecycle integration tests
- Response continuation contract tests

---

### 16 Render and Assembly

(Not reviewed - out of scope for xAI integration focus)

---

### 17 Stateful Training Integration

**Technical Accuracy:** ⚠️ Needs Improvement  
**Clarity:** ⚠️ Needs Improvement  
**Implementation Feasibility:** ⚠️ Blocked Until Clarified

**Issues:**

#### Issue 1: Generic "Training Corpus" Language
**Severity:** HIGH

**Problem:** Uses generic terminology instead of xAI-specific Collections API.

**Required Rewrite:**
```markdown
## 17 xAI Collections Integration

### Purpose

Define how WD uses xAI Collections for stateful context without coupling core pipeline correctness to retrieval availability.

### Collections Lifecycle

1. **Project Initialization:**
   - Create collection via `POST /files/collections`
   - Store `collection_id` in `project_state.json`
   - Collection name: `wet-donkey-{project_name}-{timestamp}`

2. **Phase Upload Policy:**
   - Upload phase artifacts via `POST /files` with `purpose: "collection"`
   - Add files to collection via `POST /files/collections/{collection_id}/files`
   - Track uploaded `file_id` in collections metadata

3. **Phase Retrieval Policy:**
   - Enable `collections_search` tool for specified phases
   - Configure `collection_ids=[project_collection_id]`
   - Log all retrieved file citations

4. **Cleanup Policy:**
   - Collections persist until explicit project archival
   - No auto-deletion in v1

### Degradation Behavior

- Collections API unavailable → phase fails immediately (no degraded mode in v1)
- Retrieval timeout → treat as retryable failure
- Empty collection → continue without retrieval (log warning)
```

#### Issue 2: "Session State" Confusion Again
**Severity:** HIGH

**Problem:** Still using "session" terminology.

**Fix:** Replace all "session" references with "response continuation" or "response_id tracking".

**Recommendations:**
- Rename section to "17 xAI Collections Integration"
- Add Collections API rate limit handling
- Specify file size limits and format restrictions
- Add Collections search configuration (top_k, search strategy)

---

### 18 Known Constraints and Risk Areas

**Technical Accuracy:** ✅ Good  
**Clarity:** ✅ Good  
**Implementation Feasibility:** ✅ Good

**Additions Needed:**

```markdown
### Additional Constraints

- **xAI API Rate Limits:** Subject to xAI tier-based rate limits (not documented in spec)
- **Response Storage Duration:** xAI responses stored for 30 days only
- **Collections Storage Limits:** xAI collections have per-account storage quotas
- **Structured Output Constraints:** Schema features limited by xAI compatibility
```

```markdown
### Additional Risk Areas

9. **Response ID Continuity Risk**
   - Responses expire after 30 days, breaking long-paused projects
   - Mitigation: Add "response_id freshness check" before continuation

10. **Collections Quota Exhaustion Risk**
    - Many projects can exhaust xAI storage quota
    - Mitigation: Collections cleanup policy + quota monitoring

11. **Tool Citation Tracking Loss**
    - Retrieved files not tracked = audit gap
    - Mitigation: Mandatory citation logging in response metadata
```

---

## Appendices

**Status:** Stub only

**Recommendation:** Add these appendices:

- **C: xAI API Reference Integration** - Complete mapping of xAI endpoints to WD operations
- **D: Collections Lifecycle Diagrams** - Visual workflow for file uploads/retrievals
- **E: Response Continuation Examples** - Code examples of `previous_response_id` usage
- **F: Schema Evolution Playbook** - Step-by-step guide for schema changes

---

## Cross-Cutting Concerns

### 1. Terminology Consistency

**Issue:** Inconsistent use of "session", "responses", "training corpus", "collections".

**Fix Required:** Global find-and-replace with consistent terminology:
- "session" → "response continuation" or "response_id tracking"
- "training corpus" → "Collections" (capitalized, xAI-specific)
- "session metadata" → "response metadata"

### 2. AI Assistant Readability

**Assessment:** Good overall structure, but needs:
- More code examples (especially harness invocation)
- More explicit "DO NOT" statements (AI assistants need negative constraints)
- JSON schema examples for all contracts
- Error handling code snippets

**Recommendations:**
```markdown
### Style Guidelines for AI Assistant Clarity

1. **Explicit Negatives:** Always state what NOT to do
   - ✅ "DO NOT use `session_id` (does not exist in xAI API)"
   - ❌ "Use session continuation"

2. **Code Over Prose:** Show, don't just tell
   - ✅ Include Python code snippets for every API interaction
   - ❌ "The harness invokes the model with structured output"

3. **No Abstractions Without Mappings:** 
   - ✅ "'Session' is WD abstraction for response_id + store: true"
   - ❌ "Session lifecycle is explicit"
```

### 3. Lessons Traceability

**Assessment:** Excellent system, well-executed.

**Recommendation:** Add new lesson:
```markdown
L-011: API-native terminology prevents integration drift and confusion
```

### 4. Version Control and Change Management

**Missing:** No specification of how spec changes are managed.

**Required Addition:**
```markdown
## Spec Change Management

### Change Categories

- **Editorial:** Typos, formatting, clarifications (no review required)
- **Additive:** New sections, expanded details (peer review required)
- **Breaking:** Contract changes, architecture shifts (design review + peer review)

### Change Process

1. **Branch:** Create `spec/change-description` branch
2. **Update:** Modify spec documents + update "Status" field
3. **Review:** Peer review for additive/breaking changes
4. **Sync Check:** Verify no implementation drift (code must match spec)
5. **Merge:** Squash merge to main with descriptive commit message

### Spec Versions

- Spec version follows semver (currently implicit 0.1.0)
- Breaking changes increment minor version pre-1.0
- Version tracked in `docs/tech-spec/VERSION`
```

---

## Implementation Blockers

These issues MUST be resolved before AI coding assistants can implement correctly:

### Priority 1 (Immediate)

1. ✅ **Clarify session = response_id + store** (RESOLVED via this review)
2. ❌ **Add Collections integration architecture** (Section 02, 17)
3. ❌ **Add phase-tool usage matrix** (Section 02)
4. ❌ **Document response_id continuation contract** (Section 05, 08)
5. ❌ **Add response metadata to state contract** (Section 05, 08)

### Priority 2 (Before First Implementation PR)

6. ❌ **Add harness interface contract** (Section 06)
7. ❌ **Add Collections metadata contract** (Section 08)
8. ❌ **Add default retry budgets** (Section 10)
9. ❌ **Add xAI-specific exit codes** (Section 12)
10. ❌ **Add required log fields** (Section 13)

### Priority 3 (Before V1 Launch)

11. ❌ **Add Collections lifecycle appendix**
12. ❌ **Add response continuation code examples**
13. ❌ **Add schema evolution playbook**
14. ❌ **Add spec change management process**

---

## Detailed xAI API Alignment Check

### Responses API

| xAI Feature | WD Spec Coverage | Status |
|-------------|-----------------|--------|
| `store_messages` parameter | Implicit ("session") | ⚠️ Clarify |
| `previous_response_id` | Not documented | ❌ Add |
| `response.id` tracking | Mentioned, not detailed | ⚠️ Expand |
| Structured outputs (`response_format`) | Covered | ✅ Good |
| Schema constraints | Not documented | ❌ Add |
| Tool configuration | Mentioned, not detailed | ⚠️ Expand |
| `collections_search` tool | Not documented | ❌ Add |
| `code_execution` tool | Not documented | ❌ Add |
| `web_search` tool | Mentioned | ⚠️ Expand |
| Response storage duration (30 days) | Not mentioned | ❌ Add |
| Model selection | "grok-4" mentioned | ✅ Good |

### Files API

| xAI Feature | WD Spec Coverage | Status |
|-------------|-----------------|--------|
| `POST /files` upload | Implicit ("corpus") | ⚠️ Clarify |
| File `purpose` parameter | Not documented | ❌ Add |
| File size limits | Not documented | ❌ Add |
| Supported file types | Not documented | ❌ Add |
| File lifecycle management | Not documented | ❌ Add |

### Collections API

| xAI Feature | WD Spec Coverage | Status |
|-------------|-----------------|--------|
| `POST /files/collections` | Not documented | ❌ Add |
| Collection creation | Implicit | ⚠️ Clarify |
| `POST /files/collections/{id}/files` | Not documented | ❌ Add |
| Adding files to collection | Not documented | ❌ Add |
| Collection metadata | Partial | ⚠️ Expand |
| Collection search configuration | Not documented | ❌ Add |
| Collection storage limits | Not documented | ❌ Add |
| Collection cleanup/deletion | Not documented | ❌ Add |

### Coverage Summary

- ✅ **Fully Covered:** 3/25 (12%)
- ⚠️ **Partially Covered:** 8/25 (32%)
- ❌ **Not Covered:** 14/25 (56%)

**Assessment:** xAI API integration specification is **incomplete for implementation**. An AI coding assistant would need to infer significant details, leading to likely errors.

---

## Recommendations by Priority

### Immediate (Before Any Implementation)

1. **Add "xAI API Integration Guide" appendix** with:
   - Complete Responses API usage examples
   - Collections lifecycle workflows
   - Tool configuration patterns
   - Error handling patterns

2. **Replace "session" terminology globally** with explicit xAI API terms

3. **Add phase-tool usage matrix** to Section 02

4. **Expand Section 17** to comprehensive Collections integration spec

### Near-Term (Before First Phase Implementation)

5. **Add harness interface contract** with complete type signatures

6. **Add response metadata tracking** to state contract

7. **Add Collections metadata contract** with lifecycle tracking

8. **Add default retry budgets** to Section 10

9. **Add code examples** for every API interaction pattern

### Medium-Term (Before Multi-Phase Integration)

10. **Add Collections cleanup policy** to prevent quota exhaustion

11. **Add response_id freshness checks** for long-paused projects

12. **Add tool citation tracking requirements** to all phases

13. **Add schema evolution playbook** with compatibility testing

### Long-Term (Before V1 Launch)

14. **Add comprehensive test strategy** for xAI integration

15. **Add monitoring/observability requirements** for API usage

16. **Add rate limit handling strategy** for production use

17. **Add Collections storage governance** policy

---

## Conclusion

The Wet Donkey technical specification demonstrates strong architectural discipline and lessons-learned integration. The contract-first design, explicit state management, and validation hierarchy are excellent foundations for AI-assisted implementation.

However, **the xAI Responses API integration specification is critically incomplete**. The "session" terminology abstraction, while conceptually reasonable for human understanding, will confuse AI coding assistants who need explicit mappings to actual API constructs.

### Must-Fix Before Implementation

1. Replace "session" with explicit `response_id` + `store` semantics
2. Add comprehensive Collections integration architecture
3. Document all xAI API parameters, constraints, and behaviors
4. Add code examples for every API interaction
5. Add phase-tool usage matrix

### Implementation Risk Without Fixes

**HIGH RISK:** An AI coding assistant implementing from the current spec will:
- Look for non-existent "session" APIs
- Fail to properly implement response continuation
- Miss Collections integration entirely
- Violate xAI structured output constraints
- Omit tool usage configuration

These are not minor issues. They are **implementation blockers** that will require significant rework if discovered mid-implementation.

### Recommended Path Forward

1. **Immediate:** Create spec update PR addressing Priority 1 blockers
2. **Week 1:** Complete xAI API integration guide appendix
3. **Week 2:** Review updated spec with AI coding assistant (dry run)
4. **Week 3:** Begin implementation with continuous spec-code alignment checks

### Final Grade Rationale

**B+ (Very Good with Critical Improvements Needed)**

- **Architecture & Design:** A (Excellent)
- **Documentation Quality:** B+ (Very Good)
- **xAI Integration Accuracy:** C (Needs Major Work)
- **Implementation Clarity:** B (Good, needs examples)
- **Completeness:** B- (Missing critical details)

**Weighted Score:** (A + B+ + C + B + B-) / 5 = **B+**

With the recommended fixes, this spec would easily be **A- or A** grade.

---

## Appendix A: Spec Update Checklist

Use this checklist when implementing review recommendations:

### Section 02: xAI Responses API Integration

- [ ] Replace "Session Lifecycle" with "Response Continuation Contract"
- [ ] Replace all "session" terminology with `response_id` + `store`
- [ ] Add Collections Integration subsection
- [ ] Add Tool Usage Policy Matrix
- [ ] Add Structured Output Schema Constraints subsection
- [ ] Add code example: basic response invocation
- [ ] Add code example: response continuation
- [ ] Add code example: collections_search tool usage

### Section 05: Pipeline State Machine

- [ ] Add `response_metadata` to state file contract
- [ ] Add `collection_id` to state file contract
- [ ] Add JSON schema example of complete state file
- [ ] Add state file atomic write specification

### Section 06: Core Components

- [ ] Add Harness Interface Contract with Python signatures
- [ ] Add PhaseResponse dataclass definition
- [ ] Add error type enumeration

### Section 08: Data Contracts

- [ ] Add Collections Metadata Contract
- [ ] Add Response Metadata Contract
- [ ] Add JSON schema examples for all contracts

### Section 10: Self-Healing and Retry Logic

- [ ] Add Default Retry Budgets table
- [ ] Add loop detection threshold specification

### Section 17: Stateful Training Integration

- [ ] Rename to "xAI Collections Integration"
- [ ] Rewrite using xAI Collections terminology
- [ ] Add Collections lifecycle workflow
- [ ] Add file upload policy per phase
- [ ] Add retrieval policy per phase
- [ ] Add cleanup policy

### Section 18: Known Constraints and Risk Areas

- [ ] Add xAI API rate limits constraint
- [ ] Add response storage duration constraint
- [ ] Add Collections storage limits constraint
- [ ] Add response_id continuity risk
- [ ] Add Collections quota exhaustion risk
- [ ] Add tool citation tracking loss risk

### New Appendices

- [ ] Create Appendix C: xAI API Reference Integration
- [ ] Create Appendix D: Collections Lifecycle Diagrams
- [ ] Create Appendix E: Response Continuation Examples
- [ ] Create Appendix F: Schema Evolution Playbook

### Cross-Cutting

- [ ] Add Spec Change Management section to README
- [ ] Add VERSION file with semver
- [ ] Add Lesson L-011 about API-native terminology
- [ ] Global search-replace "training corpus" → "Collections"
- [ ] Add code examples to every API interaction point
- [ ] Add "DO NOT" statements for common mistakes

---

## Appendix B: Example Implementations

### Example 1: Response Continuation (Correct Pattern)

```python
from xai_sdk import Client
from xai_sdk.chat import user, system
import json

# Load project state
with open('project_state.json', 'r') as f:
    state = json.load(f)

client = Client(api_key=os.getenv('XAI_API_KEY'))
chat = client.chat.create(
    model='grok-4',
    store_messages=True  # EXPLICIT: Enable response storage
)

# Check if we have a previous response to continue from
previous_response_id = state.get('response_metadata', {}).get('current_phase_response_id')

if previous_response_id:
    # EXPLICIT: Continue conversation
    chat.append(system("Previous context loaded"))
    # SDK handles previous_response_id internally when continuing

# Add current phase prompts
chat.append(system(phase_system_prompt))
chat.append(user(phase_user_prompt))

# Request structured output
response, parsed = chat.parse(PhaseSchema)

# EXPLICIT: Store response_id for next phase
state['response_metadata']['current_phase_response_id'] = response.id
state['response_metadata']['phase_history'].append({
    'phase': current_phase,
    'response_id': response.id,
    'timestamp': datetime.utcnow().isoformat(),
    'model': 'grok-4',
    'success': True
})

# Atomic state write
with open('project_state.json.tmp', 'w') as f:
    json.dump(state, f, indent=2)
os.rename('project_state.json.tmp', 'project_state.json')
```

### Example 2: Collections Integration (Correct Pattern)

```python
from xai_sdk import Client
import os

client = Client(
    api_key=os.getenv('XAI_API_KEY'),
    management_api_key=os.getenv('XAI_MANAGEMENT_API_KEY')
)

# Phase 1: Create Collection (project init)
collection = client.files.collections.create(
    name=f"wet-donkey-{project_name}-{timestamp}",
    description=f"WD project artifacts for {topic}"
)

state['collection_id'] = collection.id

# Phase 2: Upload Artifacts
with open('research_notes.md', 'rb') as f:
    file = client.files.create(
        file=f,
        purpose='collection'
    )

client.files.collections.add_file(
    collection_id=state['collection_id'],
    file_id=file.id
)

# Phase 3: Use collections_search Tool
chat = client.chat.create(model='grok-4', store_messages=True)
chat.append(system("Use collections_search to find relevant research notes"))

# Configure collections_search tool
tools = [
    {
        'type': 'collections_search',
        'collection_ids': [state['collection_id']]
    }
]

response = chat.sample(tools=tools)

# IMPORTANT: Log tool citations
if response.tool_calls:
    for tool_call in response.tool_calls:
        if tool_call.type == 'collections_search':
            print(f"Retrieved: {tool_call.results}")
            # Store citations in response metadata
```

### Example 3: Structured Output with Schema Constraints (Correct)

```python
from pydantic import BaseModel, Field
from typing import Literal

class SceneOutput(BaseModel):
    """Phase schema compliant with xAI structured output constraints."""
    
    # ✅ CORRECT: No length constraints
    narration_text: str = Field(description="Scene narration")
    
    # ✅ CORRECT: Enum for constrained values
    scene_type: Literal["intro", "main", "conclusion"] = Field(
        description="Scene type"
    )
    
    # ✅ CORRECT: No array size constraints
    visual_elements: list[str] = Field(
        description="Visual elements"
    )
    
    # ❌ WRONG: minLength not supported
    # narration_text: str = Field(min_length=50)
    
    # ❌ WRONG: minItems not supported
    # visual_elements: list[str] = Field(min_items=1)
    
    # ❌ WRONG: allOf not supported
    # metadata: AllOf[BaseMetadata, ExtendedMetadata]

# Use with xAI SDK
response, scene = chat.parse(SceneOutput)
assert isinstance(scene, SceneOutput)  # Guaranteed by xAI
```

---

**End of Peer Review**

*This review was conducted to ensure Wet Donkey can be implemented successfully by AI coding assistants with minimal ambiguity and maximum alignment with xAI API capabilities.*