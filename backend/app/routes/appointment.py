"""
Appointment API Routes.

Exposes endpoints for managing consultation bookings:
- POST /appointments/book: Patient books an appointment slot with an approved doctor.
- GET /appointments/patient: Patient views their booked appointments.
- GET /appointments/doctor: Doctor views consultations assigned to them.
- PATCH /appointments/{id}/status: Authorized status updates (confirm, complete, cancel).

All endpoints require JWT Bearer authentication.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.appointment import (
    AppointmentBookingRequest,
    AppointmentResponse,
    AppointmentStatusUpdate,
)
from app.services.appointment_service import (
    book_appointment,
    get_doctor_appointments,
    get_patient_appointments,
    update_appointment_status,
)
from app.utils.auth_dependencies import get_current_user

router = APIRouter(tags=["Appointments"])


@router.post(
    "/book",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book a doctor consultation",
    description=(
        "Schedule an appointment with an approved doctor. Patient identity is derived "
        "directly from the authenticated JWT token. Enforces operating day/hour checks "
        "and conflict detection."
    ),
)
async def book_appointment_endpoint(
    booking_data: AppointmentBookingRequest,
    current_user: dict = Depends(get_current_user),
) -> AppointmentResponse:
    """
    Book an appointment slot.
    The booking patient's UID is automatically taken from the authenticated token.
    """
    role = current_user.get("role")
    if role == "pending":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accounts awaiting verification cannot book appointments.",
        )

    patient_uid = current_user.get("uid")
    return await book_appointment(patient_uid=patient_uid, booking_data=booking_data)


@router.get(
    "/patient",
    response_model=list[AppointmentResponse],
    status_code=status.HTTP_200_OK,
    summary="List patient appointments",
    description="Retrieve all consultations booked by the authenticated patient.",
)
async def get_my_patient_appointments(
    current_user: dict = Depends(get_current_user),
) -> list[AppointmentResponse]:
    """
    Retrieve appointments for the authenticated patient.
    """
    patient_uid = current_user.get("uid")
    return await get_patient_appointments(patient_uid=patient_uid)


@router.get(
    "/doctor",
    response_model=list[AppointmentResponse],
    status_code=status.HTTP_200_OK,
    summary="List doctor appointments",
    description=(
        "Retrieve scheduled appointments assigned to the authenticated doctor. "
        "Admins may optionally supply a ?doctor_uid= query parameter to inspect any doctor's schedule."
    ),
)
async def get_my_doctor_appointments(
    doctor_uid: Optional[str] = Query(
        default=None,
        description="Admin-only: query a specific doctor's appointments by UID",
    ),
    current_user: dict = Depends(get_current_user),
) -> list[AppointmentResponse]:
    """
    Retrieve appointments for a doctor.
    Doctors view only their own assigned bookings.
    Admins can view any doctor's bookings.
    """
    role = current_user.get("role")
    user_uid = current_user.get("uid")

    if role == "doctor":
        target_doctor_uid = user_uid
    elif role == "admin":
        if not doctor_uid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin requests must specify a 'doctor_uid' query parameter.",
            )
        target_doctor_uid = doctor_uid
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to doctors and clinical administrators.",
        )

    return await get_doctor_appointments(doctor_uid=target_doctor_uid)


@router.patch(
    "/{id}/status",
    response_model=AppointmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update appointment status",
    description=(
        "Update the lifecycle status of an appointment. Patients may cancel their appointments. "
        "Assigned doctors may confirm, complete, or cancel appointments. Arbitrary transitions are rejected."
    ),
)
async def update_status_endpoint(
    id: str,
    update_data: AppointmentStatusUpdate,
    current_user: dict = Depends(get_current_user),
) -> AppointmentResponse:
    """
    Update appointment status with strict participant-level authorization.
    """
    return await update_appointment_status(
        appointment_id=id,
        update_data=update_data,
        current_user=current_user,
    )
