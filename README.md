# PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit app that helps a busy pet owner plan daily care tasks across multiple pets — prioritising high-stakes tasks, handling recurring schedules, and warning about conflicts.

---

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

---

## Features

| Feature | Description |
|---------|-------------|
| **Owner & multi-pet management** | Register an owner with a daily time budget; add/remove multiple pets |
| **Task creation** | Each task has a name, type, duration, priority (high/medium/low), optional notes, and a frequency |
| **Priority-aware scheduling** | Greedy scheduler sorts HIGH → MEDIUM → LOW; shorter tasks break ties within each tier to maximise the number of tasks that fit |
| **Sorting views** | Task list can be sorted by priority or duration (shortest/longest first) in both the task manager and the generated plan |
| **Filtering** | Filter the plan by pet name; filter task lists by completion status, priority, or task type |
| **Recurring tasks** | Mark a DAILY or WEEKLY task complete and a new instance is automatically scheduled for the next occurrence (`due_date + 1 day` or `+ 7 days`) |
| **Conflict detection** | After scheduling, an O(n²) overlap check flags any tasks whose time windows intersect — shown as `st.error`/`st.warning` banners in the UI |
| **Budget progress bar** | Visual indicator shows what fraction of the daily budget is consumed by pending tasks |
| **Scheduling explanation** | Expandable panel explains why each task was included or skipped |

---

## Smarter Scheduling

PawPal+ includes several algorithms that make the scheduler more intelligent:

| Algorithm | Where | How it works |
|-----------|-------|--------------|
| **Priority sort** | `Scheduler._sort_tasks()` | `sorted()` with key `(PRIORITY_ORDER[priority], duration_minutes)` |
| **Sort by duration** | `Pet.tasks_sorted_by_duration()`, `Scheduler.sort_scheduled_by_duration()` | `sorted()` with `lambda t: t.duration_minutes`, ascending or descending |
| **Filter by pet / priority / type** | `Owner.filter_tasks_by_pet()`, `Scheduler.filter_by_*()`, `Pet.filter_tasks()` | List comprehensions on one attribute at a time |
| **Recurring tasks** | `Task.mark_complete()` → `Pet.complete_task()` | Returns a new `Task` with `due_date = today + timedelta(days=1 or 7)`; `Pet.complete_task()` appends it automatically |
| **Conflict detection** | `Scheduler.detect_conflicts()` | Pairwise overlap: A and B conflict when `A.start < B.end and B.start < A.end`. Returns `Conflict` objects with readable warning strings |

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

### Run the terminal demo

```bash
python main.py
```

---

## Testing PawPal+

Run the full test suite with:

```bash
python -m pytest
```

Verbose output (shows each test name):

```bash
python -m pytest -v
```

### What the tests cover

| Class | Tests | Behaviours verified |
|-------|-------|---------------------|
| `Task` | 6 | `mark_complete()` flips status; one-time → `None`; daily/weekly → renewal with correct `due_date`; `to_dict()` completeness |
| `Pet` | 10 | Add/remove/pending; `complete_task()` auto-renews recurring tasks only; sort non-destructiveness; `filter_tasks()` by completion and priority |
| `Owner` | 5 | Add/remove pet; `total_task_minutes()` sums pending, excludes completed; `filter_tasks_by_pet()` case-insensitive |
| `Scheduler` | 9 | Priority order; budget enforcement; `total_minutes_used ≤ budget`; empty owner; plan sort/filter utilities; conflict detection variants |
| `TestEdgeCases` | 20 | Pet/owner with no tasks; exact-fit and +1-minute-over budget; sort stability & non-destructiveness; `start_minute` ascending; `end_minute` arithmetic; recurrence without `due_date`; field inheritance; same-start conflict; back-to-back non-conflict; three-way overlap; empty/single-task detect; case-insensitive filter |

**Total: 54 tests — all passing.**

### Confidence level: ★★★★☆

Core scheduling logic (greedy sort, time-budget enforcement, recurrence, conflict detection) is fully covered. Remaining uncertainty: Streamlit UI layer is not unit-tested, and future edge cases like tasks spanning midnight or multiple owners sharing a pet are not yet handled.

---

## System Architecture

See [uml_final.md](uml_final.md) for the final Mermaid.js class diagram and a table of changes from the initial draft.

---

## Project structure

```
pawpal_system.py   # All logic: Owner, Pet, Task, Scheduler, DailyPlan, Conflict
app.py             # Streamlit UI — imports from pawpal_system
main.py            # Terminal demo script
tests/
  test_pawpal.py   # 54 automated tests
uml_final.md       # Final Mermaid UML diagram + change log
reflection.md      # Design and AI-collaboration reflection
```

---

## Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## DEMO

<img width="897" height="759" alt="image" src="https://github.com/user-attachments/assets/3aef1433-5ef1-4a54-94a0-c6663104e5d5" />
<img width="867" height="714" alt="image" src="https://github.com/user-attachments/assets/26a68e34-d66e-45b1-a88e-789192709db7" />
