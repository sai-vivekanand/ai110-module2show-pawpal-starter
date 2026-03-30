"""
PawPal+ — logic layer
All backend classes live here; UI (app.py) imports from this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TaskType(str, Enum):
    WALK = "walk"
    FEEDING = "feeding"
    MEDICATION = "medication"
    GROOMING = "grooming"
    ENRICHMENT = "enrichment"
    OTHER = "other"


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ---------------------------------------------------------------------------
# Data classes (pure data, no scheduling logic)
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet-care task."""

    name: str
    task_type: TaskType
    duration_minutes: int          # estimated time needed
    priority: Priority
    notes: str = ""
    completed: bool = False

    def mark_complete(self) -> None:
        """Set completed to True, indicating the task has been done."""
        self.completed = True

    def to_dict(self) -> dict:
        """Return a plain dict representation suitable for JSON export or Streamlit state."""
        return {
            "name": self.name,
            "task_type": self.task_type.value,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority.value,
            "notes": self.notes,
            "completed": self.completed,
        }


@dataclass
class Pet:
    """A pet profile that owns a list of care tasks."""

    name: str
    species: str                   # e.g. "dog", "cat"
    breed: str
    age_years: float
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a new task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task_name: str) -> None:
        """Remove the first task whose name matches task_name (case-insensitive)."""
        self.tasks = [t for t in self.tasks if t.name.lower() != task_name.lower()]

    def get_pending_tasks(self) -> list[Task]:
        """Return all tasks that have not yet been marked complete."""
        return [t for t in self.tasks if not t.completed]


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """Represents the pet owner, their daily time budget, and their pets."""

    def __init__(
        self,
        name: str,
        available_minutes: int,
        preferences: Optional[dict] = None,
    ) -> None:
        self.name = name
        self.available_minutes = available_minutes   # total time budget per day
        self.preferences: dict = preferences or {}
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a new pet under this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove the pet with the given name (case-insensitive)."""
        self.pets = [p for p in self.pets if p.name.lower() != pet_name.lower()]

    def get_all_pending_tasks(self) -> list[tuple[Pet, Task]]:
        """Return (pet, task) pairs for every pending task across all pets."""
        pairs: list[tuple[Pet, Task]] = []
        for pet in self.pets:
            for task in pet.get_pending_tasks():
                pairs.append((pet, task))
        return pairs

    def total_task_minutes(self) -> int:
        """Sum of all pending task durations across every owned pet."""
        return sum(task.duration_minutes for _, task in self.get_all_pending_tasks())


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

@dataclass
class ScheduledTask:
    """A task that has been placed in the daily plan, paired with its start time."""

    pet: Pet
    task: Task
    start_minute: int   # minutes elapsed from the start of the scheduling window

    @property
    def end_minute(self) -> int:
        """Minute at which this task ends."""
        return self.start_minute + self.task.duration_minutes


@dataclass
class DailyPlan:
    """The complete output produced by Scheduler.generate_plan()."""

    scheduled: list[ScheduledTask] = field(default_factory=list)
    skipped: list[tuple[Pet, Task]] = field(default_factory=list)
    total_minutes_used: int = 0

    def summary(self) -> str:
        """Return a formatted, human-readable summary of the day's plan."""
        lines: list[str] = []
        lines.append("=" * 50)
        lines.append("  TODAY'S PAWPAL+ SCHEDULE")
        lines.append("=" * 50)

        if self.scheduled:
            lines.append(f"\n  Scheduled ({self.total_minutes_used} min total):\n")
            for st in self.scheduled:
                h_start, m_start = divmod(st.start_minute, 60)
                h_end, m_end = divmod(st.end_minute, 60)
                time_str = (
                    f"  {h_start:02d}:{m_start:02d} - {h_end:02d}:{m_end:02d}"
                )
                lines.append(
                    f"{time_str}  [{st.task.priority.value.upper():6}] "
                    f"{st.pet.name}: {st.task.name} ({st.task.duration_minutes} min)"
                )
                if st.task.notes:
                    lines.append(f"                       Note: {st.task.notes}")
        else:
            lines.append("\n  No tasks scheduled.")

        if self.skipped:
            lines.append("\n  Skipped (not enough time):\n")
            for pet, task in self.skipped:
                lines.append(
                    f"  - {pet.name}: {task.name} "
                    f"({task.duration_minutes} min, {task.priority.value})"
                )

        lines.append("\n" + "=" * 50)
        return "\n".join(lines)


class Scheduler:
    """
    Converts tasks from an Owner's pets into a time-bounded daily plan.

    Strategy (greedy by priority):
      1. Collect all pending (pet, task) pairs from the Owner.
      2. Sort: HIGH → MEDIUM → LOW; shorter duration as tiebreak within same priority.
      3. Greedily add tasks while remaining time allows.
      4. Tasks that don't fit are stored in DailyPlan.skipped.
    """

    PRIORITY_ORDER = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def generate_plan(self) -> DailyPlan:
        """Build and return a DailyPlan that fits within the owner's daily time budget."""
        all_pending = self.owner.get_all_pending_tasks()
        sorted_pairs = self._sort_tasks(all_pending)

        plan = DailyPlan()
        remaining = self.owner.available_minutes
        cursor = 0  # current minute pointer

        for pet, task in sorted_pairs:
            if task.duration_minutes <= remaining:
                plan.scheduled.append(ScheduledTask(pet=pet, task=task, start_minute=cursor))
                cursor += task.duration_minutes
                remaining -= task.duration_minutes
                plan.total_minutes_used += task.duration_minutes
            else:
                plan.skipped.append((pet, task))

        return plan

    def _sort_tasks(self, pairs: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Sort (pet, task) pairs by priority (high first), then duration (shorter first)."""
        return sorted(
            pairs,
            key=lambda pt: (
                self.PRIORITY_ORDER[pt[1].priority],
                pt[1].duration_minutes,
            ),
        )

    def explain_plan(self, plan: DailyPlan) -> str:
        """Return a natural-language explanation of each scheduling decision."""
        lines: list[str] = ["Scheduling explanation:"]

        for st in plan.scheduled:
            lines.append(
                f"  INCLUDED  '{st.task.name}' for {st.pet.name} — "
                f"priority={st.task.priority.value}, duration={st.task.duration_minutes} min"
            )

        for pet, task in plan.skipped:
            lines.append(
                f"  SKIPPED   '{task.name}' for {pet.name} — "
                f"priority={task.priority.value}, duration={task.duration_minutes} min "
                f"(exceeded remaining time budget)"
            )

        lines.append(
            f"\n  Budget used: {plan.total_minutes_used} / {self.owner.available_minutes} min"
        )
        return "\n".join(lines)
