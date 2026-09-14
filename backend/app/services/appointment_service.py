"""
Appointment Management Service.

Handles the complete consultation booking lifecycle:
- Slot validation (operating days, business hours, conflict detection)
- Appointment creation with automated patient and doctor metadata resolution
- Patient and doctor-specific appointment retrieval
- Role-enforced, state-machine status updates
"""

from datetime import date, datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from google.cloud.firestore_v1.base_query import FieldFilter

from app.database import db
from app.models.appointment import (
    AppointmentBookingRequest,
    AppointmentResponse,
    AppointmentStatus,
    AppointmentStatusUpdate,
)


async def book_appointment(
    patient_uid: str,
    booking_data: AppointmentBookingRequest,
) -> AppointmentResponse:
    """
    Create a new appointment slot for an authenticated patient.

    Enforces:
    1. Patient account active verification
    2. Doctor existence and approval verification
    3. Day of week availability validation
    4. Operational hours validation
    5. Double-booking prevention for both doctor and patient
    """
    # Step 1: Validate patient
    patient_doc = db.collection("users").document(patient_uid).get()
    if not patient_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found.",
        )
    patient_data = patient_doc.to_dict()
    if not patient_data.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patient account is deactivated.",
        )
    patient_name = patient_data.get("name", "Patient")

    # Step 2: Validate doctor
    doctor_ref = db.collection("doctors").document(booking_data.doctor_uid).get()
    if not doctor_ref.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found.",
        )
    doctor_data = doctor_ref.to_dict()
    if not doctor_data.get("is_approved", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor is not approved to take appointments.",
        )

    doctor_user_ref = db.collection("users").document(booking_data.doctor_uid).get()
    if not doctor_user_ref.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile is incomplete.",
        )
    doctor_user_data = doctor_user_ref.to_dict()
    if not doctor_user_data.get("is_active", True) or doctor_user_data.get("role") != "doctor":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor account is currently inactive.",
        )

    doctor_name = doctor_user_data.get("name", "Doctor")
    doctor_specialization = doctor_data.get("specialization") or "General Medicine"
    consultation_fee = doctor_data.get("consultation_fee")

    # Step 3: Slot Validation (Date & Day of Week)
    try:
        apt_date = datetime.strptime(booking_data.appointment_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Expected YYYY-MM-DD.",
        )

    if apt_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot book an appointment for a past date.",
        )

    day_name = apt_date.strftime("%A")  # e.g., 'Monday'
    available_days = doctor_data.get("available_days") or [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
    ]
    if day_name.lower() not in [d.lower() for d in available_days]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Doctor is not available on {day_name}s. Available days: {', '.join(available_days)}.",
        )

    # Step 4: Slot Validation (Hours)
    try:
        req_time = datetime.strptime(booking_data.appointment_time, "%H:%M").time()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid time format. Expected HH:MM (24-hour format).",
        )

    available_hours = doctor_data.get("available_hours") or {"start": "09:00", "end": "17:00"}
    start_time_str = available_hours.get("start", "09:00")
    end_time_str = available_hours.get("end", "17:00")

    try:
        start_time = datetime.strptime(start_time_str, "%H:%M").time()
        end_time = datetime.strptime(end_time_str, "%H:%M").time()
    except ValueError:
        start_time = datetime.strptime("09:00", "%H:%M").time()
        end_time = datetime.strptime("17:00", "%H:%M").time()

    if req_time < start_time or req_time >= end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Requested time {booking_data.appointment_time} is outside doctor's operating hours "
                f"({start_time_str} - {end_time_str})."
            ),
        )

    # Step 5: Duplicate Slot & Conflict Detection
    # Query appointments for this doctor on this date
    doctor_appointments = (
        db.collection("appointments")
        .where(filter=FieldFilter("doctor_uid", "==", booking_data.doctor_uid))
        .where(filter=FieldFilter("appointment_date", "==", booking_data.appointment_date))
        .stream()
    )
    for apt in doctor_appointments:
        data = apt.to_dict()
        if data.get("appointment_time") == booking_data.appointment_time:
            if data.get("status") in (AppointmentStatus.pending.value, AppointmentStatus.confirmed.value):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This time slot is already booked for the selected doctor. Please choose a different slot.",
                )

    # Query appointments for this patient on this date to prevent patient double-booking
    patient_appointments = (
        db.collection("appointments")
        .where(filter=FieldFilter("patient_uid", "==", patient_uid))
        .where(filter=FieldFilter("appointment_date", "==", booking_data.appointment_date))
        .stream()
    )
    for apt in patient_appointments:
        data = apt.to_dict()
        if data.get("appointment_time") == booking_data.appointment_time:
            if data.get("status") in (AppointmentStatus.pending.value, AppointmentStatus.confirmed.value):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You already have an active appointment scheduled at this date and time.",
                )

    # Step 6: Create Appointment Record in Firestore
    now = datetime.now(timezone.utc).isoformat()
    doc_ref = db.collection("appointments").document()
    appointment_id = doc_ref.id

    appointment_record = {
        "id": appointment_id,
        "patient_uid": patient_uid,
        "doctor_uid": booking_data.doctor_uid,
        "patient_name": patient_name,
        "doctor_name": doctor_name,
        "doctor_specialization": doctor_specialization,
        "appointment_date": booking_data.appointment_date,
        "appointment_time": booking_data.appointment_time,
        "status": AppointmentStatus.pending.value,
        "reason": booking_data.reason,
        "consultation_fee": consultation_fee,
        "notes": None,
        "created_at": now,
        "updated_at": now,
    }

    doc_ref.set(appointment_record)
    return AppointmentResponse(**appointment_record)


async def get_patient_appointments(patient_uid: str) -> list[AppointmentResponse]:
    """
    Retrieve all appointments booked by a specific patient.
    """
    docs = (
        db.collection("appointments")
        .where(filter=FieldFilter("patient_uid", "==", patient_uid))
        .stream()
    )

    results: list[AppointmentResponse] = []
    for doc in docs:
        results.append(AppointmentResponse(**doc.to_dict()))

    # Sort in memory: newest date and time first
    results.sort(
        key=lambda x: (x.appointment_date, x.appointment_time),
        reverse=True,
    )
    return results


async def get_doctor_appointments(doctor_uid: str) -> list[AppointmentResponse]:
    """
    Retrieve all appointments scheduled with a specific doctor.
    """
    docs = (
        db.collection("appointments")
        .where(filter=FieldFilter("doctor_uid", "==", doctor_uid))
        .stream()
    )

    results: list[AppointmentResponse] = []
    for doc in docs:
        results.append(AppointmentResponse(**doc.to_dict()))

    # Sort in memory: newest date and time first
    results.sort(
        key=lambda x: (x.appointment_date, x.appointment_time),
        reverse=True,
    )
    return results


async def update_appointment_status(
    appointment_id: str,
    update_data: AppointmentStatusUpdate,
    current_user: dict,
) -> AppointmentResponse:
    """
    Update the lifecycle status of an appointment.

    Ownership & Role Rules:
    - Patients may only cancel their own pending or confirmed appointments.
    - Doctors may confirm, complete, or cancel appointments assigned to themselves.
    - Admins may update any appointment status for clinical administration.
    """
    doc_ref = db.collection("appointments").document(appointment_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found.",
        )

    apt = doc.to_dict()
    user_uid = current_user.get("uid")
    role = current_user.get("role")
    current_status = apt.get("status")
    new_status = update_data.status.value

    # Terminal state protection
    if current_status == AppointmentStatus.completed.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify an appointment that is already completed.",
        )
    if current_status == AppointmentStatus.cancelled.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify an appointment that is already cancelled.",
        )

    # Role-based authorization and state transition validation
    if role == "patient":
        if apt.get("patient_uid") != user_uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this appointment.",
            )
        if new_status != AppointmentStatus.cancelled.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Patients are only authorized to cancel their appointments.",
            )

    elif role == "doctor":
        if apt.get("doctor_uid") != user_uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctors can only manage appointments assigned to them.",
            )
        # Doctor allowed transitions:
        # pending -> confirmed, cancelled
        # confirmed -> completed, cancelled
        if current_status == AppointmentStatus.pending.value:
            if new_status not in (AppointmentStatus.confirmed.value, AppointmentStatus.cancelled.value):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Pending appointments can only transition to 'confirmed' or 'cancelled', not '{new_status}'.",
                )
        elif current_status == AppointmentStatus.confirmed.value:
            if new_status not in (AppointmentStatus.completed.value, AppointmentStatus.cancelled.value):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Confirmed appointments can only transition to 'completed' or 'cancelled', not '{new_status}'.",
                )

    elif role == "admin":
        # Admins have full oversight to advance or cancel
        pass

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify appointment status.",
        )

    now = datetime.now(timezone.utc).isoformat()
    updates = {
        "status": new_status,
        "updated_at": now,
    }
    if update_data.notes:
        updates["notes"] = update_data.notes

    doc_ref.update(updates)
    apt.update(updates)
    return AppointmentResponse(**apt)
