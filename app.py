"""
PawPal+ — Streamlit UI
Connects the Owner / Pet / Task / Scheduler logic layer to the browser.
"""

import streamlit as st

from pawpal_system import (
    Frequency,
    Owner,
    Pet,
    Priority,
    Scheduler,
    Task,
    TaskType,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# ---------------------------------------------------------------------------
# Session-state bootstrap
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None
if "last_plan" not in st.session_state:
    st.session_state.last_plan = None


def owner() -> Owner | None:
    """Return the Owner stored in session_state (may be None before setup)."""
    return st.session_state.owner


# ============================================================
# OWNER SETUP
# ============================================================

st.title("🐾 PawPal+")
st.caption("Smart pet care scheduling — priority-aware, conflict-detecting, recurring-task-ready.")
st.subheader("Owner Setup")

with st.form("owner_form"):
    col_a, col_b = st.columns(2)
    with col_a:
        owner_name = st.text_input("Your name", value="Jordan")
    with col_b:
        available_minutes = st.number_input(
            "Minutes available today", min_value=10, max_value=480, value=90, step=5
        )
    submitted_owner = st.form_submit_button("Save owner info")

if submitted_owner:
    existing_pets = owner().pets if owner() else []
    st.session_state.owner = Owner(name=owner_name, available_minutes=int(available_minutes))
    for pet in existing_pets:
        st.session_state.owner.add_pet(pet)
    st.success(f"Owner saved: {owner_name} ({available_minutes} min/day)")

if owner():
    total_needed = owner().total_task_minutes()
    budget = owner().available_minutes
    pct = min(total_needed / budget, 1.0) if budget else 0
    st.caption(
        f"Active owner: **{owner().name}** | Budget: **{budget} min/day** | "
        f"Pets: **{len(owner().pets)}** | Pending tasks: **{total_needed} min**"
    )
    st.progress(pct, text=f"{total_needed}/{budget} min planned")
else:
    st.info("Fill in your name and available time, then click **Save owner info** to get started.")
    st.stop()

st.divider()

# ============================================================
# PET MANAGEMENT
# ============================================================

st.subheader("My Pets")

with st.expander("Add a new pet", expanded=len(owner().pets) == 0):
    with st.form("add_pet_form"):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            pet_name = st.text_input("Pet name", value="Buddy")
        with c2:
            species = st.selectbox("Species", ["dog", "cat", "bird", "rabbit", "other"])
        with c3:
            breed = st.text_input("Breed", value="Labrador")
        with c4:
            age = st.number_input("Age (years)", min_value=0.0, max_value=30.0, value=2.0, step=0.5)
        add_pet_btn = st.form_submit_button("Add pet")

    if add_pet_btn:
        existing_names = [p.name.lower() for p in owner().pets]
        if pet_name.strip().lower() in existing_names:
            st.warning(f"A pet named '{pet_name}' already exists.")
        elif not pet_name.strip():
            st.warning("Pet name cannot be empty.")
        else:
            owner().add_pet(Pet(name=pet_name.strip(), species=species, breed=breed, age_years=float(age)))
            st.success(f"Added {pet_name.strip()} the {species}!")

if not owner().pets:
    st.info("No pets yet. Add one above.")
else:
    for pet in owner().pets:
        pending = pet.get_pending_tasks()
        done = [t for t in pet.tasks if t.completed]
        with st.expander(f"🐾 {pet.name} — {pet.species} ({pet.breed}, {pet.age_years} yrs) | {len(pending)} pending"):
            st.caption(f"{len(pending)} pending · {len(done)} completed")
            if st.button(f"Remove {pet.name}", key=f"remove_pet_{pet.name}"):
                owner().remove_pet(pet.name)
                st.rerun()

st.divider()

# ============================================================
# TASK MANAGEMENT
# ============================================================

st.subheader("Care Tasks")

if not owner().pets:
    st.info("Add at least one pet before adding tasks.")
else:
    with st.expander("Add a new task", expanded=True):
        with st.form("add_task_form"):
            tc1, tc2 = st.columns(2)
            with tc1:
                task_pet = st.selectbox("For which pet?", [p.name for p in owner().pets])
                task_name = st.text_input("Task name", value="Morning walk")
                task_type = st.selectbox("Task type", [t.value for t in TaskType])
            with tc2:
                task_duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
                task_priority = st.selectbox("Priority", ["high", "medium", "low"])
                task_frequency = st.selectbox(
                    "Frequency", [f.value for f in Frequency],
                    help="DAILY/WEEKLY tasks auto-renew when marked complete"
                )
                task_notes = st.text_input("Notes (optional)", value="")
            add_task_btn = st.form_submit_button("Add task")

        if add_task_btn:
            target_pet = next((p for p in owner().pets if p.name == task_pet), None)
            if target_pet:
                target_pet.add_task(Task(
                    name=task_name.strip() or "Unnamed task",
                    task_type=TaskType(task_type),
                    duration_minutes=int(task_duration),
                    priority=Priority(task_priority),
                    frequency=Frequency(task_frequency),
                    notes=task_notes.strip(),
                ))
                st.success(f"Added '{task_name}' to {target_pet.name}'s list.")

    # ---- Per-pet task list with sort control ----
    st.markdown("#### Current tasks")

    sort_mode = st.radio(
        "Sort tasks by",
        ["Priority (high first)", "Duration (shortest first)", "Duration (longest first)"],
        horizontal=True,
    )

    any_tasks = False
    for pet in owner().pets:
        if sort_mode == "Priority (high first)":
            pending = pet.tasks_sorted_by_priority()
        elif sort_mode == "Duration (shortest first)":
            pending = pet.tasks_sorted_by_duration(ascending=True)
        else:
            pending = pet.tasks_sorted_by_duration(ascending=False)

        if not pending:
            continue
        any_tasks = True
        st.markdown(f"**{pet.name}**")

        for task in pending:
            # Priority badge colour
            badge = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.priority.value, "⚪")
            recur_tag = f" ↻ {task.frequency.value}" if task.frequency != Frequency.ONCE else ""
            col_info, col_done, col_rm = st.columns([7, 1, 1])
            with col_info:
                st.markdown(
                    f"{badge} **{task.name}** ({task.duration_minutes} min) "
                    f"— *{task.task_type.value}*{recur_tag}"
                    + (f"  \n  _{task.notes}_" if task.notes else "")
                )
            with col_done:
                if st.button("✓", key=f"done_{pet.name}_{task.name}", help="Mark complete"):
                    pet.complete_task(task.name)   # handles recurrence renewal
                    st.rerun()
            with col_rm:
                if st.button("✕", key=f"rm_{pet.name}_{task.name}", help="Remove task"):
                    pet.remove_task(task.name)
                    st.rerun()

    if not any_tasks:
        st.info("All tasks are complete — or no tasks have been added yet.")

st.divider()

# ============================================================
# SCHEDULE GENERATION
# ============================================================

st.subheader("Generate Today's Schedule")

total_needed = owner().total_task_minutes()
budget = owner().available_minutes
overflow = total_needed - budget

if overflow > 0:
    st.warning(
        f"You have **{total_needed} min** of tasks but only **{budget} min** available. "
        f"The scheduler will prioritise high-priority tasks and skip **~{overflow} min** worth of low-priority ones."
    )

if total_needed == 0:
    st.info("Add some tasks before generating a schedule.")
elif st.button("Generate schedule", type="primary"):
    scheduler = Scheduler(owner=owner())
    plan = scheduler.generate_plan()
    st.session_state.last_plan = (plan, scheduler)
    st.rerun()

# ---- Render last plan ----
if st.session_state.last_plan:
    plan, scheduler = st.session_state.last_plan

    st.markdown("#### 📋 Today's Plan")

    # -- Scheduled tasks table --
    if plan.scheduled:
        # Allow user to sort the displayed plan
        plan_sort = st.radio(
            "View plan sorted by",
            ["Time (start time)", "Duration (longest first)"],
            horizontal=True,
            key="plan_sort",
        )
        if plan_sort == "Duration (longest first)":
            display_tasks = Scheduler.sort_scheduled_by_duration(plan.scheduled, ascending=False)
        else:
            display_tasks = Scheduler.sort_scheduled_by_start(plan.scheduled)

        rows = []
        for st_task in display_tasks:
            h_s, m_s = divmod(st_task.start_minute, 60)
            h_e, m_e = divmod(st_task.end_minute, 60)
            recur = f" ↻ {st_task.task.frequency.value}" if st_task.task.frequency != Frequency.ONCE else ""
            rows.append({
                "Time": f"{h_s:02d}:{m_s:02d} – {h_e:02d}:{m_e:02d}",
                "Pet": st_task.pet.name,
                "Task": st_task.task.name + recur,
                "Type": st_task.task.task_type.value,
                "Priority": st_task.task.priority.value.upper(),
                "Duration (min)": st_task.task.duration_minutes,
                "Notes": st_task.task.notes,
            })
        st.table(rows)
        st.success(
            f"✅ Scheduled **{len(plan.scheduled)} task(s)** using "
            f"**{plan.total_minutes_used}** of **{owner().available_minutes} minutes**."
        )
    else:
        st.warning("No tasks could be scheduled — check durations vs. available time.")

    # -- Skipped tasks --
    if plan.skipped:
        st.markdown("**⏭ Skipped** (not enough time remaining):")
        for pet, task in plan.skipped:
            st.markdown(
                f"- **{pet.name}**: {task.name} "
                f"({task.duration_minutes} min · {task.priority.value} priority)"
            )

    # -- Conflict warnings --
    if plan.conflicts:
        st.error(
            f"⚠️ **{len(plan.conflicts)} scheduling conflict(s) detected.** "
            "Two or more tasks overlap in time — review your task list or increase your daily budget."
        )
        for conflict in plan.conflicts:
            st.warning(str(conflict))
    else:
        st.success("✅ No scheduling conflicts detected.")

    # -- Filter view --
    with st.expander("🔍 Filter this plan by pet"):
        pet_names = list({st_task.pet.name for st_task in plan.scheduled})
        if pet_names:
            selected_pet = st.selectbox("Show tasks for", ["All"] + pet_names, key="filter_pet")
            if selected_pet != "All":
                filtered = Scheduler.filter_by_pet(plan.scheduled, selected_pet)
                if filtered:
                    for st_task in Scheduler.sort_scheduled_by_start(filtered):
                        h, m = divmod(st_task.start_minute, 60)
                        st.markdown(f"- {h:02d}:{m:02d} — **{st_task.task.name}** ({st_task.task.duration_minutes} min)")
                else:
                    st.info(f"No scheduled tasks for {selected_pet}.")

    # -- Explanation --
    with st.expander("💡 Why was each task included or skipped?"):
        st.text(scheduler.explain_plan(plan))
