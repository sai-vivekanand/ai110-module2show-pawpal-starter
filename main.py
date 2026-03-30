"""
main.py — PawPal+ demo / smoke-test script.
Run with: python main.py
"""

from pawpal_system import Owner, Pet, Task, TaskType, Priority, Scheduler


def main() -> None:
    # --- Owner setup -------------------------------------------------------
    alex = Owner(name="Alex", available_minutes=90)

    # --- Pets --------------------------------------------------------------
    buddy = Pet(name="Buddy", species="dog", breed="Labrador", age_years=3.0)
    luna = Pet(name="Luna", species="cat", breed="Siamese", age_years=2.5)

    alex.add_pet(buddy)
    alex.add_pet(luna)

    # --- Tasks for Buddy ---------------------------------------------------
    buddy.add_task(Task(
        name="Morning walk",
        task_type=TaskType.WALK,
        duration_minutes=30,
        priority=Priority.HIGH,
        notes="Go around the park twice",
    ))
    buddy.add_task(Task(
        name="Breakfast",
        task_type=TaskType.FEEDING,
        duration_minutes=10,
        priority=Priority.HIGH,
    ))
    buddy.add_task(Task(
        name="Flea treatment",
        task_type=TaskType.MEDICATION,
        duration_minutes=5,
        priority=Priority.MEDIUM,
        notes="Apply between shoulder blades",
    ))
    buddy.add_task(Task(
        name="Fetch / enrichment",
        task_type=TaskType.ENRICHMENT,
        duration_minutes=20,
        priority=Priority.LOW,
    ))

    # --- Tasks for Luna ----------------------------------------------------
    luna.add_task(Task(
        name="Wet food",
        task_type=TaskType.FEEDING,
        duration_minutes=5,
        priority=Priority.HIGH,
    ))
    luna.add_task(Task(
        name="Brush coat",
        task_type=TaskType.GROOMING,
        duration_minutes=15,
        priority=Priority.MEDIUM,
        notes="Use the slicker brush",
    ))
    luna.add_task(Task(
        name="Laser-pointer play",
        task_type=TaskType.ENRICHMENT,
        duration_minutes=10,
        priority=Priority.LOW,
    ))

    # --- Schedule ----------------------------------------------------------
    scheduler = Scheduler(owner=alex)
    plan = scheduler.generate_plan()

    print(plan.summary())
    print()
    print(scheduler.explain_plan(plan))


if __name__ == "__main__":
    main()
