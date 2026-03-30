"""
PawPal+ — Streamlit UI
Connects the Owner / Pet / Task / Scheduler logic layer to the browser.
"""

import streamlit as st

from pawpal_system import Owner, Pet, Task, TaskType, Priority, Scheduler

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# ---------------------------------------------------------------------------
# Session-state bootstrap
# Streamlit re-runs this file top-to-bottom on every interaction, so we
# only create the Owner once and keep it in the "session vault" thereafter.
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None          # set properly in Step 1 below
if "last_plan" not in st.session_state:
    st.session_state.last_plan = None

# ---------------------------------------------------------------------------
# Helper: shorthand for the live Owner object
# ---------------------------------------------------------------------------

def owner() -> Owner | None:
    """Return the Owner stored in session_state (may be None before setup)."""
    return st.session_state.owner


# ============================================================
# STEP 1 — Owner setup
# ============================================================

st.title("🐾 PawPal+")
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
    # Preserve any pets that already exist when the owner info is re-saved
    existing_pets = owner().pets if owner() else []
    st.session_state.owner = Owner(
        name=owner_name, available_minutes=int(available_minutes)
    )
    for pet in existing_pets:
        st.session_state.owner.add_pet(pet)
    st.success(f"Owner saved: {owner_name} ({available_minutes} min/day)")

if owner():
    st.caption(
        f"Active owner: **{owner().name}** | Budget: **{owner().available_minutes} min/day** | "
        f"Pets: **{len(owner().pets)}**"
    )
else:
    st.info("Fill in your name and available time, then click **Save owner info** to get started.")
    st.stop()   # nothing else works without an Owner

st.divider()

# ============================================================
# STEP 2 — Pet management
# ============================================================

st.subheader("My Pets")

# --- Add-pet form ---
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
            new_pet = Pet(name=pet_name.strip(), species=species, breed=breed, age_years=float(age))
            owner().add_pet(new_pet)
            st.success(f"Added {new_pet.name} the {new_pet.species}!")

# --- Display / remove existing pets ---
if not owner().pets:
    st.info("No pets yet. Add one above.")
else:
    for pet in owner().pets:
        with st.expander(f"🐾 {pet.name} ({pet.species}, {pet.breed}, {pet.age_years} yrs)"):
            pending = pet.get_pending_tasks()
            done = [t for t in pet.tasks if t.completed]
            st.caption(f"{len(pending)} pending task(s), {len(done)} completed")

            # Remove pet
            if st.button(f"Remove {pet.name}", key=f"remove_pet_{pet.name}"):
                owner().remove_pet(pet.name)
                st.rerun()

st.divider()

# ============================================================
# STEP 3 — Task management
# ============================================================

st.subheader("Care Tasks")

if not owner().pets:
    st.info("Add at least one pet before adding tasks.")
else:
    # --- Add-task form ---
    with st.expander("Add a new task", expanded=True):
        with st.form("add_task_form"):
            tc1, tc2 = st.columns(2)
            with tc1:
                task_pet = st.selectbox("For which pet?", [p.name for p in owner().pets])
                task_name = st.text_input("Task name", value="Morning walk")
                task_type = st.selectbox(
                    "Task type",
                    [t.value for t in TaskType],
                    index=0,
                )
            with tc2:
                task_duration = st.number_input(
                    "Duration (min)", min_value=1, max_value=240, value=20
                )
                task_priority = st.selectbox("Priority", ["high", "medium", "low"])
                task_notes = st.text_input("Notes (optional)", value="")

            add_task_btn = st.form_submit_button("Add task")

        if add_task_btn:
            target_pet = next((p for p in owner().pets if p.name == task_pet), None)
            if target_pet:
                new_task = Task(
                    name=task_name.strip() or "Unnamed task",
                    task_type=TaskType(task_type),
                    duration_minutes=int(task_duration),
                    priority=Priority(task_priority),
                    notes=task_notes.strip(),
                )
                target_pet.add_task(new_task)
                st.success(f"Added '{new_task.name}' to {target_pet.name}'s list.")

    # --- Task list per pet ---
    st.markdown("#### Current tasks")
    any_tasks = False
    for pet in owner().pets:
        pending = pet.get_pending_tasks()
        if not pending:
            continue
        any_tasks = True
        st.markdown(f"**{pet.name}**")
        for task in pending:
            col_info, col_done, col_rm = st.columns([6, 1, 1])
            with col_info:
                st.markdown(
                    f"- `{task.priority.value.upper():6}` {task.name} "
                    f"({task.duration_minutes} min) — *{task.task_type.value}*"
                    + (f" | {task.notes}" if task.notes else "")
                )
            with col_done:
                if st.button("✓", key=f"done_{pet.name}_{task.name}", help="Mark complete"):
                    task.mark_complete()
                    st.rerun()
            with col_rm:
                if st.button("✕", key=f"rm_{pet.name}_{task.name}", help="Remove task"):
                    pet.remove_task(task.name)
                    st.rerun()

    if not any_tasks:
        st.info("All tasks are complete — or no tasks have been added yet.")

st.divider()

# ============================================================
# STEP 4 — Generate schedule
# ============================================================

st.subheader("Generate Today's Schedule")

total_needed = owner().total_task_minutes()
st.caption(
    f"Total pending task time: **{total_needed} min** | "
    f"Daily budget: **{owner().available_minutes} min**"
)

if total_needed == 0:
    st.info("Add some tasks before generating a schedule.")
elif st.button("Generate schedule", type="primary"):
    scheduler = Scheduler(owner=owner())
    plan = scheduler.generate_plan()
    st.session_state.last_plan = (plan, scheduler)
    st.rerun()

# --- Render last plan if it exists ---
if st.session_state.last_plan:
    plan, scheduler = st.session_state.last_plan

    st.markdown("#### 📋 Today's Plan")

    if plan.scheduled:
        rows = []
        for st_task in plan.scheduled:
            h_s, m_s = divmod(st_task.start_minute, 60)
            h_e, m_e = divmod(st_task.end_minute, 60)
            rows.append({
                "Time": f"{h_s:02d}:{m_s:02d} – {h_e:02d}:{m_e:02d}",
                "Pet": st_task.pet.name,
                "Task": st_task.task.name,
                "Type": st_task.task.task_type.value,
                "Priority": st_task.task.priority.value,
                "Duration (min)": st_task.task.duration_minutes,
                "Notes": st_task.task.notes,
            })
        st.table(rows)
        st.success(
            f"Scheduled {len(plan.scheduled)} task(s) using "
            f"{plan.total_minutes_used} of {owner().available_minutes} minutes."
        )
    else:
        st.warning("No tasks could be scheduled — check durations vs. available time.")

    if plan.skipped:
        st.markdown("**Skipped (not enough time):**")
        for pet, task in plan.skipped:
            st.markdown(f"- {pet.name}: *{task.name}* ({task.duration_minutes} min, {task.priority.value})")

    with st.expander("Why was each task included or skipped?"):
        st.text(scheduler.explain_plan(plan))
