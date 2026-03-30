"""
PawPal+ — logic layer
All backend classes live here; UI (app.py) imports from this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
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


class Frequency(str, Enum):
    """How often a task should recur after completion."""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet-care task, optionally recurring."""

    name: str
    task_type: TaskType
    duration_minutes: int           # estimated time needed
    priority: Priority
    notes: str = ""
    completed: bool = False
    frequency: Frequency = Frequency.ONCE
    due_date: Optional[date] = None  # None means "any day / today"

    def mark_complete(self) -> Optional[Task]:
        """
        Mark this task done. For recurring tasks returns a new Task instance
        scheduled for the next occurrence; returns None for one-time tasks.
        """
        self.completed = True
        if self.frequency == Frequency.DAILY:
            next_due = (self.due_date or date.today()) + timedelta(days=1)
            return Task(
                name=self.name,
                task_type=self.task_type,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                notes=self.notes,
                frequency=self.frequency,
                due_date=next_due,
            )
        if self.frequency == Frequency.WEEKLY:
            next_due = (self.due_date or date.today()) + timedelta(weeks=1)
            return Task(
                name=self.name,
                task_type=self.task_type,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                notes=self.notes,
                frequency=self.frequency,
                due_date=next_due,
            )
        return None

    def to_dict(self) -> dict:
        """Return a plain dict representation suitable for JSON export or Streamlit state."""
        return {
            "name": self.name,
            "task_type": self.task_type.value,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority.value,
            "notes": self.notes,
            "completed": self.completed,
            "frequency": self.frequency.value,
            "due_date": self.due_date.isoformat() if self.due_date else None,
        }


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """A pet profile that owns a list of care tasks."""

    name: str
    species: str                    # e.g. "dog", "cat"
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

    def complete_task(self, task_name: str) -> None:
        """
        Mark the named task complete. If it is recurring, automatically add
        the next occurrence to this pet's task list.
        """
        for task in self.tasks:
            if task.name.lower() == task_name.lower() and not task.completed:
                next_task = task.mark_complete()
                if next_task:
                    self.tasks.append(next_task)
                break

    # ------------------------------------------------------------------
    # Filtering helpers
    # ------------------------------------------------------------------

    def filter_tasks(
        self,
        *,
        completed: Optional[bool] = None,
        task_type: Optional[TaskType] = None,
        priority: Optional[Priority] = None,
    ) -> list[Task]:
        """
        Return a filtered view of this pet's tasks.

        Pass keyword arguments to narrow results:
        - completed=True/False filters by completion status
        - task_type=TaskType.WALK limits to a specific type
        - priority=Priority.HIGH limits to a specific priority level
        """
        result = self.tasks
        if completed is not None:
            result = [t for t in result if t.completed == completed]
        if task_type is not None:
            result = [t for t in result if t.task_type == task_type]
        if priority is not None:
            result = [t for t in result if t.priority == priority]
        return result

    # ------------------------------------------------------------------
    # Sorting helpers
    # ------------------------------------------------------------------

    def tasks_sorted_by_duration(self, *, ascending: bool = True) -> list[Task]:
        """Return pending tasks sorted by duration_minutes."""
        return sorted(
            self.get_pending_tasks(),
            key=lambda t: t.duration_minutes,
            reverse=not ascending,
        )

    def tasks_sorted_by_priority(self) -> list[Task]:
        """Return pending tasks sorted HIGH → MEDIUM → LOW."""
        order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
        return sorted(self.get_pending_tasks(), key=lambda t: order[t.priority])


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

    def filter_tasks_by_pet(self, pet_name: str) -> list[tuple[Pet, Task]]:
        """Return pending (pet, task) pairs for a single named pet."""
        return [
            (pet, task)
            for pet, task in self.get_all_pending_tasks()
            if pet.name.lower() == pet_name.lower()
        ]

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
class Conflict:
    """Two scheduled tasks whose time windows overlap."""

    task_a: ScheduledTask
    task_b: ScheduledTask

    def __str__(self) -> str:
        """Return a human-readable warning describing the overlap."""
        return (
            f"CONFLICT: '{self.task_a.task.name}' ({self.task_a.pet.name}, "
            f"{self.task_a.start_minute}–{self.task_a.end_minute} min) overlaps with "
            f"'{self.task_b.task.name}' ({self.task_b.pet.name}, "
            f"{self.task_b.start_minute}–{self.task_b.end_minute} min)"
        )


@dataclass
class DailyPlan:
    """The complete output produced by Scheduler.generate_plan()."""

    scheduled: list[ScheduledTask] = field(default_factory=list)
    skipped: list[tuple[Pet, Task]] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    total_minutes_used: int = 0

    def summary(self) -> str:
        """Return a formatted, human-readable summary of the day's plan."""
        lines: list[str] = []
        lines.append("=" * 54)
        lines.append("  TODAY'S PAWPAL+ SCHEDULE")
        lines.append("=" * 54)

        if self.scheduled:
            lines.append(f"\n  Scheduled ({self.total_minutes_used} min total):\n")
            for st in self.scheduled:
                h_start, m_start = divmod(st.start_minute, 60)
                h_end, m_end = divmod(st.end_minute, 60)
                time_str = f"  {h_start:02d}:{m_start:02d} - {h_end:02d}:{m_end:02d}"
                lines.append(
                    f"{time_str}  [{st.task.priority.value.upper():6}] "
                    f"{st.pet.name}: {st.task.name} ({st.task.duration_minutes} min)"
                    + (f"  [{st.task.frequency.value}]" if st.task.frequency != Frequency.ONCE else "")
                )
                if st.task.notes:
                    lines.append(f"                         Note: {st.task.notes}")
        else:
            lines.append("\n  No tasks scheduled.")

        if self.skipped:
            lines.append("\n  Skipped (not enough time):\n")
            for pet, task in self.skipped:
                lines.append(
                    f"  - {pet.name}: {task.name} "
                    f"({task.duration_minutes} min, {task.priority.value})"
                )

        if self.conflicts:
            lines.append("\n  ⚠ Conflicts detected:\n")
            for conflict in self.conflicts:
                lines.append(f"  {conflict}")

        lines.append("\n" + "=" * 54)
        return "\n".join(lines)


class Scheduler:
    """
    Converts tasks from an Owner's pets into a time-bounded daily plan.

    Strategy (greedy by priority):
      1. Collect all pending (pet, task) pairs from the Owner.
      2. Sort: HIGH → MEDIUM → LOW; shorter duration as tiebreak.
      3. Greedily schedule tasks within the owner's time budget.
      4. Run overlap detection across all scheduled tasks.
    """

    PRIORITY_ORDER = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    # ------------------------------------------------------------------
    # Core plan generation
    # ------------------------------------------------------------------

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

        plan.conflicts = self.detect_conflicts(plan.scheduled)
        return plan

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------

    def _sort_tasks(self, pairs: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Sort (pet, task) pairs by priority (HIGH first), then duration (shorter first)."""
        return sorted(
            pairs,
            key=lambda pt: (self.PRIORITY_ORDER[pt[1].priority], pt[1].duration_minutes),
        )

    @staticmethod
    def sort_scheduled_by_start(scheduled: list[ScheduledTask]) -> list[ScheduledTask]:
        """Return scheduled tasks sorted ascending by their start_minute."""
        return sorted(scheduled, key=lambda st: st.start_minute)

    @staticmethod
    def sort_scheduled_by_duration(
        scheduled: list[ScheduledTask], *, ascending: bool = True
    ) -> list[ScheduledTask]:
        """Return scheduled tasks sorted by task duration."""
        return sorted(
            scheduled,
            key=lambda st: st.task.duration_minutes,
            reverse=not ascending,
        )

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    @staticmethod
    def filter_by_pet(
        scheduled: list[ScheduledTask], pet_name: str
    ) -> list[ScheduledTask]:
        """Return only the scheduled tasks belonging to the named pet."""
        return [st for st in scheduled if st.pet.name.lower() == pet_name.lower()]

    @staticmethod
    def filter_by_priority(
        scheduled: list[ScheduledTask], priority: Priority
    ) -> list[ScheduledTask]:
        """Return only scheduled tasks at the given priority level."""
        return [st for st in scheduled if st.task.priority == priority]

    @staticmethod
    def filter_by_type(
        scheduled: list[ScheduledTask], task_type: TaskType
    ) -> list[ScheduledTask]:
        """Return only scheduled tasks of the given task type."""
        return [st for st in scheduled if st.task.task_type == task_type]

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    @staticmethod
    def detect_conflicts(scheduled: list[ScheduledTask]) -> list[Conflict]:
        """
        Detect overlapping time windows across all scheduled tasks.

        Two tasks conflict when one starts before the other ends.
        Returns a list of Conflict objects (empty if no overlaps found).
        This is O(n²) which is fine for the small task counts typical in
        a single-owner pet-care app.
        """
        conflicts: list[Conflict] = []
        for i, a in enumerate(scheduled):
            for b in scheduled[i + 1:]:
                # Tasks overlap when neither ends before the other starts
                if a.start_minute < b.end_minute and b.start_minute < a.end_minute:
                    conflicts.append(Conflict(task_a=a, task_b=b))
        return conflicts

    # ------------------------------------------------------------------
    # Explanation
    # ------------------------------------------------------------------

    def explain_plan(self, plan: DailyPlan) -> str:
        """Return a natural-language explanation of each scheduling decision."""
        lines: list[str] = ["Scheduling explanation:"]

        for st in plan.scheduled:
            recur = f" [{st.task.frequency.value}]" if st.task.frequency != Frequency.ONCE else ""
            lines.append(
                f"  INCLUDED  '{st.task.name}' for {st.pet.name} — "
                f"priority={st.task.priority.value}, duration={st.task.duration_minutes} min{recur}"
            )

        for pet, task in plan.skipped:
            lines.append(
                f"  SKIPPED   '{task.name}' for {pet.name} — "
                f"priority={task.priority.value}, duration={task.duration_minutes} min "
                f"(exceeded remaining time budget)"
            )

        if plan.conflicts:
            lines.append("\n  Conflicts:")
            for c in plan.conflicts:
                lines.append(f"    {c}")

        lines.append(
            f"\n  Budget used: {plan.total_minutes_used} / {self.owner.available_minutes} min"
        )
        return "\n".join(lines)
