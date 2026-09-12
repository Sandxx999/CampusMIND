# CampusMIND 2.0 — Phase 5 Academic Analytics & Intelligence Architecture

## 1. Architecture Overview

Phase 5 extends CampusMIND 2.0 from a secure institutional RAG/chat platform into an intelligent academic assistance platform capable of personalized student insights, attendance risk analysis, course/assessment analytics, and role-based institutional intelligence.

```
+-----------------------------------------------------------------------------------+
|                                  React Frontend                                   |
|               (Assistant Chat, Campus Intelligence, Academic Analytics)            |
+-----------------------------------------------------------------------------------+
                                          │
                                HTTP REST API Calls
                                          ▼
+-----------------------------------------------------------------------------------+
|                              FastAPI API Routes                                   |
|                        /api/v1/analytics/*  |  /api/v1/chat                      |
+-----------------------------------------------------------------------------------+
                                          │
                        Server-Side JWT & Role Verification
                                          ▼
+-----------------------------------------------------------------------------------+
|                             Analytics & Chat Service                              |
|           (AnalyticsService | ChatService | AcademicQueryRouter)                  |
+-----------------------------------------------------------------------------------+
                      │                                        │
           Policy & Doc Queries                      Personal Data & Stats
                      ▼                                        ▼
+---------------------------+             +-----------------------------------------+
|    RAG Retrieval Engine   |             |         Academic Analytics Engine       |
| (ChromaDB / BM25 / Rerank)|             |  (AttendanceRiskEngine / Recommendations)|
+---------------------------+             +-----------------------------------------+
                      │                                        │
           Institutional Knowledge                     Canonical ORM Database
                      ▼                                        ▼
         Documents & Syllabi                         SQLite / PostgreSQL Database
```

---

## 2. Analytics Data Flow

1. **Request Ingestion**: User invokes an analytics API endpoint (`/api/v1/analytics/*`) or sends a chat message.
2. **Server-Side Authentication & Authorization**: The request JWT token is validated. The user's role and identity context (`username`, `role`, `enrollment_no`) are extracted.
3. **Intent Routing**: For chat queries, `AcademicQueryRouter` classifies whether the query targets institutional knowledge, student personal data, student analytics, course analytics, faculty analytics, or admin analytics.
4. **Deterministic Calculation**: `AnalyticsEngine` retrieves normalized records from the database (`AttendanceRecord`, `AssessmentGrade`, `Enrollment`, `StudentProfile`, `CourseOffering`). No machine-learning hallucinations or fabricated values are introduced.
5. **Risk & Recommendation Generation**: `AttendanceRiskEngine` computes deficit and recovery requirements. `RecommendationEngine` generates explainable rules.
6. **Audited Response & Synthesis**: The response is logged to `AuditEvent` via `AuditRepository` and returned via strict Pydantic schemas.

---

## 3. Authorization Boundaries

| Role | Permitted Analytics Scope | Unauthorized Access Attempts |
|---|---|---|
| **Student** | Own academic profile, attendance, performance, risk, and recommendations (`/api/v1/analytics/student/me/*`) | Attempting to access another student's record or admin/faculty endpoints returns `403 Forbidden` / `404 Not Found`. |
| **Faculty** | Authorized course offering sections assigned to the faculty member (`/api/v1/analytics/faculty/offerings/{offering_id}/*`) | Attempting to access course offerings taught by other faculty returns `403 Forbidden`. |
| **Admin** | Institution-wide overview, department-level, and program-level analytics (`/api/v1/analytics/admin/*`) | Non-admin roles attempting admin endpoints return `403 Forbidden`. |

*Note*: Client-supplied role claims, user IDs, or enrollment parameters in request bodies/headers are **NEVER** trusted. All authorization decisions remain strictly server-side based on validated JWT identity tokens.

---

## 4. Attendance Risk Calculation Rules

Attendance risk analysis is deterministic and explainable.

### Policy Thresholds & Categories
- Default Required Threshold: **75.0%**
- Categories:
  - **`SAFE`**: Current Attendance $\ge 75.0\%$
  - **`WATCH`**: $70.0\% \le \text{Current Attendance} < 75.0\%$
  - **`AT_RISK`**: $60.0\% \le \text{Current Attendance} < 70.0\%$
  - **`CRITICAL`**: Current Attendance $< 60.0\%$
  - **`UNKNOWN`**: Insufficient conducted class data ($\le 0$ classes conducted)

### Deficit & Recovery Calculations
- **Deficit Percentage**: $\max(0.0, \text{Required Pct} - \text{Current Pct})$
- **Consecutive Classes Needed to Recover**:
  Let $A$ = attended classes, $C$ = conducted classes, $R$ = required ratio ($0.75$).
  $$N = \left\lceil \frac{R \cdot C - A}{1 - R} \right\rceil$$
  Where $N$ represents the minimum number of consecutive future classes a student must attend without missing to reach the $R \times 100\%$ threshold.

---

## 5. Performance Calculation Rules

- **Assessment Score Percentage**: $\frac{\text{Obtained Marks}}{\text{Max Marks}} \times 100$
- **Course Average Score**: Arithmetic mean of published assessment percentages within a course section.
- **Assessment Type Performance**: Categorized breakdown across `quiz`, `assignment`, `midterm`, `final`, `lab`.
- **Strongest / Focus Subjects**: Courses ranked by highest and lowest assessment average percentages.
- **Insufficient Data Behavior**: When no assessment grades exist for a student, the engine returns `assessment_average: null` and sets `insufficient_data: true` without inventing synthetic scores.

---

## 6. Recommendation Rules

Recommendations are generated using transparent, deterministic rules:
- **Attendance Risk Guidance**:
  - `CRITICAL` / `AT_RISK`: Suggests exact consecutive classes needed to recover eligibility (`severity: critical/warning`).
  - `WATCH`: Warns about low margin (`severity: warning`).
  - `SAFE`: Encourages sustaining attendance (`severity: positive`).
- **Assessment Performance Guidance**:
  - Average score $< 50\%$: Recommends office hours consultation (`severity: critical`).
  - Average score $50\% - 69.9\%$: Recommends subject review (`severity: warning`).
  - Average score $\ge 80\%$: Recommends maintaining study pattern (`severity: positive`).
- **Backlog Guidance**:
  - Active backlogs $> 0$: Recommends registering for clearing examinations (`severity: critical`).

---

## 7. RAG vs Structured Data Security Boundary

```
  Institutional Policies & Documents   ────>   ChromaDB RAG Index   ────>   RAG Retrieval
  Private Student Records & Grades    ────>   Relational Database   ────>   Authorized Repositories
  Calculated Personal Analytics       ────>   Analytics Engine      ────>   Audit-Logged APIs
```

- Private student records, grades, CGPA, attendance logs, or backlogs are **NEVER** embedded into the general ChromaDB vector index.
- For combined queries (e.g. *"What attendance do I need to maintain?"*):
  1. The official attendance policy document is retrieved from RAG.
  2. The student's personal attendance metrics are calculated from the relational database via `AnalyticsEngine`.
  3. The answer is synthesized with explicit section headers distinguishing **Official Institutional Policy** from **Calculated Personal Metrics**.

---

## 8. Versioned API Endpoints (`/api/v1/analytics/`)

| Method | Endpoint Path | Authorization | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/analytics/student/me` | Authenticated Student | Complete student academic summary & recommendations |
| `GET` | `/api/v1/analytics/student/me/attendance` | Authenticated Student | Student course-wise attendance & trend |
| `GET` | `/api/v1/analytics/student/me/performance` | Authenticated Student | Student assessment averages & GPA |
| `GET` | `/api/v1/analytics/student/me/risk` | Authenticated Student | Student attendance risk analysis & recovery formula |
| `GET` | `/api/v1/analytics/student/me/recommendations` | Authenticated Student | Explainable rule-based recommendations |
| `GET` | `/api/v1/analytics/faculty/offerings/{offering_id}` | Assigned Faculty / Admin | Course section attendance & grade distribution |
| `GET` | `/api/v1/analytics/faculty/offerings/{offering_id}/attendance` | Assigned Faculty / Admin | Section attendance metrics & at-risk student list |
| `GET` | `/api/v1/analytics/faculty/offerings/{offering_id}/performance` | Assigned Faculty / Admin | Section assessment performance averages |
| `GET` | `/api/v1/analytics/admin/overview` | Admin | Institution-wide academic overview |
| `GET` | `/api/v1/analytics/admin/departments/{department_id}` | Admin | Department-level academic analytics |
| `GET` | `/api/v1/analytics/admin/programs/{program_id}` | Admin | Program-level academic analytics |

---

## 9. Known Limitations & Production Safety

- **Data Dependencies**: Analytics rely on actual records in `attendance_records` and `assessment_grades`. Sparse early-term database records trigger explicit `insufficient_data: true` responses.
- **No Predictive Grade Claims**: The engine does not guarantee future grades or pass/fail outcomes.
- **Stateless Analytics**: Analytics calculations run deterministically per query without introducing unvetted caching layers.
