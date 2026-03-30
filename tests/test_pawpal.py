"""
Unit tests for PawPal+ core logic.
Run with: python -m pytest
"""

import pytest
from pawpal_system import (
    Owner,
    Pet,
    Task,
    TaskType,
    Priority,
    Scheduler,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_task(name="Walk", duration=15, priority=Priority.MEDIUM) -> Task:
    return Task(name=name, task_type=TaskType.WALK, duration_minutes=duration, priority=priority)


def make_pet(name="Buddy") -> Pet:
    return Pet(name=name, species="dog", breed="Lab", age_years=2.0)


def make_owner(available_minutes=60) -> Owner:
    owner = Owner(name="Alex", available_minutes=available_minutes)
    return owner


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
        """to_dict() should return all core fields."""
        task = make_task(name="Feed", duration=10, priority=Priority.HIGH)
        d = task.to_dict()
        assert d["name"] == "Feed"
        assert d["duration_minutes"] == 10
        assert d["priority"] == "high"
        assert d["completed"] is False


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
        """total_task_minutes() should sum durations of all pending tasks across pets."""
        owner = make_owner()
        pet1 = make_pet("Buddy")
        pet2 = make_pet("Luna")
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
        pending_task = make_task(name="Pending", duration=10)
        pet.add_task(done_task)
        pet.add_task(pending_task)
        owner.add_pet(pet)
        assert owner.total_task_minutes() == 10


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
        scheduled_names = [st.task.name for st in plan.scheduled]
        skipped_names = [t.name for _, t in plan.skipped]
        assert "Quick" in scheduled_names
        assert "Long" in skipped_names

    def test_total_minutes_does_not_exceed_budget(self):
        """The plan's total_minutes_used must never exceed available_minutes."""
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
        result = plan.summary()
        assert isinstance(result, str)
        assert len(result) > 0
