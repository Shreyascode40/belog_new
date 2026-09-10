# API Endpoint Specification

## Base URL
```
/api/v1/
```

## Authentication
```
/api/v1/auth/register/           POST
/api/v1/auth/login/              POST
/api/v1/auth/logout/             POST
/api/v1/auth/token/refresh/      POST
/api/v1/auth/profile/            GET, PUT
```

## Users
```
/api/v1/users/                   GET (HOD/Admin), POST (HOD/Admin)
/api/v1/users/{id}/              GET, PUT, DELETE (HOD/Admin)
/api/v1/users/{id}/deactivate/   POST (HOD/Admin)
/api/v1/users/me/                GET (All authenticated)
```

## Students
```
/api/v1/students/                GET (HOD/Admin), POST (HOD/Admin)
/api/v1/students/{id}/           GET, PUT (HOD/Admin, self)
/api/v1/students/me/             GET (Student)
/api/v1/students/me/profile/     GET, PUT (Student)
```

## Faculty
```
/api/v1/faculty/                 GET (HOD/Admin), POST (HOD/Admin)
/api/v1/faculty/{id}/            GET, PUT (HOD/Admin)
/api/v1/faculty/me/              GET (Faculty)
```

## Academic Years
```
/api/v1/academic-years/          GET, POST (HOD/Admin)
/api/v1/academic-years/{id}/     GET, PUT, DELETE (HOD/Admin)
```

## Project Groups
```
/api/v1/groups/                  GET, POST (HOD/Admin)
/api/v1/groups/{id}/             GET, PUT, DELETE (HOD/Admin)
/api/v1/groups/{id}/members/     GET, POST (HOD/Admin)
/api/v1/groups/{id}/members/{student_id}/  DELETE (HOD/Admin)
/api/v1/groups/{id}/guide/       POST (HOD/Admin)
/api/v1/groups/{id}/reviewers/   POST (HOD/Admin)
```

## Projects
```
/api/v1/projects/                GET, POST (HOD/Admin)
/api/v1/projects/{id}/           GET, PUT, DELETE (HOD/Admin)
/api/v1/projects/areas/          GET (all project areas)
```

## Stages
```
/api/v1/stages/                  GET, POST (HOD/Admin)
/api/v1/stages/{id}/             GET, PUT, DELETE (HOD/Admin)
/api/v1/stages/order/            PUT (HOD/Admin - reorder)
/api/v1/stages/{id}/unlock/      POST (Workflow Service)
```

## Submissions
```
/api/v1/submissions/             GET, POST (HOD/Admin, Student)
/api/v1/submissions/{id}/        GET, PUT (HOD/Admin, Student)
/api/v1/submissions/{id}/approve/ POST (Faculty/Reviewer)
/api/v1/submissions/{id}/request-changes/ POST (Faculty/Reviewer)
/api/v1/submissions/{id}/resubmit/ POST (Student)
/api/v1/submissions/{id}/versions/ GET (HOD/Admin)
/api/v1/submissions/group/{groupId}/  GET (HOD/Admin, Faculty, Reviewer)
```

## Documents
```
/api/v1/documents/               GET, POST (HOD/Admin, Student, Faculty)
/api/v1/documents/{id}/          GET, PUT, DELETE (Owner, HOD/Admin)
/api/v1/documents/{id}/versions/ GET (Owner, HOD/Admin)
/api/v1/documents/{id}/download/ GET (Authenticated)
```

## Reviews
```
/api/v1/reviews/                 GET, POST (HOD/Admin, Faculty, Reviewer)
/api/v1/reviews/{id}/            GET, PUT (Assigned faculty/reviewer)
/api/v1/reviews/{id}/criteria/   GET, POST (Assigned faculty/reviewer)
/api/v1/reviews/{id}/marks/      GET, POST (Assigned faculty/reviewer)
/api/v1/reviews/{id}/finalize/   POST (HOD/Admin, Faculty - authorized)
/api/v1/reviews/group/{groupId}/ GET (Faculty, HOD/Admin)
```

## Rubrics
```
/api/v1/rubrics/                 GET, POST (HOD/Admin)
/api/v1/rubrics/{id}/            GET, PUT, DELETE (HOD/Admin)
/api/v1/rubrics/{id}/criteria/   GET, POST (HOD/Admin)
```

## CO/PO
```
/api/v1/co-po/cos/               GET, POST (HOD/Admin)
/api/v1/co-po/po/                GET, POST (HOD/Admin)
/api/v1/co-po/mappings/          GET, POST (HOD/Admin)
/api/v1/co-po/mappings/{id}/     GET, PUT, DELETE (HOD/Admin)
/api/v1/co-po/attainment/        GET (HOD/Admin)
/api/v1/co-po/attainment/{id}/   GET (HOD/Admin)
/api/v1/co-po/calculate/         POST (HOD/Admin)
```

## Approvals
```
/api/v1/approvals/               GET (HOD/Admin)
/api/v1/approvals/{id}/          GET (HOD/Admin)
```

## Notifications
```
/api/v1/notifications/           GET (Authenticated)
/api/v1/notifications/{id}/read/ POST (Authenticated)
/api/v1/notifications/mark-all-read/ POST (Authenticated)
```

## Audit
```
/api/v1/audit/                   GET (HOD/Admin)
/api/v1/audit/{id}/              GET (HOD/Admin)
```

## Dashboard
```
/api/v1/dashboard/student/       GET (Student)
/api/v1/dashboard/faculty/       GET (Faculty)
/api/v1/dashboard/hod/           GET (HOD/Admin)
/api/v1/dashboard/reviewer/      GET (Faculty with reviewer role)
```

## Reports
```
/api/v1/reports/progress/        GET (HOD/Admin)
/api/v1/reports/faculty-workload/GET (HOD/Admin)
/api/v1/reports/overdue/         GET (HOD/Admin)
/api/v1/reports/marks/           GET (HOD/Admin)
/api/v1/reports/co-attainment/   GET (HOD/Admin)
/api/v1/reports/export/          GET (HOD/Admin, CSV/Excel/PDF)
```

## Logbook
```
/api/v1/logbook/generate/        POST (HOD/Admin)
/api/v1/logbook/{id}/            GET (HOD/Admin)
/api/v1/logbook/{id}/pdf/        GET (HOD/Admin)
```

## Response Format
```json
// Success
{
  "success": true,
  "data": {},
  "message": "Operation successful"
}

// Paginated
{
  "success": true,
  "data": [],
  "count": 100,
  "next": "/api/v1/...",
  "previous": null
}

// Error
{
  "success": false,
  "message": "Operation failed",
  "errors": {
    "field": ["Error message"]
  }
}
```

## Error Codes
| Code | Meaning |
|------|---------|
| 400 | Validation error |
| 401 | Authentication required |
| 403 | Permission denied |
| 404 | Resource not found |
| 409 | Conflict (duplicate, state mismatch) |
| 423 | Locked (resource locked) |
| 429 | Rate limit exceeded |
```

## Role-Permission Matrix

| Endpoint Pattern | Student | Faculty | Reviewer | HOD/Admin |
|-----------------|---------|---------|----------|-----------|
| Auth/* | R/W | R/W | R/W | R/W |
| Users/* | - | - | - | CRUD |
| Students/* | self GET/PUT | - | - | CRUD |
| Faculty/* | - | - | - | CRUD |
| AcademicYears/* | - | - | - | CRUD |
| Groups/* | view own | view assigned | view assigned | CRUD |
| Groups/{id}/members | - | - | - | CRUD |
| Groups/{id}/guide | - | - | - | CRUD |
| Groups/{id}/reviewers | - | - | - | CRUD |
| Projects/* | - | - | - | CRUD |
| Stages/* | view | view | view | CRUD |
| Submissions/* | own CRUD | assigned review | assigned review | CRUD |
| Submissions/{id}/approve | - | own | own | - |
| Documents/* | own CRUD | own groups | own groups | CRUD |
| Reviews/* | - | assigned | assigned | CRUD |
| Reviews/{id}/marks | - | assigned | assigned | - |
| Reviews/{id}/finalize | - | own | own | - |
| CO/PO/* | - | - | - | CRUD |
| Notifications/* | own | own | own | own |
| Audit/* | - | - | - | R |
| Dashboard/student | own | - | - | - |
| Dashboard/faculty | - | own | - | - |
| Dashboard/reviewer | - | - | own | - |
| Dashboard/hod | - | - | - | own |
| Reports/* | - | - | - | R |
| Logbook/* | download | - | - | CRUD |

CRUD = Create, Read, Update, Delete
R = Read only
own = Only records related to authenticated user
- = Not allowed
```

## CO/PO Attainment Calculation Specification

### Marking Scheme (as per official BE project rubric)

**Criteria and Weightage:**
| Criterion | Max Marks | Weightage |
|-----------|-----------|-----------|
| Project Management | 10 | 10% |
| Problem Analysis | 10 | 10% |
| Design | 15 | 15% |
| Implementation | 20 | 20% |
| Testing & Verification | 10 | 10% |
| Project Report | 15 | 15% |
| Presentation | 10 | 10% |
| Innovation/Contribution | 10 | 10% |
| **Total** | **100** | **100%** |

### CO Attainment Calculation

```
For each CO:
  raw_marks = sum of marks obtained in criteria mapped to that CO
  max_marks = sum of max marks in criteria mapped to that CO
  normalized_marks = (raw_marks / max_marks) * 100
  attainment_level = based on normalized_marks:
    90-100: EXCELLENT
    80-89:  GOOD
    70-79:  SATISFACTORY
    60-69:  NEEDS IMPROVEMENT
    <60:    UNSATISFACTORY
```

### PO Attainment Calculation

```
For each PO:
  po_cos = all COs mapped to that PO
  For each CO in po_coos:
    co_attainment = COAttainment for that CO
  po_attainment = weighted average of CO attainments for that PO
```

### Formula Verification
- Raw marks cannot exceed max marks per criterion
- Required criteria must have marks entered before finalization
- Empty criteria are excluded from calculation
- Negative marks are rejected
- At least one CO and one PO must exist per academic year
- CO/PO mappings must be bi-directional (each CO has at least one PO, each PO has at least one CO)

### Edge Cases
- If no criteria map to a CO: CO attainment = 0, level = UNSATISFACTORY
- If all marks are 0: attainment = 0
- If a review is in DRAFT status: marks are not included in CO/PO calculation
- Only FINALIZED reviews contribute to final CO/PO attainment
