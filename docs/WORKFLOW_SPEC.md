# Workflow Engine Specification

## State Machine

```
┌──────────┐    submit    ┌──────────────┐    faculty review   ┌──────────────┐
│  DRAFT   │───────────►│  SUBMITTED   │──────────────────►│UNDER_REVIEW  │
│          │            │              │                    │              │
└──────────┘            └──────────────┘                    └──────────────┘
       ▲                                                │         │
       │         ┌──────────────┐                        │         │
       │         │ CHANGES_REQ  │◄───────────────────────┘         │
       └─────────┤              │    change request                  │
                 └──────────────┘                        │
                       │                         ┌────────▼────────┐
                       │  resubmit               │                 │
                       └────────────────────────►│ RESUBMITTED     │
                                                 │                 │
                                                 └─────────────────┘
       ┌──────────────┐    approve      ┌──────────────┐
       │  APPROVED    │────────────────►│   LOCKED     │
       │              │                 │              │
       └──────────────┘                 └──────────────┘

       ┌──────────────┐    timeout    ┌──────────────┐
       │  OVERDUE     │──────────────►│   CANCELLED  │
       └──────────────┘               └──────────────┘
```

## Stage States

| State | Description | Allowed Actions |
|-------|-------------|-----------------|
| DRAFT | Initial state, editable by owner | Edit, Save, Submit |
| SUBMITTED | Submitted to faculty for review | View, Faculty can review |
| UNDER_REVIEW | Being reviewed by faculty/reviewer | Faculty can add remarks, approve, request changes |
| CHANGES_REQUIRED | Reviewer requested modifications | Student can resubmit |
| RESUBMITTED | Student resubmitted after change request | Goes back to UNDER_REVIEW |
| APPROVED | All review criteria met | Stage unlocks for next dependent stage |
| LOCKED | Finalized, no edits allowed | View only |
| OVERDUE | Past deadline | HOD monitoring, escalation |
| CANCELLED | Explicitly cancelled by authorized role | View only, audit trail |

## Workflow Rules

1. **State Transitions**: Every transition must be validated by the backend state machine
2. **Stage Dependencies**: A stage unlocks only when ALL dependent stages are APPROVED or LOCKED
3. **Approval Gate**: Transition SUBMITTED → UNDER_REVIEW requires at least one submission record
4. **Lock Rule**: APPROVED → LOCKED transition is automatic after configurable delay or manual lock
5. **Deadline Enforcement**: Overdue status is calculated by comparing due_date with current time
6. **No Skip**: Stages must be completed in order; no skipping forward

## Transition Validation

```
DRAFT → SUBMITTED:    Valid if content exists, deadline not passed
SUBMITTED → UNDER_REVIEW: Valid if faculty assigned, submission exists
UNDER_REVIEW → APPROVED: Valid if all criteria reviewed, marks entered, reviewer is assigned
UNDER_REVIEW → CHANGES_REQUIRED: Valid if reviewer is assigned to group
CHANGES_REQUIRED → RESUBMITTED: Valid if student resubmits
RESUBMITTED → UNDER_REVIEW: Automatic transition
ANY → OVERDUE: Automatic, based on due_date
ANY → CANCELLED: HOD only
APPROVED → LOCKED: Automatic or HOD manual lock
```

## Concurrency Handling

- Use `select_for_update()` in database transactions for state transitions
- Optimistic locking with version field on Submission
- Prevent two faculty members from approving simultaneously
- Handle race conditions during stage unlocking

## Stage Configuration

HOD can configure stages per AcademicYear:
- stage_name, slug, order, is_required, start_date, due_date
- Each stage has configurable dependencies
- Default 18-stage sequence provided as seed data

## Stage Unlocking Logic

```
function canUnlockStage(stage, group):
    if stage.dependencies is empty:
        return True
    for dep in stage.dependencies:
        dep_submission = Submission.objects.filter(section__stage=dep, group=group).latest()
        if dep_submission.status not in [APPROVED, LOCKED]:
            return False
    return True
```
