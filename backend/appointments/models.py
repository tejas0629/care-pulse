from django.db import models
from django.contrib.auth.models import User


class Appointment(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="doctor_appointments"
    )

    patient_name = models.CharField(
        max_length=100,
        default="Unknown"
    )

    date = models.DateField()

    time = models.TimeField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['doctor', 'date', 'time'], name='unique_doctor_appointment_time')
        ]

    def clean(self):
        # Import here to avoid circular imports at module import time
        from django.core.exceptions import ValidationError
        try:
            from doctor.models import Availability
        except Exception:
            Availability = None

        # Check for availability if model exists
        if Availability is not None:
            weekday = self.date.weekday()
            # find any availability entry covering this time
            available = Availability.objects.filter(
                doctor=self.doctor,
                weekday=weekday,
                start_time__lte=self.time,
                end_time__gte=self.time,
            ).exists()

            if not available:
                raise ValidationError('Doctor is not available at the requested date/time')

    def __str__(self):
        return self.patient_name