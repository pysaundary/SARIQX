# SARIQX ENTERPRISE B2B SAAS TECHNICAL BLUEPRINT

## System Architecture, Relational Schema Design, and Multiphase Implementation Roadmap

---

# SARIQX ENTERPRISE B2B SAAS TECHNICAL BLUEPRINT
## System Architecture, Relational Schema Design, and Multiphase Implementation Roadmap

---

## 1. Executive Architectural Vision & The Relational Paradigm Shift

### 1.1 The Architecture Mandate
SARIQX is engineered as an enterprise-grade, multi-tenant B2B SaaS platform designed to operate as a robust Educational Operating System. The platform requires iron-clad tenant data isolation, strict structural constraints, multi-variable financial billing, real-time resource metering, and deep analytical processing. 

### 1.2 The Relational Paradigm: Why PostgreSQL Prevails Over MongoDB
A common architectural anti-pattern in modern web development is the indiscriminate deployment of NoSQL databases like MongoDB for complex business applications. For an enterprise B2B SaaS application like SARIQX, MongoDB is fundamentally unsuited due to the following structural limitations:

1. **Lack of Strict Referential Integrity & Cascade Operations:** SARIQX operates on a deeply nested relational hierarchy: `Tenant -> User -> Question -> Answer -> Attachment`. In MongoDB, maintaining consistency across these boundaries requires manual, application-level two-phase commits. PostgreSQL enforces this natively via declarative foreign key constraints with optimized `ON DELETE CASCADE` and `ON UPDATE` behaviors, guaranteeing that orphaned records can never exist.
2. **Absence of Native Window Functions and Common Table Expressions (CTEs):** Complex analytical processing—such as calculating running storage totals per tenant, dynamically ranking instructor performance within a specific institution, or computing percentile distributions for student report cards—requires advanced query capabilities. MongoDB’s aggregation pipeline is verbose, memory-intensive, and lacks the optimized, single-pass mathematical processing of PostgreSQL’s `OVER (PARTITION BY ...)` window functions and recursive CTEs.
3. **Data Storage Amplification and Lack of Normalization:** MongoDB stores data as denormalized BSON documents. In a multi-tenant system, repeating tenant metadata, user metadata, and status enums within every document causes massive storage amplification. PostgreSQL’s normalized storage model ensures that data is stored exactly once, maximizing cache hit ratios across memory pages.
4. **ACID Transaction Guarantees Across Tenant Boundaries:** Financial operations, coupon redemptions, and real-time storage quota increments must happen atomically. A failure in linking an image attachment to a question must roll back the entire transaction. PostgreSQL provides true, enterprise-grade ACID transactions via Write-Ahead Logging (WAL), whereas MongoDB's multi-document transactions introduce significant latency and lock contention at scale.

---

## 2. Current Core System Architecture (Completed Modules)

The core foundation of SARIQX has been completely implemented using a decoupled, asynchronous Python architecture backed by FastAPI, SQLAlchemy 2.0, and PostgreSQL.

```text
+-----------------------------------------------------------------------------------+
|                                  SARIQX BACKEND                                   |
+-----------------------------------------------------------------------------------+
                                         |
         +-------------------------------+-------------------------------+
         |                               |                               |
         v                               v                               v
+------------------+           +-------------------+           +-------------------+
|  Dual-Token Auth |           |  Resolution Core  |           |  Media Pipeline   |
|   (JWT Rotation) |           |  (Tenant Iso. &   |           |  (Pillow WebP &   |
|   & Unique Slug  |           |   Eager Loading)  |           |   Dynamic Paths)  |
+------------------+           +-------------------+           +-------------------+
2.1 Dual-Token Authentication Subsystem with Cryptographic Rotation

The authentication pipeline utilizes a secure, state-free dual-token architecture to eliminate permanent session vulnerability while enabling seamless user experiences.

    Access Tokens: Short-lived cryptographic signatures (30-minute expiry) carrying user identity, tenant boundaries, and Role-Based Access Control (RBAC) scopes.

    Refresh Tokens: Long-lived tokens (7-day expiry) used exclusively to hit the /api/v1/auth/refresh endpoint.

    Cryptographic Flow & Interceptor Integration: When an expired access token hits the API, the backend intercepts the verification via jwt.ExpiredSignatureError and bubbles up an explicit HTTP 401 response payload with detail: "TOKEN_EXPIRED". This structural error code allows client-side interceptors to pause the request queue, submit the refresh token to obtain a fresh access token, and replay the original request invisibly to the end user.

    Collision-Free Username Generation: To prevent tutor poaching and email scraping from rival institutions, the registration pipeline automatically generates a slugified, unique username. It extracts the email prefix, applies regular expression sanitization, appends the final 8-character block of a pre-generated uuid.uuid4(), and maps it directly to the database. This guarantees O(1) execution time and completely eliminates race conditions.

2.2 Core Resolution Engine & Multi-Tenant Isolation

The data layer enforces rigid multi-tenancy at the query construction phase rather than relying on application-level filtering.

    RBAC Enforcement: Users are statically mapped to an enumeration type: SUPER_ADMIN, TENANT_ADMIN, TENANT_MODERATOR, and END_USER.

    Query Isolation Matrix: * END_USER (Students) queries are automatically appended with a WHERE student_id = current_user.id clause, restricting access strictly to personal data.

        TENANT_ADMIN and TENANT_MODERATOR queries are structurally constrained with a WHERE tenant_id = current_user.tenant_id clause, ensuring complete data boundary enforcement between competing educational institutions.

    N+1 Query Elimination: To optimize data fetching across deep relational trees, all feed endpoints utilize SQLAlchemy 2.0’s selectinload() strategy. This loads nested structures (e.g., questions with their respective attachments and answers) in exactly two database roundtrips, regardless of array lengths.

2.3 Media Upload Pipeline & Asynchronous Strategy Pattern

The multimedia attachment layer is completely decoupled from the local filesystem or specific cloud providers via an abstract interface layer.

    The Strategy Pattern: The system defines a structural contract via an Abstract Base Class StorageProvider enforcing an asynchronous upload_file signature. The runtime behavior switches dynamically based on environment configuration (STORAGE_PROVIDER=local or s3), allowing migration from local drives to global cloud buckets with zero structural code modifications.

    Background Processing & Optimization Engine: Images are normalized to RGB mode, structurally downscaled using high-fidelity LANCZOS resampling if widths exceed 1920 pixels, and compressed natively into the modern WEBP format. This cuts raw DSLR image footprints from ~15MB down to <400KB while preserving microscopic mathematical notation clarity.

    Dynamic Relative-to-Absolute Path Resolution: The database stores exclusively relative POSIX paths (/media/tenant_id/...). The API response layer maps this string through a Pydantic 2.0 @computed_field decorator, dynamically prepending the environmental configuration value BACKEND_BASE_URL at serialization time.

3. Phase 1: B2B SaaS Multi-Tenant Billing & Resource Metering Engine (UPCOMING)

This module transforms the application into a functional commercial B2B SaaS system by embedding structural quotas and programmatic access control boundaries.
3.1 Extended Subscription Relational Schema
CREATE TYPE plan_tier_enum AS ENUM ('FREE', 'PRO', 'ENTERPRISE');

ALTER TABLE tenants ADD COLUMN plan_tier plan_tier_enum DEFAULT 'FREE' NOT NULL;
ALTER TABLE tenants ADD COLUMN max_students INTEGER DEFAULT 50 NOT NULL;
ALTER TABLE tenants ADD COLUMN max_staff INTEGER DEFAULT 3 NOT NULL;
ALTER TABLE tenants ADD COLUMN max_storage_mb DOUBLE PRECISION DEFAULT 100.0 NOT NULL;
ALTER TABLE tenants ADD COLUMN used_storage_mb DOUBLE PRECISION DEFAULT 0.0 NOT NULL;

CREATE TABLE coupons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    discount_percent INTEGER NOT NULL CHECK (discount_percent > 0 AND discount_percent <= 100),
    max_redemptions INTEGER NOT NULL,
    current_redemptions INTEGER DEFAULT 0 NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    valid_until TIMESTAMP WITH TIME ZONE NOT NULL
);
3.2 Programmatic Quota Enforcement

    User Registration Boundaries: Before processing a user insertion, the engine queries the active count of existing users mapped to that specific tenant_id. If limits are exceeded, the transaction is aborted with an HTTP 402 Payment Required (STUDENT_LIMIT_EXCEEDED).

    Storage Volume Metering: Prior to executing physical storage writes, the system calculates the file footprint in MB. If tenant.used_storage_mb + incoming_mb > tenant.max_storage_mb, the pipeline terminates with an HTTP 402 status code. Upon success, the tenant's used_storage_mb is incremented atomically.

3.3 Payment Gateway Integration Architecture

    Checkout Session Generation: FastAPI generates a cryptographic checkout configuration payload via the Stripe/Razorpay SDK.

    Asynchronous Webhook Listener: A dedicated route /api/v1/billing/webhook ingests and verifies raw cryptographic event streams sent directly from the payment provider servers.

    State Synchronization: Upon a verified payment event, the system executes an atomic model upgrade mapping the new structural boundaries (e.g., expanding limits for a PRO tier shift).

4. Phase 2: Relational Intelligence Dashboards (Advanced SQL Processing)

Leveraging advanced relational analytical techniques directly inside the PostgreSQL layer.
4.1 The Tutor Performance Analytics Dashboard (Window Functions)

Bypassing application-level loops, the system deploys optimized SQL window processing to track tutor engagement and response latency.
WITH tutor_metrics AS (
    SELECT 
        u.id AS tutor_id,
        u.username AS tutor_username,
        u.tenant_id,
        COUNT(a.id) AS total_answers_posted,
        COALESCE(AVG(EXTRACT(EPOCH FROM (a.created_at - q.created_at)) / 60), 0.0) AS avg_resolution_time_minutes
    FROM users u
    INNER JOIN answers a ON a.solver_id = u.id
    INNER JOIN questions q ON a.question_id = q.id
    WHERE u.is_deleted = FALSE AND u.is_active = TRUE
    GROUP BY u.id, u.username, u.tenant_id
)
SELECT 
    tutor_id,
    tutor_username,
    tenant_id,
    total_answers_posted,
    ROUND(avg_resolution_time_minutes::numeric, 2) AS avg_response_time_minutes,
    DENSE_RANK() OVER (
        PARTITION BY tenant_id 
        ORDER BY total_answers_posted DESC, avg_resolution_time_minutes ASC
    ) AS tenant_internal_rank
FROM tutor_metrics;
4.2 The Institute Admin CCTV & Security Audit System

    Content Constraint Engine: Text payloads are parsed through a lightweight dictionary evaluation. If blacklisted substring patterns match, the record's flag is immediately set to PROFANITY or ADULT_CONTENT.

    Security Escalation Feed (CTE Architecture): An administrative view that computes a tenant's historical moderation breach distribution alongside active flagged records.
    4.2 The Institute Admin CCTV & Security Audit System

    Content Constraint Engine: Text payloads are parsed through a lightweight dictionary evaluation. If blacklisted substring patterns match, the record's flag is immediately set to PROFANITY or ADULT_CONTENT.

    Security Escalation Feed (CTE Architecture): An administrative view that computes a tenant's historical moderation breach distribution alongside active flagged records.
    5. Phase 3: Live Assessment, Notification Pipeline & Surprise Test Subsystem
5.1 Relational Architecture for Academic Examinations

Implementing strict tables for exams, exam_questions (with JSONB for options), and exam_submissions.
5.2 The Surprise Test Subsystem Architecture

    The Interception Pipeline: Backend initializes an exam record, shifts start_time to the current system timestamp, and locks end_time strictly.

    Notification Dispatch: The backend triggers a high-priority WebSocket payload carrying the structural test schema directly to all connected client nodes for that specific tenant.

    Client Real-Time Interception: The active Svelte frontend locks out input fields and forces a full-screen modal overlay.

5.3 Automated Academic Metrics Engine

Generates comprehensive report cards using multi-expression CTEs and true percentile calculations (NTILE(100)).
WITH student_scores AS (...),
exam_global_metrics AS (...),
ranked_student_matrix AS (
    SELECT 
        ss.student_id,
        ss.absolute_score,
        -- Calculate the exact mathematical percentile across the test boundary
        NTILE(100) OVER (
            PARTITION BY ss.exam_id 
            ORDER BY ss.absolute_score ASC
        ) AS student_percentile
    FROM student_scores ss
    INNER JOIN exam_global_metrics egm ON ss.exam_id = egm.exam_id
)
SELECT * FROM ranked_student_matrix;
6. Phase 4: Svelte Frontend Integration & Reactive State Architecture

The frontend client is an optimized SPA utilizing Svelte and Vite for high reactivity.
6.1 Asynchronous Token Rotation Interceptor Flow

Axios configuration handles background security token refreshes invisibly without disrupting user flow.
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        if (error.response?.status === 401 && error.response.data.detail === "TOKEN_EXPIRED" && !originalRequest._retry) {
            originalRequest._retry = true;
            try {
                const refreshResponse = await axios.post('/auth/refresh', { refresh_token });
                // Save new tokens and replay originalRequest
            } catch (err) {
                // Wipe local storage and redirect to /login
            }
        }
        return Promise.reject(error);
    }
);
6.2 Flawless Reactive Component Design (Doubt Ingestion)

The form submits the file payload to /upload, receives the relative_path, appends it to the attachments array, and submits the final JSON payload to /doubts/ask. The state is then cleared cleanly without a page reload.
7. Phase 5: Real-Time Communication & Live Doubt Rooms
7.1 Approach A: Google Meet API Automation (MVP)

    Backend securely holds a Google Workspace service-account identity.

    Triggers event creation request to Google Calendar API.

    Inserts the returned conferenceData URL into the active tenant's database as a "JOIN LIVE MEETING" entry.

7.2 Approach B: High-Performance Native WebRTC Bridge (Future Scale)

    Deploying a centralized media bridge (SFU like Mediasoup or LiveKit) to avoid inefficient peer-to-peer mesh networking.

    Instructors stream high-definition video upstream once; the server forwards the track downstream to students, ensuring low latency and low client resource consumption.
