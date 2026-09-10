# Database ER Diagram - Digital BE Project Log Book Management System

## Conceptual Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    AUTHENTICATION & USERS                                 │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  ┌──────────────┐       ┌──────────────────┐       ┌──────────────────┐                │
│  │     User     │       │ StudentProfile   │       │ FacultyProfile   │                │
│  ├──────────────┤       ├──────────────────┤       ├──────────────────┤                │
│  │ id (PK)      │◄──1:1─┤ user_id (FK→User)│       │ user_id (FK→User)│◄──1:1──┤       │
│  │ email        │       │ roll_number(UQ)  │       │ employee_id(UQ)  │       │       │
│  │ password     │       │ name             │       │ name             │       │       │
│  │ role         │       │ mobile           │       │ designation      │       │       │
│  │ is_active    │       │ exam_seat_number │       │ department(FK)   │       │       │
│  │ is_staff     │       │ photograph       │       │ specialization   │       │       │
│  │ date_joined  │       │ department(FK)   │       └──────────────────┘       │       │
│  │ last_login   │       │ academic_year(FK)│                                   │       │
│  └──────────────┘       │ enrollment_year  │                                   │       │
│                         └──────────────────┘                                   │       │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    ACADEMIC STRUCTURE                                    │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  ┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐            │
│  │   Department     │       │  AcademicYear    │       │    Semester      │            │
│  ├──────────────────┤       ├──────────────────┤       ├──────────────────┤            │
│  │ id (PK)          │       │ id (PK)          │       │ id (PK)          │            │
│  │ name             │       │ year_label       │       │ academic_year(FK)│            │
│  │ code (UQ)        │       │ start_date       │       │ number           │            │
│  │ is_active        │       │ end_date         │       │ name             │            │
│  └──────────────────┘       │ is_current       │       │ start_date       │            │
│                             └──────────────────┘       │ end_date         │            │
│                                                        └──────────────────┘            │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    PROJECT & GROUPS                                      │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  ┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐            │
│  │  ProjectGroup    │       │     Project      │       │   GroupMember    │            │
│  ├──────────────────┤       ├──────────────────┤       ├──────────────────┤            │
│  │ id (PK)          │◄──1:1─┤ group_id (FK→Grp)│       │ id (PK)          │            │
│  │ academic_year(FK)│       │ title            │       │ group_id (FK)    │            │
│  │ group_number(UQ) │       │ area/domain      │       │ student_id (FK)  │            │
│  │ department(FK)   │       │ description      │       │ is_leader        │            │
│  │ status           │       │ technology_stack │       │ joined_date      │            │
│  │ created_at       │       │ created_at       │       │ left_date        │            │
│  └──────────────────┘       │ updated_at       │       └──────────────────┘            │
│                             └──────────────────┘                                       │
│                                                                                         │
│  ┌──────────────────────────────┐       ┌──────────────────────────────┐               │
│  │  ProjectGuideAssignment      │       │   ReviewerAssignment         │               │
│  ├──────────────────────────────┤       ├──────────────────────────────┤               │
│  │ id (PK)                      │       │ id (PK)                      │               │
│  │ group_id (FK)                │       │ group_id (FK)                │               │
│  │ faculty_id (FK→Faculty)      │       │ faculty_id (FK→Faculty)      │               │
│  │ academic_year(FK)            │       │ review_number                │               │
│  │ assigned_date                │       │ assigned_date                │               │
│  │ is_active                    │       │ is_active                    │               │
│  └──────────────────────────────┘       └──────────────────────────────┘               │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    WORKFLOW ENGINE                                       │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  ┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐            │
│  │  ProjectStage    │       │  StageDependency │       │     Section      │            │
│  ├──────────────────┤       ├──────────────────┤       ├──────────────────┤            │
│  │ id (PK)          │◄──M:N─┤ id (PK)          │       │ id (PK)          │            │
│  │ academic_year(FK)│       │ stage_id (FK)    │       │ stage_id (FK)    │            │
│  │ name             │       │ depends_on(FK)   │       │ section_type     │            │
│  │ slug (UQ per AY) │       │ dependency_type  │       │ title            │            │
│  │ order            │       └──────────────────┘       │ description      │            │
│  │ stage_type       │                                  │ is_required      │            │
│  │ is_required      │                                  │ order            │            │
│  │ start_date       │                                  │ owner_role       │            │
│  │ due_date         │                                  │ data_schema      │            │
│  │ is_active        │                                  │ content (JSONB)  │            │
│  └──────────────────┘                                  │ status           │            │
│                                                        │ submitted_at     │            │
│                                                        │ approved_at      │            │
│                                                        │ approved_by(FK)  │            │
│                                                        │ version          │            │
│                                                        └──────────────────┘            │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    SUBMISSIONS & APPROVALS                              │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  ┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐            │
│  │   Submission     │       │ SubmissionVersion│       │    Approval      │            │
│  ├──────────────────┤       ├──────────────────┤       ├──────────────────┤            │
│  │ id (PK)          │◄──1:N─┤ id (PK)          │       │ id (PK)          │            │
│  │ section_id (FK)  │       │ submission_id(FK)│       │ submission_id(FK)│            │
│  │ group_id (FK)    │       │ version_number   │       │ approver_id (FK) │            │
│  │ submitted_by(FK) │       │ content (JSONB)  │       │ role             │            │
│  │ status           │       │ submitted_at     │       │ decision         │            │
│  │ content (JSONB)  │       │ submitted_by(FK) │       │ remark           │            │
│  │ submitted_at     │       │ review_remark    │       │ decided_at       │            │
│  │ reviewed_at      │       └──────────────────┘       └──────────────────┘            │
│  │ reviewed_by(FK)  │                                                                   │
│  │ version          │                                                                   │
│  └──────────────────┘                                                                   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    DOCUMENTS                                            │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  ┌──────────────────┐       ┌──────────────────┐                                       │
│  │    Document      │       │ DocumentVersion  │                                       │
│  ├──────────────────┤       ├──────────────────┤                                       │
│  │ id (PK)          │◄──1:N─┤ id (PK)          │                                       │
│  │ group_id (FK)    │       │ document_id (FK) │                                       │
│  │ doc_type         │       │ version_number   │                                       │
│  │ title            │       │ file_path        │                                       │
│  │ uploaded_by(FK)  │       │ file_size        │                                       │
│  │ stage_id (FK)    │       │ mime_type        │                                       │
│  │ status           │       │ uploaded_at      │                                       │
│  │ current_version  │       │ uploaded_by(FK)  │                                       │
│  │ remarks          │       └──────────────────┘                                       │
│  │ created_at       │                                                                   │
│  └──────────────────┘                                                                   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    REVIEWS & MARKS                                       │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  ┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐            │
│  │     Review       │       │  ReviewCriterion │       │      Mark        │            │
│  ├──────────────────┤       ├──────────────────┤       ├──────────────────┤            │
│  │ id (PK)          │◄──1:N─┤ id (PK)          │       │ id (PK)          │            │
│  │ group_id (FK)    │       │ review_id (FK)   │       │ criterion_id(FK) │            │
│  │ review_number    │       │ name             │       │ group_id (FK)    │            │
│  │ academic_year(FK)│       │ description      │       │ reviewer_id (FK) │            │
│  │ stage_id (FK)    │       │ max_marks        │       │ obtained_marks   │            │
│  │ review_date      │       │ weightage        │       │ remarks          │            │
│  │ status           │       │ co_id (FK)       │       │ status           │            │
│  │ total_max_marks  │       │ po_id (FK)       │       │ finalized_at     │            │
│  │ total_obtained   │       └──────────────────┘       │ finalized_by(FK) │            │
│  │ finalized_at     │                                  │ created_at       │            │
│  │ finalized_by(FK) │                                  │ updated_at       │            │
│  └──────────────────┘                                  └──────────────────┘            │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    CO/PO ATTAINMENT                                     │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  ┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐            │
│  │  CourseOutcome   │       │ ProgramOutcome   │       │   COPOMapping    │            │
│  ├──────────────────┤       ├──────────────────┤       ├──────────────────┤            │
│  │ id (PK)          │◄──M:N─┤ id (PK)          │◄──M:N─┤ id (PK)          │            │
│  │ code (UQ)        │       │ code (UQ)        │       │ co_id (FK→CO)    │            │
│  │ name             │       │ name             │       │ po_id (FK→PO)    │            │
│  │ description      │       │ description      │       │ weightage        │            │
│  │ department(FK)   │       │ department(FK)   │       │ created_at       │            │
│  │ academic_year(FK)│       │ academic_year(FK)│       └──────────────────┘            │
│  └──────────────────┘       └──────────────────┘                                       │
│                                                                                         │
│  ┌──────────────────────────────────┐                                                  │
│  │  COAttainment                    │                                                  │
│  ├──────────────────────────────────┤                                                  │
│  │ id (PK)                          │                                                  │
│  │ co_id (FK→CO)                    │                                                  │
│  │ group_id (FK)                    │                                                  │
│  │ review_id (FK)                   │                                                  │
│  │ raw_marks                        │                                                  │
│  │ normalized_marks                 │                                                  │
│  │ attainment_level                 │                                                  │
│  │ calculated_at                    │                                                  │
│  └──────────────────────────────────┘                                                  │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    NOTIFICATIONS & AUDIT                                │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  ┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐            │
│  │  Notification    │       │    AuditLog      │       │    Deadline      │            │
│  ├──────────────────┤       ├──────────────────┤       ├──────────────────┤            │
│  │ id (PK)          │       │ id (PK)          │       │ id (PK)          │            │
│  │ recipient_id(FK) │       │ actor_id (FK)    │       │ stage_id (FK)    │            │
│  │ notification_type│       │ actor_role       │       │ academic_year(FK)│            │
│  │ title            │       │ action           │       │ start_date       │            │
│  │ message          │       │ entity_type      │       │ due_date         │            │
│  │ related_type     │       │ entity_id        │       │ is_active        │            │
│  │ related_id       │       │ previous_value   │       └──────────────────┘            │
│  │ is_read          │       │ new_value        │                                       │
│  │ read_at          │       │ ip_address       │                                       │
│  │ created_at       │       │ user_agent       │                                       │
│  └──────────────────┘       │ timestamp        │                                       │
│                             └──────────────────┘                                       │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    FINAL LOGBOOK                                         │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  ┌──────────────────┐                                                                   │
│  │  FinalLogBook    │                                                                   │
│  ├──────────────────┤                                                                   │
│  │ id (PK)          │                                                                   │
│  │ group_id (FK)    │                                                                   │
│  │ academic_year(FK)│                                                                   │
│  │ status           │                                                                   │
│  │ generated_at     │                                                                   │
│  │ generated_by(FK) │                                                                   │
│  │ pdf_path         │                                                                   │
│  │ version          │                                                                   │
│  │ remarks          │                                                                   │
│  └──────────────────┘                                                                   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

## Relationship Summary

| Relationship | Type | Description |
|---|---|---|
| User → StudentProfile | 1:1 | One user has one student profile |
| User → FacultyProfile | 1:1 | One user has one faculty profile |
| AcademicYear → Semester | 1:N | One year has multiple semesters |
| ProjectGroup → Project | 1:1 | One group has one project |
| ProjectGroup → GroupMember | 1:N | One group has multiple members |
| Student → GroupMember | 1:N | One student can be in multiple groups (different years) |
| ProjectGroup → ProjectGuideAssignment | 1:N | Multiple guides can be assigned |
| ProjectGroup → ReviewerAssignment | 1:N | Multiple reviewers assigned per review |
| ProjectGroup → Section | 1:N | Multiple sections per group |
| ProjectStage → StageDependency | 1:N | Dependencies between stages |
| Section → Submission | 1:N | Multiple submissions per section |
| Submission → SubmissionVersion | 1:N | Version history preserved |
| Submission → Approval | 1:N | Multiple approvals possible |
| ProjectGroup → Document | 1:N | Documents per group |
| Document → DocumentVersion | 1:N | Version history preserved |
| ProjectGroup → Review | 1:N | Reviews per group |
| Review → ReviewCriterion | 1:N | Criteria per review |
| ReviewCriterion → Mark | 1:N | Marks per criterion per group |
| CO → COPOMapping | 1:N | CO mapped to multiple POs |
| PO → COPOMapping | 1:N | PO mapped to multiple COs |
| ReviewCriterion → COAttainment | 1:N | Attainment calculated per criterion |
| User → Notification | 1:N | Notifications per user |
| User → AuditLog | 1:N | Audit entries per actor |
| AcademicYear → Deadline | 1:N | Deadlines per year |
| ProjectGroup → FinalLogBook | 1:1 | Final logbook per group |

## Key Constraints

1. **Unique Constraints**: 
   - User.email, StudentProfile.roll_number, FacultyProfile.employee_id
   - AcademicYear.year_label (per department)
   - ProjectGroup(academic_year, group_number, department) - unique group per year
   - COPOMapping(co_id, po_id) - unique mapping

2. **Soft Delete**: All major entities use `is_active`/`status` flags, never hard delete

3. **Audit Trail**: AuditLog is append-only, no updates/deletes allowed

4. **JSONB Usage**: Section.content and Submission.content use JSONB for flexible logbook data, but structured data (marks, reviews, approvals) uses proper relational tables
