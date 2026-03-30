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

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
