from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination

from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Q

from appointments.models import Appointment
from .serializers import AppointmentSerializer, AvailabilitySerializer
from .permissions import IsDoctor
from doctor.models import Availability
from datetime import datetime, date, timedelta
from django.db.models import Count


# =========================
# DASHBOARD OVERVIEW
# =========================

class DoctorDashboardOverview(APIView):

    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request):

        doctor = request.user

        today_date = now().date()

        base_qs = Appointment.objects.filter(doctor=doctor)

        # Aggregated counts
        counts = {
            'total': base_qs.count(),
            'today': base_qs.filter(date=today_date).count(),
            'upcoming': base_qs.filter(date__gt=today_date, status__in=['pending']).count(),
            'completed': base_qs.filter(status='completed').count(),
            'cancelled': base_qs.filter(status='cancelled').count(),
        }

        # monthly completed stats (last 6 months)
        stats = []
        for i in range(5, -1, -1):
            month_start = (today_date.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
            y = month_start.year
            m = month_start.month
            count = base_qs.filter(status='completed', date__year=y, date__month=m).count()
            stats.append({'year': y, 'month': m, 'completed': count})

        return Response({
            "success": True,
            "message": "Doctor dashboard overview",
            "data": {
                **counts,
                "monthly_stats": stats
            }
        })


# =========================
# ALL APPOINTMENTS (PAGINATION)
# =========================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDoctor])
def doctor_appointments(request):
    # Advanced filtering: status, search by patient name, date range
    qs = Appointment.objects.filter(doctor=request.user).order_by('-date', '-time')

    status = request.GET.get('status')
    search = request.GET.get('search')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if status:
        qs = qs.filter(status__iexact=status)

    if search:
        qs = qs.filter(patient_name__icontains=search)

    if start_date:
        qs = qs.filter(date__gte=start_date)
    if end_date:
        qs = qs.filter(date__lte=end_date)

    paginator = PageNumberPagination()
    paginator.page_size = 10

    result_page = paginator.paginate_queryset(qs, request)
    serializer = AppointmentSerializer(result_page, many=True)

    return paginator.get_paginated_response(serializer.data)


# =========================
# TODAY APPOINTMENTS
# =========================

class TodayAppointmentsView(APIView):

    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request):

        doctor = request.user
        appointments = Appointment.objects.filter(
            doctor=doctor,
            date=now().date()
        )

        serializer = AppointmentSerializer(appointments, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        })


# =========================
# MARK COMPLETE
# =========================

class MarkAppointmentComplete(APIView):

    permission_classes = [IsAuthenticated, IsDoctor]

    @transaction.atomic
    def post(self, request, id):

        doctor = request.user
        appointment = get_object_or_404(
            Appointment, id=id, doctor=doctor
        )

        appointment.status = "completed"
        appointment.save()

        return Response({
            "success": True,
            "message": "Appointment completed successfully"
        })


# =========================
# RESCHEDULE
# =========================

class RescheduleAppointment(APIView):

    permission_classes = [IsAuthenticated, IsDoctor]

    @transaction.atomic
    def post(self, request, id):

        doctor = request.user
        appointment = get_object_or_404(
            Appointment, id=id, doctor=doctor
        )

        new_date = request.data.get("date")
        new_time = request.data.get("time")

        if not new_date or not new_time:
            return Response({
                "success": False,
                "message": "Date and time are required"
            }, status=400)

        # parse values
        try:
            parsed_date = datetime.fromisoformat(new_date).date() if 'T' in new_date else datetime.strptime(new_date, '%Y-%m-%d').date()
        except Exception:
            return Response({"success": False, "message": "Invalid date format. Use YYYY-MM-DD."}, status=400)

        try:
            parsed_time = datetime.fromisoformat(new_time).time() if 'T' in new_time else datetime.strptime(new_time, '%H:%M:%S').time()
        except Exception:
            try:
                parsed_time = datetime.strptime(new_time, '%H:%M').time()
            except Exception:
                return Response({"success": False, "message": "Invalid time format. Use HH:MM or HH:MM:SS."}, status=400)

        # conflict check: another appointment at same time
        conflict = Appointment.objects.filter(doctor=doctor, date=parsed_date, time=parsed_time).exclude(id=appointment.id).exists()
        if conflict:
            return Response({"success": False, "message": "Requested timeslot is already booked."}, status=400)

        # availability check
        weekday = parsed_date.weekday()
        available = Availability.objects.filter(doctor=doctor, weekday=weekday, start_time__lte=parsed_time, end_time__gte=parsed_time, active=True).exists()
        if not available:
            return Response({"success": False, "message": "Doctor is not available at the requested date/time."}, status=400)

        # new date must not be in the past
        if parsed_date < now().date():
            return Response({"success": False, "message": "New date cannot be in the past."}, status=400)

        appointment.date = parsed_date
        appointment.time = parsed_time
        # when rescheduling, set status back to pending (if not cancelled/completed logic may vary)
        appointment.status = 'pending'
        appointment.save()

        return Response({"success": True, "message": "Appointment rescheduled successfully", "data": {"id": appointment.id, "date": str(appointment.date), "time": str(appointment.time), "status": appointment.status}})


# =========================
# DOCTOR PROFILE
# =========================

class DoctorProfileView(APIView):

    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request):

        doctor = request.user

        return Response({
            "success": True,
            "data": {
                "id": doctor.id,
                "username": doctor.username,
                "email": doctor.email,
            }
        })


# =========================
# AVAILABILITY (Placeholder)
# =========================

class DoctorAvailabilityView(APIView):

    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request):
        # list availabilities for logged-in doctor
        doctor = request.user
        qs = Availability.objects.filter(doctor=doctor, active=True).order_by('weekday', 'start_time')
        serializer = AvailabilitySerializer(qs, many=True)
        return Response({"success": True, "data": serializer.data})

    def post(self, request):
        data = request.data.copy()
        data['doctor'] = request.user.id
        serializer = AvailabilitySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "message": "Availability created", "data": serializer.data}, status=201)
        return Response({"success": False, "errors": serializer.errors}, status=400)

    def delete(self, request):
        # allow deletion by id param in body
        avail_id = request.data.get('id')
        if not avail_id:
            return Response({"success": False, "message": "id is required"}, status=400)
        obj = get_object_or_404(Availability, id=avail_id, doctor=request.user)
        obj.delete()
        return Response({"success": True, "message": "Availability removed", "data": {"id": avail_id}})


class AvailabilityDetailView(APIView):

    permission_classes = [IsAuthenticated, IsDoctor]

    def put(self, request, id):
        obj = get_object_or_404(Availability, id=id, doctor=request.user)
        serializer = AvailabilitySerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "message": "Availability updated", "data": serializer.data})
        return Response({"success": False, "message": "Validation error", "errors": serializer.errors}, status=400)

    def patch(self, request, id):
        obj = get_object_or_404(Availability, id=id, doctor=request.user)
        serializer = AvailabilitySerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "message": "Availability updated", "data": serializer.data})
        return Response({"success": False, "message": "Validation error", "errors": serializer.errors}, status=400)

    def delete(self, request, id):
        obj = get_object_or_404(Availability, id=id, doctor=request.user)
        obj.delete()
        return Response({"success": True, "message": "Availability removed", "data": {"id": id}})


# =========================
# CALENDAR VIEW
# =========================

class DoctorCalendarView(APIView):

    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request):

        doctor = request.user
        date = request.GET.get("date")

        if date:
            appointments = Appointment.objects.filter(
                doctor=doctor,
                date=date
            )
        else:
            appointments = Appointment.objects.filter(
                doctor=doctor
            )

        serializer = AppointmentSerializer(appointments, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        })


# =========================
# APPOINTMENT DETAIL
# =========================

class DoctorAppointmentDetail(APIView):

    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request, id):

        doctor = request.user
        appointment = get_object_or_404(
            Appointment, id=id, doctor=doctor
        )

        serializer = AppointmentSerializer(appointment)

        return Response({
            "success": True,
            "data": serializer.data
        })
    # =========================
# CANCEL APPOINTMENT
# =========================

class CancelAppointment(APIView):

    permission_classes = [IsAuthenticated, IsDoctor]

    def post(self, request, id):

        doctor = request.user

        appointment = get_object_or_404(
            Appointment,
            id=id,
            doctor=doctor
        )

        appointment.status = "cancelled"
        appointment.save()

        return Response({
            "success": True,
            "message": "Appointment cancelled successfully"
        })
    # =========================
# PATIENT HISTORY
# =========================

class PatientHistoryView(APIView):

    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request, patient_name):

        doctor = request.user

        appointments = Appointment.objects.filter(
            doctor=doctor,
            patient_name__iexact=patient_name
        ).order_by('-date')

        serializer = AppointmentSerializer(appointments, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        })