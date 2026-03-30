"""
Unit tests for PawPal+ core logic.
Run with: python -m pytest
"""

from datetime import date, timedelta

import pytest
from pawpal_system import (
    Conflict,
    Frequency,
    Owner,
    Pet,
    Priority,
    Scheduler,
    ScheduledTask,
    Task,
    TaskType,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_task(
    name="Walk",
    duration=15,
    priority=Priority.MEDIUM,
    frequency=Frequency.ONCE,
) -> Task:
    return Task(
        name=name,
        task_type=TaskType.WALK,
        duration_minutes=duration,
        priority=priority,
        frequency=frequency,
    )


def make_pet(name="Buddy") -> Pet:
    return Pet(name=name, species="dog", breed="Lab", age_years=2.0)


def make_owner(available_minutes=60) -> Owner:
    return Owner(name="Alex", available_minutes=available_minutes)


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------

class TestTask:
    def test_mark_complete_changes_status(self):
        """Calling mark_complete() must flip completed from False to True."""
        task = make_task()
        assert task.completed is False
        task.mark_complete()
        assert task.completed is True

    def test_mark_complete_is_idempotent(self):
        """Calling mark_complete() twice should leave the task completed."""
        task = make_task()
        task.mark_complete()
        task.mark_complete()
        assert task.completed is True

    def test_to_dict_contains_expected_keys(self):
        """to_dict() should return all core fields including frequency and due_date."""
        task = make_task(name="Feed", duration=10, priority=Priority.HIGH)
        d = task.to_dict()
        assert d["name"] == "Feed"
        assert d["duration_minutes"] == 10
        assert d["priority"] == "high"
        assert d["completed"] is False
        assert "frequency" in d
        assert "due_date" in d

    # -- Recurring tasks --

    def test_once_task_returns_none_on_complete(self):
        """A one-time task should return None (no renewal) when completed."""
        task = make_task(frequency=Frequency.ONCE)
        result = task.mark_complete()
        assert result is None

    def test_daily_task_returns_new_task_on_complete(self):
        """A daily task should produce a fresh Task due tomorrow."""
        today = date.today()
        task = Task(
            name="Morning walk",
            task_type=TaskType.WALK,
            duration_minutes=30,
            priority=Priority.HIGH,
            frequency=Frequency.DAILY,
            due_date=today,
        )
        next_task = task.mark_complete()
        assert next_task is not None
        assert next_task.completed is False
        assert next_task.due_date == today + timedelta(days=1)
        assert next_task.name == task.name

    def test_weekly_task_returns_new_task_due_in_7_days(self):
        """A weekly task should produce a renewal due in exactly 7 days."""
        today = date.today()
        task = Task(
            name="Grooming",
            task_type=TaskType.GROOMING,
            duration_minutes=20,
            priority=Priority.MEDIUM,
            frequency=Frequency.WEEKLY,
            due_date=today,
        )
        next_task = task.mark_complete()
        assert next_task is not None
        assert next_task.due_date == today + timedelta(weeks=1)


# ---------------------------------------------------------------------------
# Pet tests
# ---------------------------------------------------------------------------

class TestPet:
    def test_add_task_increases_count(self):
        """Adding a task to a Pet should increase its task count by one."""
        pet = make_pet()
        initial_count = len(pet.tasks)
        pet.add_task(make_task())
        assert len(pet.tasks) == initial_count + 1

    def test_add_multiple_tasks(self):
        """Adding three tasks should result in a count of three."""
        pet = make_pet()
        for i in range(3):
            pet.add_task(make_task(name=f"Task {i}"))
        assert len(pet.tasks) == 3

    def test_remove_task_by_name(self):
        """remove_task() should delete the matching task."""
        pet = make_pet()
        pet.add_task(make_task(name="Walk"))
        pet.add_task(make_task(name="Feed"))
        pet.remove_task("Walk")
        names = [t.name for t in pet.tasks]
        assert "Walk" not in names
        assert "Feed" in names

    def test_get_pending_tasks_excludes_completed(self):
        """get_pending_tasks() should not return tasks that are marked complete."""
        pet = make_pet()
        task_a = make_task(name="A")
        task_b = make_task(name="B")
        task_a.mark_complete()
        pet.add_task(task_a)
        pet.add_task(task_b)
        pending = pet.get_pending_tasks()
        assert len(pending) == 1
        assert pending[0].name == "B"

    def test_complete_task_auto_adds_daily_renewal(self):
        """complete_task() on a daily task should append a new pending instance."""
        pet = make_pet()
        pet.add_task(make_task(name="Breakfast", frequency=Frequency.DAILY))
        assert len(pet.tasks) == 1
        pet.complete_task("Breakfast")
        assert len(pet.tasks) == 2
        assert pet.tasks[0].completed is True
        assert pet.tasks[1].completed is False

    def test_complete_task_no_renewal_for_once(self):
        """complete_task() on a one-time task should not add a renewal."""
        pet = make_pet()
        pet.add_task(make_task(name="Vet visit", frequency=Frequency.ONCE))
        pet.complete_task("Vet visit")
        assert len(pet.tasks) == 1

    # -- Sorting --

    def test_tasks_sorted_by_duration_ascending(self):
        """tasks_sorted_by_duration() should return shortest first by default."""
        pet = make_pet()
        pet.add_task(make_task(name="Long", duration=30))
        pet.add_task(make_task(name="Short", duration=5))
        pet.add_task(make_task(name="Medium", duration=15))
        sorted_tasks = pet.tasks_sorted_by_duration()
        durations = [t.duration_minutes for t in sorted_tasks]
        assert durations == sorted(durations)

    def test_tasks_sorted_by_priority(self):
        """tasks_sorted_by_priority() should return HIGH before LOW."""
        pet = make_pet()
        pet.add_task(make_task(name="Low", priority=Priority.LOW))
        pet.add_task(make_task(name="High", priority=Priority.HIGH))
        sorted_tasks = pet.tasks_sorted_by_priority()
        assert sorted_tasks[0].name == "High"
        assert sorted_tasks[-1].name == "Low"

    # -- Filtering --

    def test_filter_tasks_by_completion(self):
        """filter_tasks(completed=False) should return only pending tasks."""
        pet = make_pet()
        done = make_task(name="Done")
        done.mark_complete()
        pending = make_task(name="Pending")
        pet.add_task(done)
        pet.add_task(pending)
        result = pet.filter_tasks(completed=False)
        assert len(result) == 1
        assert result[0].name == "Pending"

    def test_filter_tasks_by_priority(self):
        """filter_tasks(priority=HIGH) should return only high-priority tasks."""
        pet = make_pet()
        pet.add_task(make_task(name="High", priority=Priority.HIGH))
        pet.add_task(make_task(name="Low", priority=Priority.LOW))
        result = pet.filter_tasks(priority=Priority.HIGH)
        assert all(t.priority == Priority.HIGH for t in result)


# ---------------------------------------------------------------------------
# Owner tests
# ---------------------------------------------------------------------------

class TestOwner:
    def test_add_pet_increases_count(self):
        """add_pet() should increase the owner's pet count."""
        owner = make_owner()
        owner.add_pet(make_pet("Buddy"))
        assert len(owner.pets) == 1

    def test_remove_pet_by_name(self):
        """remove_pet() should remove only the named pet."""
        owner = make_owner()
        owner.add_pet(make_pet("Buddy"))
        owner.add_pet(make_pet("Luna"))
        owner.remove_pet("Buddy")
        names = [p.name for p in owner.pets]
        assert "Buddy" not in names
        assert "Luna" in names

    def test_total_task_minutes_sums_all_pending(self):
        """total_task_minutes() should sum durations across all pets."""
        owner = make_owner()
        pet1, pet2 = make_pet("Buddy"), make_pet("Luna")
        pet1.add_task(make_task(duration=20))
        pet2.add_task(make_task(duration=10))
        owner.add_pet(pet1)
        owner.add_pet(pet2)
        assert owner.total_task_minutes() == 30

    def test_total_task_minutes_excludes_completed(self):
        """Completed tasks should not count toward total_task_minutes()."""
        owner = make_owner()
        pet = make_pet()
        done_task = make_task(name="Done", duration=15)
        done_task.mark_complete()
        pet.add_task(done_task)
        pet.add_task(make_task(name="Pending", duration=10))
        owner.add_pet(pet)
        assert owner.total_task_minutes() == 10

    def test_filter_tasks_by_pet(self):
        """filter_tasks_by_pet() should return only tasks for the named pet."""
        owner = make_owner()
        buddy, luna = make_pet("Buddy"), make_pet("Luna")
        buddy.add_task(make_task(name="Walk"))
        luna.add_task(make_task(name="Brush"))
        owner.add_pet(buddy)
        owner.add_pet(luna)
        results = owner.filter_tasks_by_pet("Buddy")
        assert all(pet.name == "Buddy" for pet, _ in results)
        assert len(results) == 1


# ---------------------------------------------------------------------------
# Scheduler tests
# ---------------------------------------------------------------------------

class TestScheduler:
    def test_high_priority_scheduled_before_low(self):
        """High-priority tasks should appear before low-priority ones in the plan."""
        owner = make_owner(available_minutes=60)
        pet = make_pet()
        pet.add_task(make_task(name="Low task", duration=10, priority=Priority.LOW))
        pet.add_task(make_task(name="High task", duration=10, priority=Priority.HIGH))
        owner.add_pet(pet)

        plan = Scheduler(owner).generate_plan()
        names = [st.task.name for st in plan.scheduled]
        assert names.index("High task") < names.index("Low task")

    def test_tasks_exceeding_budget_are_skipped(self):
        """Tasks that push over the time budget should appear in skipped."""
        owner = make_owner(available_minutes=20)
        pet = make_pet()
        pet.add_task(make_task(name="Quick", duration=10, priority=Priority.HIGH))
        pet.add_task(make_task(name="Long", duration=30, priority=Priority.HIGH))
        owner.add_pet(pet)

        plan = Scheduler(owner).generate_plan()
        assert "Quick" in [st.task.name for st in plan.scheduled]
        assert "Long" in [t.name for _, t in plan.skipped]

    def test_total_minutes_does_not_exceed_budget(self):
        """total_minutes_used must never exceed available_minutes."""
        owner = make_owner(available_minutes=45)
        pet = make_pet()
        for i in range(5):
            pet.add_task(make_task(name=f"Task {i}", duration=15))
        owner.add_pet(pet)
        plan = Scheduler(owner).generate_plan()
        assert plan.total_minutes_used <= owner.available_minutes

    def test_empty_task_list_produces_empty_plan(self):
        """An owner with no tasks should produce a plan with nothing scheduled."""
        owner = make_owner()
        owner.add_pet(make_pet())
        plan = Scheduler(owner).generate_plan()
        assert plan.scheduled == []
        assert plan.skipped == []

    def test_plan_summary_is_string(self):
        """DailyPlan.summary() should return a non-empty string."""
        owner = make_owner()
        pet = make_pet()
        pet.add_task(make_task())
        owner.add_pet(pet)
        plan = Scheduler(owner).generate_plan()
        assert isinstance(plan.summary(), str)
        assert len(plan.summary()) > 0

    # -- Sorting --

    def test_sort_scheduled_by_start(self):
        """sort_scheduled_by_start() should order tasks by start_minute ascending."""
        pet = make_pet()
        task_a = make_task(name="A", duration=10)
        task_b = make_task(name="B", duration=5)
        st_a = ScheduledTask(pet=pet, task=task_a, start_minute=20)
        st_b = ScheduledTask(pet=pet, task=task_b, start_minute=5)
        result = Scheduler.sort_scheduled_by_start([st_a, st_b])
        assert result[0].start_minute < result[1].start_minute

    def test_sort_scheduled_by_duration_descending(self):
        """sort_scheduled_by_duration(ascending=False) should put longest first."""
        pet = make_pet()
        short = ScheduledTask(pet=pet, task=make_task(duration=5), start_minute=0)
        long_ = ScheduledTask(pet=pet, task=make_task(duration=30), start_minute=5)
        result = Scheduler.sort_scheduled_by_duration([short, long_], ascending=False)
        assert result[0].task.duration_minutes == 30

    # -- Filtering --

    def test_filter_by_pet(self):
        """filter_by_pet() should return only tasks for the named pet."""
        buddy = make_pet("Buddy")
        luna = make_pet("Luna")
        st_buddy = ScheduledTask(pet=buddy, task=make_task(), start_minute=0)
        st_luna = ScheduledTask(pet=luna, task=make_task(), start_minute=15)
        result = Scheduler.filter_by_pet([st_buddy, st_luna], "Buddy")
        assert len(result) == 1
        assert result[0].pet.name == "Buddy"

    def test_filter_by_priority(self):
        """filter_by_priority() should return only tasks at the given level."""
        pet = make_pet()
        high_st = ScheduledTask(pet=pet, task=make_task(priority=Priority.HIGH), start_minute=0)
        low_st = ScheduledTask(pet=pet, task=make_task(priority=Priority.LOW), start_minute=15)
        result = Scheduler.filter_by_priority([high_st, low_st], Priority.HIGH)
        assert len(result) == 1
        assert result[0].task.priority == Priority.HIGH

    # -- Conflict detection --

    def test_no_conflict_for_sequential_tasks(self):
        """Tasks that run back-to-back should produce no conflicts."""
        pet = make_pet()
        a = ScheduledTask(pet=pet, task=make_task(duration=10), start_minute=0)
        b = ScheduledTask(pet=pet, task=make_task(duration=10), start_minute=10)
        assert Scheduler.detect_conflicts([a, b]) == []

    def test_conflict_detected_for_overlapping_tasks(self):
        """Tasks that overlap in time should produce a Conflict."""
        pet = make_pet()
        a = ScheduledTask(pet=pet, task=make_task(duration=20), start_minute=0)
        b = ScheduledTask(pet=pet, task=make_task(duration=10), start_minute=10)
        conflicts = Scheduler.detect_conflicts([a, b])
        assert len(conflicts) == 1
        assert isinstance(conflicts[0], Conflict)

    def test_conflict_str_contains_task_names(self):
        """Conflict.__str__() should mention both task names."""
        pet = make_pet()
        a = ScheduledTask(pet=pet, task=make_task(name="Walk", duration=20), start_minute=0)
        b = ScheduledTask(pet=pet, task=make_task(name="Feed", duration=10), start_minute=10)
        conflict = Scheduler.detect_conflicts([a, b])[0]
        msg = str(conflict)
        assert "Walk" in msg
        assert "Feed" in msg

    def test_plan_has_no_conflicts_by_default(self):
        """The greedy planner assigns tasks sequentially so there are no overlaps."""
        owner = make_owner(available_minutes=60)
        pet = make_pet()
        for i in range(4):
            pet.add_task(make_task(name=f"Task {i}", duration=10))
        owner.add_pet(pet)
        plan = Scheduler(owner).generate_plan()
        assert plan.conflicts == []


# ---------------------------------------------------------------------------
# Edge-case tests
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Happy-path limits and boundary conditions for every major feature."""

    # -- Pet with zero tasks --

    def test_pet_with_no_tasks_has_empty_pending(self):
        """A freshly created Pet has no pending tasks."""
        pet = make_pet()
        assert pet.get_pending_tasks() == []

    def test_pet_with_no_tasks_sorts_to_empty_list(self):
        """Sorting an empty task list should return an empty list, not raise."""
        pet = make_pet()
        assert pet.tasks_sorted_by_duration() == []
        assert pet.tasks_sorted_by_priority() == []

    def test_owner_with_no_pets_returns_zero_minutes(self):
        """An owner who has registered no pets should have 0 total task minutes."""
        owner = make_owner()
        assert owner.total_task_minutes() == 0

    def test_owner_with_no_pets_has_empty_pending_list(self):
        """get_all_pending_tasks() returns an empty list when no pets exist."""
        owner = make_owner()
        assert owner.get_all_pending_tasks() == []

    # -- Exact-fit budget --

    def test_task_exactly_filling_budget_is_scheduled(self):
        """A task whose duration exactly equals available_minutes must be scheduled."""
        owner = make_owner(available_minutes=30)
        pet = make_pet()
        pet.add_task(make_task(name="Exact fit", duration=30))
        owner.add_pet(pet)
        plan = Scheduler(owner).generate_plan()
        assert len(plan.scheduled) == 1
        assert plan.total_minutes_used == 30
        assert plan.skipped == []

    def test_task_one_minute_over_budget_is_skipped(self):
        """A task that exceeds the budget by exactly 1 minute must be skipped."""
        owner = make_owner(available_minutes=29)
        pet = make_pet()
        pet.add_task(make_task(name="One over", duration=30))
        owner.add_pet(pet)
        plan = Scheduler(owner).generate_plan()
        assert plan.scheduled == []
        assert len(plan.skipped) == 1

    # -- Sorting correctness --

    def test_sort_by_duration_preserves_all_tasks(self):
        """Sorting should not drop or duplicate any tasks."""
        pet = make_pet()
        for i in range(5):
            pet.add_task(make_task(name=f"T{i}", duration=i * 5 + 1))
        original_names = {t.name for t in pet.tasks}
        sorted_names = {t.name for t in pet.tasks_sorted_by_duration()}
        assert original_names == sorted_names

    def test_sort_by_duration_is_non_destructive(self):
        """tasks_sorted_by_duration() must not reorder pet.tasks in place."""
        pet = make_pet()
        pet.add_task(make_task(name="Long", duration=30))
        pet.add_task(make_task(name="Short", duration=5))
        original_order = [t.name for t in pet.tasks]
        pet.tasks_sorted_by_duration()   # call the sort
        assert [t.name for t in pet.tasks] == original_order   # unchanged

    def test_scheduled_tasks_start_minutes_are_ascending(self):
        """In a freshly generated plan, start_minute must strictly increase."""
        owner = make_owner(available_minutes=90)
        pet = make_pet()
        for i in range(4):
            pet.add_task(make_task(name=f"T{i}", duration=10))
        owner.add_pet(pet)
        plan = Scheduler(owner).generate_plan()
        starts = [st.start_minute for st in plan.scheduled]
        assert starts == sorted(starts)

    def test_end_minute_equals_start_plus_duration(self):
        """ScheduledTask.end_minute must always equal start_minute + duration."""
        pet = make_pet()
        task = make_task(duration=25)
        st = ScheduledTask(pet=pet, task=task, start_minute=10)
        assert st.end_minute == 35

    # -- Recurrence edge cases --

    def test_daily_task_without_due_date_uses_today(self):
        """A daily task with no due_date set should renew relative to today."""
        today = date.today()
        task = Task(
            name="Walk",
            task_type=TaskType.WALK,
            duration_minutes=20,
            priority=Priority.HIGH,
            frequency=Frequency.DAILY,
            due_date=None,   # no explicit date
        )
        next_task = task.mark_complete()
        assert next_task is not None
        assert next_task.due_date == today + timedelta(days=1)

    def test_completing_recurring_task_does_not_affect_other_tasks(self):
        """Renewing one task should not change any other task on the pet."""
        pet = make_pet()
        pet.add_task(make_task(name="Daily walk", frequency=Frequency.DAILY))
        pet.add_task(make_task(name="One-time vet", frequency=Frequency.ONCE))
        pet.complete_task("Daily walk")
        vet_task = next(t for t in pet.tasks if t.name == "One-time vet")
        assert vet_task.completed is False   # untouched

    def test_renewed_task_inherits_same_type_and_priority(self):
        """The renewal produced by mark_complete() must carry forward all core fields."""
        task = Task(
            name="Medication",
            task_type=TaskType.MEDICATION,
            duration_minutes=5,
            priority=Priority.HIGH,
            frequency=Frequency.DAILY,
            due_date=date.today(),
        )
        renewal = task.mark_complete()
        assert renewal is not None
        assert renewal.task_type == TaskType.MEDICATION
        assert renewal.priority == Priority.HIGH
        assert renewal.duration_minutes == 5
        assert renewal.frequency == Frequency.DAILY

    # -- Conflict detection edge cases --

    def test_tasks_sharing_exact_start_conflict(self):
        """Two tasks starting at the same minute must be flagged as a conflict."""
        pet = make_pet()
        a = ScheduledTask(pet=pet, task=make_task(name="A", duration=10), start_minute=0)
        b = ScheduledTask(pet=pet, task=make_task(name="B", duration=5), start_minute=0)
        conflicts = Scheduler.detect_conflicts([a, b])
        assert len(conflicts) == 1

    def test_task_ending_exactly_when_next_starts_is_not_a_conflict(self):
        """Back-to-back tasks (end == next start) must NOT be a conflict."""
        pet = make_pet()
        a = ScheduledTask(pet=pet, task=make_task(duration=10), start_minute=0)
        b = ScheduledTask(pet=pet, task=make_task(duration=10), start_minute=10)
        assert Scheduler.detect_conflicts([a, b]) == []

    def test_single_task_has_no_conflicts(self):
        """A list with only one task cannot conflict with anything."""
        pet = make_pet()
        a = ScheduledTask(pet=pet, task=make_task(duration=20), start_minute=0)
        assert Scheduler.detect_conflicts([a]) == []

    def test_empty_scheduled_list_has_no_conflicts(self):
        """detect_conflicts([]) must return an empty list without raising."""
        assert Scheduler.detect_conflicts([]) == []

    def test_multiple_conflicts_all_reported(self):
        """When three tasks all overlap, all pairwise conflicts must be returned."""
        pet = make_pet()
        a = ScheduledTask(pet=pet, task=make_task(name="A", duration=30), start_minute=0)
        b = ScheduledTask(pet=pet, task=make_task(name="B", duration=30), start_minute=5)
        c = ScheduledTask(pet=pet, task=make_task(name="C", duration=30), start_minute=10)
        conflicts = Scheduler.detect_conflicts([a, b, c])
        assert len(conflicts) == 3   # A-B, A-C, B-C

    # -- Filter edge cases --

    def test_filter_by_nonexistent_pet_returns_empty(self):
        """filter_by_pet() for a name that doesn't exist should return []."""
        pet = make_pet("Buddy")
        st = ScheduledTask(pet=pet, task=make_task(), start_minute=0)
        assert Scheduler.filter_by_pet([st], "Ghost") == []

    def test_filter_tasks_by_pet_case_insensitive(self):
        """filter_tasks_by_pet() should match regardless of name capitalisation."""
        owner = make_owner()
        pet = make_pet("Buddy")
        pet.add_task(make_task())
        owner.add_pet(pet)
        assert len(owner.filter_tasks_by_pet("buddy")) == 1
        assert len(owner.filter_tasks_by_pet("BUDDY")) == 1
