# PawPal+ — Final UML Class Diagram

Paste the Mermaid code below into https://mermaid.live to render the diagram.

```mermaid
classDiagram
    direction TB

    class Frequency {
        <<enumeration>>
        ONCE
        DAILY
        WEEKLY
    }

    class TaskType {
        <<enumeration>>
        WALK
        FEEDING
        MEDICATION
        GROOMING
        ENRICHMENT
        OTHER
    }

    class Priority {
        <<enumeration>>
        HIGH
        MEDIUM
        LOW
    }

    class Task {
        +str name
        +TaskType task_type
        +int duration_minutes
        +Priority priority
        +str notes
        +bool completed
        +Frequency frequency
        +date|None due_date
        +mark_complete() Task|None
        +to_dict() dict
    }

    class Pet {
        +str name
        +str species
        +str breed
        +float age_years
        +list~Task~ tasks
        +add_task(task)
        +remove_task(name)
        +complete_task(name)
        +get_pending_tasks() list~Task~
        +filter_tasks(completed, task_type, priority) list~Task~
        +tasks_sorted_by_duration(ascending) list~Task~
        +tasks_sorted_by_priority() list~Task~
    }

    class Owner {
        +str name
        +int available_minutes
        +dict preferences
        +list~Pet~ pets
        +add_pet(pet)
        +remove_pet(name)
        +get_all_pending_tasks() list~tuple~
        +filter_tasks_by_pet(name) list~tuple~
        +total_task_minutes() int
    }

    class ScheduledTask {
        +Pet pet
        +Task task
        +int start_minute
        +end_minute() int
    }

    class Conflict {
        +ScheduledTask task_a
        +ScheduledTask task_b
        +__str__() str
    }

    class DailyPlan {
        +list~ScheduledTask~ scheduled
        +list~tuple~ skipped
        +list~Conflict~ conflicts
        +int total_minutes_used
        +summary() str
    }

    class Scheduler {
        +Owner owner
        +generate_plan() DailyPlan
        +explain_plan(plan) str
        +_sort_tasks(pairs) list
        +sort_scheduled_by_start(scheduled)$ list
        +sort_scheduled_by_duration(scheduled, ascending)$ list
        +filter_by_pet(scheduled, name)$ list
        +filter_by_priority(scheduled, priority)$ list
        +filter_by_type(scheduled, task_type)$ list
        +detect_conflicts(scheduled)$ list~Conflict~
    }

    %% Relationships
    Owner "1" --> "0..*" Pet : owns
    Pet "1" --> "0..*" Task : has
    Task --> Frequency : frequency
    Task --> TaskType : task_type
    Task --> Priority : priority
    Scheduler --> Owner : reads
    Scheduler ..> DailyPlan : produces
    DailyPlan "1" --> "0..*" ScheduledTask : scheduled
    DailyPlan "1" --> "0..*" Conflict : conflicts
    ScheduledTask --> Pet : pet
    ScheduledTask --> Task : task
    Conflict --> ScheduledTask : task_a
    Conflict --> ScheduledTask : task_b
```

## Changes from initial draft (Phase 1 → final)

| What changed | Why |
|---|---|
| `Task` gained `frequency: Frequency` and `due_date: date` | Recurring task support added in Phase 3 |
| `Task.mark_complete()` returns `Task \| None` instead of `None` | Returns a renewal instance for daily/weekly tasks |
| `Pet` gained `complete_task()`, `filter_tasks()`, `tasks_sorted_by_*()` | Sorting and filtering layer added in Phase 3 |
| `Owner` gained `get_all_pending_tasks()` and `filter_tasks_by_pet()` | Scheduler now queries Owner directly rather than accepting a separate pet list |
| `Scheduler.__init__` takes only `Owner` (not `Owner + Pet`) | Supports multi-pet owners naturally |
| `ScheduledTask` gained `pet: Pet` field | Needed to identify which pet owns each block in the schedule |
| `Conflict` dataclass added | Conflict detection result type, Phase 3 |
| `DailyPlan.conflicts` field added | Populated by `generate_plan()` after scheduling |
| All `Scheduler.sort_*/filter_*` methods are `@staticmethod` | They operate on plain lists and have no dependency on `self.owner` |
