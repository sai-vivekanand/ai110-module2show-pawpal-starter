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

## Testing PawPal+

Run the full test suite with:

```bash
python -m pytest
```

Or with verbose output to see each test name:

```bash
python -m pytest -v
```

### What the tests cover

| Class | Tests | Behaviours verified |
|-------|-------|---------------------|
| `Task` | 6 | `mark_complete()` flips status; one-time tasks return `None`; daily/weekly tasks return a renewal with the correct next `due_date`; `to_dict()` includes all fields |
| `Pet` | 10 | `add_task` / `remove_task` / `get_pending_tasks`; `complete_task()` auto-appends the renewal for recurring tasks only; `tasks_sorted_by_duration/priority()` are non-destructive and preserve all tasks; `filter_tasks()` by completion and priority |
| `Owner` | 5 | `add_pet` / `remove_pet`; `total_task_minutes()` sums pending tasks and excludes completed ones; `filter_tasks_by_pet()` case-insensitive match |
| `Scheduler` | 9 | Priority ordering in generated plan; tasks over budget go to `skipped`; `total_minutes_used` never exceeds budget; empty-owner edge case; `sort_scheduled_by_start/duration()`; `filter_by_pet/priority()`; conflict detection for overlapping, back-to-back, same-start, and multi-way overlaps |
| Edge Cases | 20 | Pet / owner with no tasks; exact-fit and one-minute-over budget; sort stability and non-destructiveness; `start_minute` ascending in generated plan; `end_minute` arithmetic; recurrence without `due_date` falls back to today; renewal inherits all core fields; conflict detection with 0, 1, and 3 tasks; filter returning empty list |

**Total: 54 tests — all passing.**

### Confidence level: ★★★★☆

The scheduler's core logic (greedy sort, time-budget enforcement, recurrence, conflict detection) is fully covered by automated tests. The remaining uncertainty is around the Streamlit UI layer, which is not unit-tested, and future edge cases like tasks spanning midnight or a pet owned by multiple users.

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
