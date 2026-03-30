# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

### Core User Actions

1. **Add / manage a pet and owner profile** — The user enters their own name and how many minutes they have available each day, then registers a pet with a name, species, breed, and age. This data drives every scheduling decision.

2. **Add and edit care tasks** — The user creates tasks such as walks, feeding, medication, grooming, or enrichment. Each task has a name, a type, an estimated duration (minutes), and a priority level (high / medium / low). Tasks can be edited or removed at any time.

3. **Generate and view today's daily care plan** — The user asks the system to produce a schedule. The Scheduler fits as many tasks as possible into the owner's available time window, orders them by priority, and returns a readable plan that explains which tasks were included and why any were skipped.

### Classes and Responsibilities

| Class | Responsibility |
|-------|----------------|
| `Owner` | Stores the owner's name and daily time budget; acts as the entry point for the system |
| `Pet` | Stores the pet's profile (name, species, breed, age); linked to an Owner |
| `Task` | Dataclass holding a single care task (type, duration, priority); pure data, no logic |
| `Scheduler` | Accepts an Owner, a Pet, and a list of Tasks; applies constraints and priority rules to produce a sorted, time-bounded daily plan |

**b. Design changes**

After reviewing the skeleton, one notable gap surfaced: there was no explicit `reason` field on skipped tasks. The first draft of `DailyPlan` only had a `skipped: list[Task]` list, so users couldn't tell *why* a task was omitted (time budget exceeded vs. user preference). This was addressed by adding a `ScheduledTask` wrapper dataclass that carries a `start_minute`, and by having `explain_plan()` in `Scheduler` generate per-task reasoning strings — keeping the explanation logic in one place rather than leaking it into the UI layer.

A secondary observation: `Owner.total_task_minutes()` could be ambiguous if a pet is shared between owners in future. For this single-owner scenario the method is fine, but it was noted as a potential bottleneck if the data model ever expands.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers two hard constraints: the owner's **daily time budget** (`available_minutes`) and task **priority level** (HIGH → MEDIUM → LOW). Within the same priority tier, **shorter tasks are scheduled first** — this is a shortest-job-first tiebreak that maximises the number of completed tasks when time is tight.

Priority was chosen as the dominant constraint because a pet owner's primary concern is that high-stakes tasks (medication, feeding) always happen before enrichment or grooming. Time budget is the only other hard constraint; everything else (pet preference, notes) is metadata that influences *what* tasks exist, not *whether* they fit.

**b. Tradeoffs**

The scheduler uses **exact sequential block assignment** — each task is placed immediately after the previous one with no gaps, and the "does it fit?" check compares only `task.duration_minutes <= remaining_budget`. This means:

- **It does not detect overlaps in the generated plan** (the greedy cursor guarantees sequential placement, so overlaps are structurally impossible from `generate_plan()`).
- **Conflict detection is a separate utility** that operates on *any* list of `ScheduledTask` objects. This is useful when tasks are imported or manually placed at fixed times in the future.
- **It cannot partially schedule a task** — if "Morning walk (30 min)" doesn't fit in the 15 remaining minutes, it is skipped entirely rather than shortened.

This tradeoff is reasonable because pet care tasks are largely atomic (you can't do half a walk) and because the greedy approach is easy to reason about and test. A more complex constraint-satisfaction approach would add code complexity for marginal benefit in a single-owner app.

---

## 3. AI Collaboration

**a. How you used AI**

AI was used at every phase of the project, but in different modes depending on the task:

- **Design brainstorming (Phase 1):** Used AI to generate a Mermaid.js UML diagram from a natural-language description of the four classes. The prompt "I am designing a pet care app with Owner, Pet, Task, and Scheduler classes — generate a Mermaid class diagram with the attributes and methods I described" was highly effective because it was concrete and gave the AI a clear scope.

- **Skeleton generation (Phase 1–2):** Used AI with `#file:pawpal_system.py` to generate Python dataclass stubs. Giving the AI the existing file as context ("based on this skeleton, generate the full implementation") produced much better output than asking from scratch — the AI respected the existing naming conventions and structure.

- **Algorithm suggestion (Phase 3):** Asked "what are lightweight ways to detect scheduling conflicts without raising exceptions?" — the suggestion of returning a list of warning objects rather than throwing was exactly the right approach and informed the `Conflict` dataclass design.

- **Test generation (Phase 4–5):** Used AI to draft edge-case test ideas by asking "what are the most important boundary conditions for a greedy scheduler with recurring tasks?" The AI suggested the exact-fit budget boundary, the back-to-back non-conflict case, and the three-way overlap test — all of which caught real design assumptions.

- **Refactoring review (Phase 5):** Used AI to review `detect_conflicts()` and asked if it could be simplified. The AI suggested a one-liner using `itertools.combinations`. The simpler version was correct but harder to read for a student audience, so the explicit nested loop was kept (see 3b below).

The most productive prompts were **contextual** (referencing the actual file), **scoped** (one question per prompt), and **outcome-oriented** ("suggest a way to…" rather than "explain how to…").

**b. Judgment and verification**

The clearest case of rejecting an AI suggestion was around `detect_conflicts()`. The AI proposed:

```python
from itertools import combinations
conflicts = [
    Conflict(a, b)
    for a, b in combinations(scheduled, 2)
    if a.start_minute < b.end_minute and b.start_minute < a.end_minute
]
```

This is correct and more "Pythonic." However, the explicit nested-loop version was kept because:
1. It is easier to read and debug for anyone new to Python.
2. The `combinations` version obscures *why* we're iterating all pairs — a future maintainer would need to know what `combinations(scheduled, 2)` produces.
3. The test `test_multiple_conflicts_all_reported` verifies the behaviour independently of the implementation, so either version passes. The choice is purely about readability.

The decision was verified by running both implementations against the full test suite — both passed — confirming it was a style choice, not a correctness issue.

Using **separate chat sessions** for each phase (design, implementation, testing) was critical for staying organised. A single long chat session tends to drift: earlier context gets summarised away, and the AI starts blending concerns from different phases. Starting fresh for each phase kept the AI's output focused on the current task without contamination from earlier discussions.

---

## 4. Testing and Verification

**a. What you tested**

The 54-test suite covers five categories:

1. **Task lifecycle** — `mark_complete()` correctly flips `completed`, returns a renewal for recurring frequencies, and returns `None` for one-time tasks. `to_dict()` serialises all fields. These tests matter because the renewal chain is the core of the recurring-task feature; a silent failure here would mean tasks disappear after one completion.

2. **Pet task management** — add, remove, pending filter, sorting, filtering by attribute, and the `complete_task()` renewal path. Important because `Pet` is the primary container that the Streamlit UI reads from; any mutation bug here would corrupt the displayed task list.

3. **Owner aggregation** — `total_task_minutes()` sums pending tasks across all pets and excludes completed ones. This drives the budget progress bar; an off-by-one here would mislead the owner about how much time they're committing.

4. **Scheduler correctness** — priority ordering, budget enforcement, exact-fit/one-over-budget boundary, and empty-owner case. These are the scheduler's invariants: any violation means tasks are dropped silently or the budget is exceeded.

5. **Conflict detection** — back-to-back (no conflict), same-start (conflict), three-way overlap (all three pairs reported), single task, empty list. Conflict detection is a safety feature; it should never produce false positives (back-to-back tasks are fine) or miss real overlaps (same-start is a real conflict).

**b. Confidence**

Confidence: **4 out of 5.**

The scheduling logic is well-covered and all 54 tests pass. The main sources of remaining uncertainty are:

- **Streamlit UI**: The UI layer is not unit-tested. A bug in how `pet.complete_task()` is called from the ✓ button (e.g., passing the wrong task name) would only be caught by manual testing.
- **Multi-day scenarios**: The scheduler is stateless — it only considers tasks whose `due_date` is today or `None`. If a weekly task was completed three days ago, there is no logic to check whether it's due again today vs. tomorrow.
- **Very large task lists**: The O(n²) conflict detector is correct but untested beyond ~10 tasks. At hundreds of tasks it would be slow.

Next edge cases to test if time permitted: tasks with `due_date` in the past (should they still be scheduled?), a pet removed mid-session while its tasks are still in the plan, and concurrent modification of the session state from two browser tabs.

---

## 5. Reflection

**a. What went well**

The cleanest part of the project is the separation between the logic layer (`pawpal_system.py`) and the UI (`app.py`). Because all scheduling decisions live in `Scheduler`, `Pet`, and `Task`, the Streamlit file never contains any business logic — it only reads from and writes to the session-state `Owner` object. This made testing straightforward (pytest never needs to import Streamlit) and made the UI easy to update without touching the core algorithms.

The recurring-task design worked out particularly well. The decision to have `Task.mark_complete()` *return* the next instance (rather than mutate a list in place) keeps the `Task` class stateless and makes the renewal behaviour easy to test in one line: `assert next_task.due_date == today + timedelta(days=1)`.

**b. What you would improve**

The biggest limitation is that the scheduler has no concept of *time of day*. All tasks are placed sequentially starting at minute 0, which means "Morning walk" and "Evening feeding" both get scheduled at 00:00 if run at the same time. A real improvement would be to let each task carry an optional `preferred_start_hour`, and to have the scheduler respect that preference when assigning `start_minute`.

A second improvement would be replacing `st.table()` (static) with `st.dataframe()` with column sorting enabled, so users can reorder the schedule interactively without rebuilding the plan.

**c. Key takeaway**

The most important lesson from this project is that **AI tools are most valuable when you already have a clear design**. When the UML was complete and the class stubs existed, AI-generated code was 80–90% correct and needed only minor adjustments. When prompts were vague ("write a scheduler"), the output required heavy rewriting. The human's job is to be the architect — defining the structure, the contracts between classes, and the invariants the system must uphold — and then using AI to fill in the implementation details within that structure. Reversing this order (letting AI design and then trying to correct it) produces code that works but doesn't reflect the design you actually want.
