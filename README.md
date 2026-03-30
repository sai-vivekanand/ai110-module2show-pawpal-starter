# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smarter Scheduling

PawPal+ includes several algorithms that make the scheduler more intelligent:

| Feature | Where | How it works |
|---------|-------|--------------|
| **Priority sort** | `Scheduler._sort_tasks()` | Tasks sorted HIGH → MEDIUM → LOW; shorter tasks break ties within the same priority so more tasks fit in the budget |
| **Sort by duration** | `Pet.tasks_sorted_by_duration()`, `Scheduler.sort_scheduled_by_duration()` | `sorted()` with a `lambda t: t.duration_minutes` key, ascending or descending |
| **Filter by pet / priority / type** | `Owner.filter_tasks_by_pet()`, `Scheduler.filter_by_pet/priority/type()`, `Pet.filter_tasks()` | List comprehensions that narrow results by one attribute at a time |
| **Recurring tasks** | `Task.mark_complete()` → `Pet.complete_task()` | When a `DAILY` or `WEEKLY` task is marked done, `mark_complete()` returns a fresh `Task` with `due_date = today + timedelta(days=1 or 7)`; `Pet.complete_task()` appends it automatically |
| **Conflict detection** | `Scheduler.detect_conflicts()` | O(n²) pairwise overlap check: tasks A and B conflict when `A.start < B.end and B.start < A.end`. Returns `Conflict` objects with human-readable warning strings rather than raising exceptions |

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
