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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
