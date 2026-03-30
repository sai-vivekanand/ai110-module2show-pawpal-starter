"""
main.py — PawPal+ demo / smoke-test script.
Run with: python main.py
"""

from datetime import date

from pawpal_system import (
    Frequency,
    Owner,
    Pet,
    Priority,
    Scheduler,
    Task,
    TaskType,
)


def section(title: str) -> None:
    print(f"\n{'─' * 54}")
    print(f"  {title}")
    print('─' * 54)


def main() -> None:
    # ----------------------------------------------------------------
    # Setup
    # ----------------------------------------------------------------
    alex = Owner(name="Alex", available_minutes=90)

    buddy = Pet(name="Buddy", species="dog", breed="Labrador", age_years=3.0)
    luna = Pet(name="Luna", species="cat", breed="Siamese", age_years=2.5)
    alex.add_pet(buddy)
    alex.add_pet(luna)

    # Tasks added intentionally OUT OF ORDER to show sorting
    buddy.add_task(Task(
        name="Fetch / enrichment",
        task_type=TaskType.ENRICHMENT,
        duration_minutes=20,
        priority=Priority.LOW,
        frequency=Frequency.DAILY,
        due_date=date.today(),
    ))
    buddy.add_task(Task(
        name="Morning walk",
        task_type=TaskType.WALK,
        duration_minutes=30,
        priority=Priority.HIGH,
        notes="Go around the park twice",
        frequency=Frequency.DAILY,
        due_date=date.today(),
    ))
    buddy.add_task(Task(
        name="Breakfast",
        task_type=TaskType.FEEDING,
        duration_minutes=10,
        priority=Priority.HIGH,
        frequency=Frequency.DAILY,
        due_date=date.today(),
    ))
    buddy.add_task(Task(
        name="Flea treatment",
        task_type=TaskType.MEDICATION,
        duration_minutes=5,
        priority=Priority.MEDIUM,
        notes="Apply between shoulder blades",
        frequency=Frequency.WEEKLY,
        due_date=date.today(),
    ))

    luna.add_task(Task(
        name="Wet food",
        task_type=TaskType.FEEDING,
        duration_minutes=5,
        priority=Priority.HIGH,
        frequency=Frequency.DAILY,
        due_date=date.today(),
    ))
    luna.add_task(Task(
        name="Brush coat",
        task_type=TaskType.GROOMING,
        duration_minutes=15,
        priority=Priority.MEDIUM,
        notes="Use the slicker brush",
        frequency=Frequency.WEEKLY,
        due_date=date.today(),
    ))
    luna.add_task(Task(
        name="Laser-pointer play",
        task_type=TaskType.ENRICHMENT,
        duration_minutes=10,
        priority=Priority.LOW,
        frequency=Frequency.DAILY,
        due_date=date.today(),
    ))

    # ----------------------------------------------------------------
    # 1. Sorting demo — tasks sorted by duration before scheduling
    # ----------------------------------------------------------------
    section("SORTING: Buddy's pending tasks by duration (shortest first)")
    for t in buddy.tasks_sorted_by_duration():
        print(f"  {t.duration_minutes:3d} min  [{t.priority.value:6}]  {t.name}")

    section("SORTING: Buddy's pending tasks by priority")
    for t in buddy.tasks_sorted_by_priority():
        print(f"  [{t.priority.value:6}]  {t.duration_minutes} min  {t.name}")

    # ----------------------------------------------------------------
    # 2. Filtering demo
    # ----------------------------------------------------------------
    section("FILTERING: Luna's HIGH priority tasks only")
    for t in luna.filter_tasks(priority=Priority.HIGH):
        print(f"  {t.name} ({t.duration_minutes} min)")

    section("FILTERING: All pending tasks for Buddy via Owner")
    for pet, task in alex.filter_tasks_by_pet("Buddy"):
        print(f"  {pet.name}: {task.name} ({task.duration_minutes} min)")

    # ----------------------------------------------------------------
    # 3. Generate + display plan (greedy / priority-sorted)
    # ----------------------------------------------------------------
    section("SCHEDULE: Today's plan")
    scheduler = Scheduler(owner=alex)
    plan = scheduler.generate_plan()
    print(plan.summary())
    print()
    print(scheduler.explain_plan(plan))

    # ----------------------------------------------------------------
    # 4. Sorted views of the generated plan
    # ----------------------------------------------------------------
    section("SORTED PLAN: Scheduled tasks by duration (longest first)")
    for st in Scheduler.sort_scheduled_by_duration(plan.scheduled, ascending=False):
        print(f"  {st.task.duration_minutes:3d} min  {st.pet.name}: {st.task.name}")

    section("FILTERED PLAN: Only Buddy's scheduled tasks")
    for st in Scheduler.filter_by_pet(plan.scheduled, "Buddy"):
        h, m = divmod(st.start_minute, 60)
        print(f"  {h:02d}:{m:02d}  {st.task.name}")

    # ----------------------------------------------------------------
    # 5. Recurring task demo — complete a daily task and see renewal
    # ----------------------------------------------------------------
    section("RECURRING: Complete Buddy's 'Breakfast' (daily) → auto-schedules tomorrow")
    before = len(buddy.tasks)
    buddy.complete_task("Breakfast")
    after = len(buddy.tasks)
    print(f"  Task count before: {before}  after: {after}")
    renewed = buddy.tasks[-1]
    print(f"  Next occurrence: '{renewed.name}'  due={renewed.due_date}  completed={renewed.completed}")

    # ----------------------------------------------------------------
    # 6. Conflict detection demo — force two tasks to overlap
    # ----------------------------------------------------------------
    section("CONFLICT DETECTION: Manually overlapping two tasks")
    from pawpal_system import ScheduledTask, DailyPlan, Conflict

    overlap_a = ScheduledTask(pet=buddy, task=buddy.tasks[0], start_minute=0)
    overlap_b = ScheduledTask(pet=luna, task=luna.tasks[0], start_minute=5)  # starts before A ends
    conflicts = Scheduler.detect_conflicts([overlap_a, overlap_b])
    if conflicts:
        for c in conflicts:
            print(f"  ⚠ {c}")
    else:
        print("  No conflicts detected.")


if __name__ == "__main__":
    main()
