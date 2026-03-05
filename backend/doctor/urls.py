from .views import *
from django.urls import path
from .views import (
    DoctorDashboardOverview,
    doctor_appointments,   
    TodayAppointmentsView,
    MarkAppointmentComplete,
    RescheduleAppointment,
    DoctorProfileView,
    DoctorAvailabilityView,
    DoctorCalendarView,
    DoctorAppointmentDetail,
    AvailabilityDetailView,
)

urlpatterns = [

    # dashboard
    path("overview/", DoctorDashboardOverview.as_view()),

    # today appointments
    path("today/", TodayAppointmentsView.as_view()),

    # all appointments / calendar
    path('appointments/', doctor_appointments),

    # appointment actions
    path("complete/<int:id>/", MarkAppointmentComplete.as_view()),
    path("reschedule/<int:id>/", RescheduleAppointment.as_view()),

    # doctor profile
    path("profile/", DoctorProfileView.as_view()),

    # availability / leave
    path("availability/", DoctorAvailabilityView.as_view()),
    path("availability/<int:id>/", AvailabilityDetailView.as_view()),
    # calendar view
    path("calendar/", DoctorCalendarView.as_view()),
    # appointment details
    path("appointment/<int:id>/", DoctorAppointmentDetail.as_view()),
    path("cancel/<int:id>/", CancelAppointment.as_view()),
path("patient-history/<str:patient_name>/", PatientHistoryView.as_view()),
]