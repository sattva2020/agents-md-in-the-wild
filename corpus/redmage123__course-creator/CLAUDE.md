# CLAUDE.md - Course Creator Platform Documentation

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Version**: 3.3.1 - Login Redirect Fixes & Authentication Enhancement
**Last Updated**: 2025-10-08

---

## 🚀 MANDATORY SESSION START PROTOCOL

**AT THE START OF EVERY SESSION, CLAUDE CODE MUST:**

### Step 1: Load Core Methodology (30 seconds)
```bash
# Check user preferences (CRITICAL - DO THIS FIRST)
python3 .claude/query_memory.py search "Agile"
python3 .claude/query_memory.py search "TDD"
python3 .claude/query_memory.py search "parallel"

# Review recent context
python3 .claude/query_memory.py list 20
```

### Step 2: Internalize Methodology (No user reminder needed)
- ✅ User ALWAYS wants Agile + Kanban boards (automatic)
- ✅ User ALWAYS wants TDD - tests BEFORE code (automatic)
- ✅ User ALWAYS wants TodoWrite tracking (automatic)
- ✅ User NEVER wants to be reminded of these preferences
- ✅ For complex tasks: Use Parallel Agent Development System (PADS)

### Step 3: Reference Self-Improvement Framework
- **Read**: `.claude/CLAUDE_SELF_IMPROVEMENT_PLAN.md` for behavioral guidelines
- **Read**: `.claude/PARALLEL_AGENT_DEVELOPMENT_SYSTEM.md` for parallel workflows
- **Templates**: `.claude/templates/` for TDD, Kanban, session checklists

### Step 4: Confirm Readiness
Silently confirm understanding of:
- Memory-first workflow
- TDD approach (Red-Green-Refactor)
- Parallel agent development for efficiency
- TodoWrite for task tracking
- Tentative language (no false claims)

**THESE ARE NOW DEFAULT BEHAVIOR - NOT OPTIONAL**

---

## 📁 Documentation Structure

This documentation is organized into logical sections within the `claude.md/` subdirectory:

### Core Requirements & Standards
- **[Critical Requirements](claude.md/01-critical-requirements.md)** - Absolute imports, exception handling, file editing efficiency
- **[Documentation Standards](claude.md/02-documentation-standards.md)** - Comprehensive code documentation requirements
- **[Memory System](claude.md/03-memory-system.md)** - Mandatory persistent memory system usage

### Version History & Features
- **[Version History](claude.md/04-version-history.md)** - Platform evolution and feature updates
- **[Architecture Overview](claude.md/05-architecture.md)** - Microservices structure and dependencies
- **[Key Systems](claude.md/06-key-systems.md)** - Quiz management, feedback, RBAC, RAG, lab containers

### Development & Operations
- **[Development Commands](claude.md/07-development-commands.md)** - Platform management, testing, database operations
- **[Testing Strategy](claude.md/08-testing-strategy.md)** - Comprehensive testing framework and requirements
- **[Quality Assurance](claude.md/09-quality-assurance.md)** - Code validation, CI/CD pipeline, compliance verification
- **[Troubleshooting](claude.md/10-troubleshooting.md)** - Common issues, debugging, problem-solving methodology

## 🚨 CRITICAL BEHAVIORAL REQUIREMENTS FOR CLAUDE CODE

### 1. MANDATORY COMPREHENSIVE E2E SELENIUM TESTING - ALL ROLES (v3.2.2)
**HIGHEST PRIORITY - APPLIES TO ALL CODE CHANGES**

- **MANDATORY**: Subagents MUST perform Selenium E2E tests on **EVERY feature and pathway for ALL user roles**
- **NO EXCEPTIONS**: All user journeys for ALL 4 roles must have complete E2E test coverage
- **TARGET**: 90%+ E2E coverage across 14 major feature areas and ALL roles (currently ~45-60%)
- **CRITICAL REQUIREMENT**: Test ALL roles, not just students!

**User Roles Requiring Complete Coverage (4 authenticated + 1 unauthenticated):**
1. **Site Admin** - Platform administration, all organizations, system configuration
2. **Organization Admin** - Member management, organization settings, tracks, compliance
3. **Instructor** - Course creation, content generation, student management, analytics
4. **Student** - Learning workflows, assessments, labs, progress tracking
5. **Anonymous/Guest** - Public pages, registration, course browsing (unauthenticated)

**Comprehensive Test Plan:** `/home/bbrelin/course-creator/tests/COMPREHENSIVE_E2E_TEST_PLAN.md`

**Priority 0 Tests (Must Implement First) - ALL ROLES:**
1. Complete Student Learning Journey (Login → Learn → Quiz → Lab → Certificate)
2. Complete Instructor Workflow (Create Course → Generate Content → Manage Students → Analytics)
3. Complete Organization Admin Workflow (Manage Members → Configure Org → Tracks → Reports)
4. Complete Site Admin Workflow (Platform Admin → Monitor System → Manage All Orgs)
5. Anonymous/Guest Workflows (Browse → Register → Password Reset)
6. RAG AI Assistant Workflow (ALL roles can interact with AI)
7. Content Generation Pipeline (Instructor role)

**Quick Test Command:**
```bash
# Run Priority 0 tests for ALL roles
pytest tests/e2e/critical_user_journeys/ -v

# Run specific role tests
pytest tests/e2e/critical_user_journeys/test_student_complete_journey.py -v
pytest tests/e2e/critical_user_journeys/test_instructor_complete_journey.py -v
pytest tests/e2e/critical_user_journeys/test_org_admin_complete_journey.py -v
pytest tests/e2e/critical_user_journeys/test_site_admin_complete_journey.py -v
pytest tests/e2e/critical_user_journeys/test_guest_complete_journey.py -v
```

### 2. MANDATORY DOCKER INFRASTRUCTURE TESTING (v3.2.2)
**SECOND HIGHEST PRIORITY - APPLIES TO ALL CODE CHANGES**

- **BEFORE** any PR or commit: ALL Docker containers MUST be healthy
- **MANDATORY** GitHub Actions workflow: `docker-infrastructure-test` must pass
- **NO EXCEPTIONS**: Every code change requires Docker health verification
- **ALL 16 SERVICES** must pass health checks with HTTPS enabled
- **VERIFICATION REQUIRED**: Run `./scripts/app-control.sh status` and confirm all green checkmarks

**Quick Verification Command:**
```bash
# THIS MUST PASS BEFORE ANY PR
./scripts/app-control.sh status 2>&1 | grep "✅"
# Expected: 16 services showing "✅ Healthy"
```

### 3. NO FALSE SUCCESS CLAIMS
- **NEVER** claim a task is "completed" or "successful" unless you have PROVEN it works through actual testing
- **NEVER** say "✅" or mark anything as working without concrete evidence
- **NEVER** use phrases like "successfully completed", "working correctly", "fixed", "healthy" without verification

### 4. MANDATORY VERIFICATION REQUIREMENTS
- Before claiming ANY task completion, you MUST provide concrete evidence:
  - Service responding to HTTP requests with 200 status
  - Actual command output showing success
  - Container running with "Up (healthy)" status
  - Real test results, not assumptions
  - **Docker infrastructure tests passing** (see requirement #1)

### 5. MANDATORY MEMORY TOOL USAGE - ALWAYS FIRST, EVERY TASK

**CRITICAL RULE: MEMORY SEARCH IS THE FIRST ACTION FOR EVERY TASK**

Before doing ANYTHING - before reading files, before writing code, before running commands - you MUST:

1. **Search memory for task-relevant facts** (keywords: technology, feature, component)
2. **Search memory for constraints** (keywords: HTTPS, requirements, architecture)
3. **Review recent context** (`list 20`)

**Memory Tool Commands:**
```bash
# ALWAYS START WITH THESE - NO EXCEPTIONS
python3 .claude/query_memory.py search "relevant_keyword"
python3 .claude/query_memory.py search "constraints"
python3 .claude/query_memory.py list 20

# Add new facts AFTER discoveries
python3 .claude/query_memory.py add "<fact_content>" "<category>" "<importance>"
```

**Why This Matters:**
- Prevents repeating mistakes (like using HTTP instead of HTTPS)
- Ensures critical requirements aren't forgotten
- Maintains consistency with user preferences
- Avoids redundant work

**Mandatory Memory Workflow:**
1. **BEFORE** making any technical decision → Search memory for relevant facts
2. **DURING** investigation → Document findings as you discover them
3. **AFTER** fixing bugs → Add facts about root cause and solution
4. **NEVER** assume you know something → Verify it exists in memory first

**Example Workflow:**
```bash
# User says: "The platform uses HTTPS only"
# Step 1: Search memory to verify
python3 .claude/query_memory.py search "HTTPS"
# Found: ID 300 confirms HTTPS-only requirement

# Step 2: Work on the task using this fact

# Step 3: Add new discovery
python3 .claude/query_memory.py add "Service endpoint discovered: /users/me (not /api/v1/users/me)" "api-endpoints" "critical"
```

### 4. MEMORY AND STATE TRACKING
- **ALWAYS** maintain accurate state of what has been attempted vs. what actually works
- If something failed before, acknowledge it failed and explain what's different this time
- Keep track of which services/components are genuinely working vs. still broken

### 5. TRUTHFUL STATUS REPORTING
When reporting status, use only these categories:
- **WORKING**: Verified with evidence (show the evidence)
- **ATTEMPTED**: Tried but not verified to work
- **BROKEN**: Confirmed not working
- **UNKNOWN**: Not yet tested

### 6. PROBLEM ACKNOWLEDGMENT
- If you encounter the same error repeatedly, STOP and acknowledge the pattern
- Don't keep trying the same approach that already failed
- Ask for guidance when stuck in loops

### 7. NO ASSUMPTION-BASED CLAIMS
- Don't claim something works because "the code looks right"
- Don't assume Docker containers work because they built successfully
- Verify actual functionality, not just absence of build errors

### 8. SYSTEMATIC VERIFICATION PROTOCOL
**Before claiming ANY fix works, you MUST:**
- **Test the exact failing case** - Copy/paste the exact error scenario and reproduce it
- **Test in the actual environment** - Not just isolated unit tests, but in the real deployment context
- **Provide evidence** - Show the before/after comparison with actual output
- **Wait for user confirmation** - Never declare success, only "attempted fix - please verify"

### 9. LANGUAGE RESTRICTIONS
**FORBIDDEN phrases (never use these without concrete proof):**
- ✅ "PROVEN: [anything] is working"
- ✅ "The error should now be resolved"
- ✅ "Pattern/code compiles successfully!"
- ✅ "Both fixes are working"
- ✅ "Successfully completed"
- ✅ "Working correctly"

**REQUIRED language (always use these instead):**
- 🔄 "I've made a change that might fix this. Please test it."
- 🔄 "Here's what I changed and why. Can you verify if it works?"
- 🔄 "The pattern works in my test, but please confirm in your browser."
- 🔄 "Attempted fix deployed - needs user verification"

### 10. ROOT CAUSE ANALYSIS REQUIREMENT
**When debugging, you MUST:**
- **Understand the problem** (not just pattern-match visual symptoms)
- **Research the root cause** (don't guess based on superficial similarities)
- **Test exact scenario** (reproduce the exact failure first)
- **Make minimal changes** (one thing at a time)
- **Document uncertainty** (what you're not sure about)

### 11. ANTI-PATTERN RECOGNITION
**Recognize and STOP these harmful patterns:**
- Visual pattern recognition → quick fix instinct → biased testing
- "This looks wrong" → make change → assume it's fixed
- Deployment success → claim functional success
- Isolated test passes → claim real-world functionality
- Speed/confidence prioritized over accuracy/verification

### 12. EPISTEMOLOGICAL HUMILITY
**Acknowledge the limits of what you can know:**
- You cannot directly interact with user browsers
- You cannot see actual user experience
- Your tests are simulations, not reality
- Deployment ≠ functionality
- Code compilation ≠ runtime success

## 🚨 Critical Code Directives (Always Apply)

### 1. Python Import Requirements
**ABSOLUTE IMPORTS ONLY** - Never use relative imports (`from ..`, `from .`) in Python files.

**SERVICE-SPECIFIC NAMESPACES** - All services use service-specific namespaces to prevent collision:

**9 Services with Clean Architecture (domain/application/infrastructure layers):**
- `analytics` → imports from `analytics.domain.*`, `analytics.application.*`, `analytics.infrastructure.*`
- `content-management` → imports from `content_management.domain.*`, `content_management.application.*`, `content_management.infrastructure.*`
- `course-generator` → imports from `course_generator.domain.*`, `course_generator.application.*`, `course_generator.infrastructure.*`
- `course-management` → imports from `course_management.domain.*`, `course_management.application.*`, `course_management.infrastructure.*`
- `knowledge-graph-service` → imports from `knowledge_graph_service.domain.*`, `knowledge_graph_service.application.*`, `knowledge_graph_service.infrastructure.*`
- `metadata-service` → imports from `metadata_service.domain.*`, `metadata_service.application.*`, `metadata_service.infrastructure.*`
- `nlp-preprocessing` → imports from `nlp_preprocessing.domain.*`, `nlp_preprocessing.application.*`, `nlp_preprocessing.infrastructure.*`
- `organization-management` → imports from `organization_management.domain.*`, `organization_management.application.*`, `organization_management.infrastructure.*`
- `user-management` → imports from `user_management.domain.*`, `user_management.application.*`, `user_management.infrastructure.*`

**Directory Structure:**
```
services/SERVICE-NAME/
├── service_name_package/       # ← New namespace directory (underscored)
│   ├── __init__.py
│   ├── domain/                 # ← Domain layer under service namespace
│   │   └── entities/
│   ├── application/            # ← Application layer under service namespace
│   │   └── services/
│   └── infrastructure/         # ← Infrastructure layer under service namespace
│       └── repositories/
├── data_access/                # ← Shared DAOs (not in namespace)
├── api/                        # ← API endpoints (not in namespace)
└── main.py                     # ← Service entry point
```

**Import Examples:**
```python
# OLD (namespace collision - DO NOT USE):
from domain.entities.course import Course
from application.services.course_service import CourseService

# NEW (service-specific namespace - USE THIS):
from course_management.domain.entities.course import Course
from course_management.application.services.course_service import CourseService
```

**Note**: Service directory names use hyphens (`content-management`), but Python package names use underscores (`content_management`).

### 2. Exception Handling
**CUSTOM EXCEPTIONS MANDATORY** - Never use generic `except Exception as e` handlers. Use structured custom exceptions with f-strings.

### 3. Documentation Requirements
**COMPREHENSIVE DOCUMENTATION** - All code must include multiline string documentation explaining business context and technical rationale.

### 4. Memory System Usage
**MANDATORY MEMORY SYSTEM** - Must use the persistent memory system for context continuity across conversations.

### 5. File Type-Specific Comment Syntax
- Python: `"""multiline strings"""` 
- JavaScript: `//` or `/* */`
- CSS: `/* */`
- HTML: `<!-- -->`
- YAML: `#`
- SQL: `--` or `/* */`
- Bash: `#`

## 🏗️ Platform Overview

The Course Creator Platform is a comprehensive educational technology system with:

- **9 Microservices** (ports 8000-8010) providing authentication, content generation, lab management, analytics, RBAC, and demo functionality
- **Multi-IDE Lab Environment** with individual Docker containers for students
- **Enhanced RBAC System** with multi-tenant organization management and Guest role
- **RAG-Enhanced AI** for progressive learning and content generation
- **Demo Service** with realistic data generation for platform demonstration (port 8010)
- **Guest Session Privacy Compliance** with GDPR/CCPA/PIPEDA-compliant PostgreSQL storage and privacy APIs
- **Enhanced AI Chatbot** with NLP, RAG, knowledge graph integration, and personalized onboarding
- **Comprehensive Testing** with 102 RBAC tests achieving 100% success rate plus 101+ demo service tests
- **Advanced Password Management** with secure admin account creation and self-service password changes
- **Enhanced UI/UX** with keyboard navigation, accessibility features, and responsive design

## 📖 How to Read This Documentation

When Claude Code needs to reference this documentation:

1. **Start here** - Read this root file for overview and critical directives
2. **Navigate to specific sections** - Use the links above to access detailed information
3. **Follow cross-references** - Related sections reference each other for comprehensive understanding

## 🔄 Quick Navigation

For immediate needs:
- **Development Setup**: See [Development Commands](claude.md/07-development-commands.md)
- **Troubleshooting**: See [Troubleshooting](claude.md/10-troubleshooting.md)
- **Architecture Questions**: See [Architecture Overview](claude.md/05-architecture.md)
- **Testing Issues**: See [Testing Strategy](claude.md/08-testing-strategy.md)
- **Privacy Compliance**: See [Guest Session Privacy Compliance](docs/GUEST_SESSION_PRIVACY_COMPLIANCE.md)
- **Privacy API**: See [Privacy API Documentation](docs/PRIVACY_API_DOCUMENTATION.md)

---

**COMPLIANCE REQUIREMENT**: All code must adhere to the critical directives listed above and the detailed requirements in the subdirectory files.