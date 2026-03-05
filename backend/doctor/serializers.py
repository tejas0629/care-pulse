from rest_framework import serializers
from appointments.models import Appointment
from datetime import datetime

from doctor.models import Availability


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'

    def validate(self, attrs):
        # Validate conflict and availability when creating/updating an appointment
        doctor = attrs.get('doctor') or getattr(self.instance, 'doctor', None)
        date = attrs.get('date') or getattr(self.instance, 'date', None)
        time = attrs.get('time') or getattr(self.instance, 'time', None)

        if doctor and date and time:
            # conflict: another appointment at same datetime
            qs = Appointment.objects.filter(doctor=doctor, date=date, time=time)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError('This timeslot is already booked for the doctor')

            # availability: check if any availability covers this weekday/time
            weekday = date.weekday()
            avail_exists = Availability.objects.filter(
                doctor=doctor,
                weekday=weekday,
                start_time__lte=time,
                end_time__gte=time,
                active=True
            ).exists()

            if not avail_exists:
                raise serializers.ValidationError('Doctor is not available at the selected date/time')

        return attrs


class AvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Availability
        fields = '__all__'

    def validate(self, attrs):
        start = attrs.get('start_time')
        end = attrs.get('end_time')
        if start and end and start >= end:
            raise serializers.ValidationError('start_time must be before end_time')

        # prevent overlapping time slots for same doctor and weekday
        doctor = attrs.get('doctor') or getattr(self.instance, 'doctor', None)
        weekday = attrs.get('weekday') or getattr(self.instance, 'weekday', None)

        if doctor and weekday is not None and start and end:
            # normalize doctor to id to handle both PK or User instance in attrs
            doctor_id = getattr(doctor, 'id', doctor)
            qs = Availability.objects.filter(doctor__id=doctor_id, weekday=weekday, active=True)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)

            # overlap exists if existing.start < new_end and existing.end > new_start
            overlap = qs.filter(start_time__lt=end, end_time__gt=start).exists()
            if overlap:
                raise serializers.ValidationError('Overlapping availability exists for this doctor on the same weekday')
        return attrs