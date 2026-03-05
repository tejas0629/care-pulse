from django.db import models
from django.contrib.auth.models import User


class DoctorProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    specialization = models.CharField(
        max_length=100,
        default="General"
    )

    hospital = models.CharField(
        max_length=200,
        default="Not Added"
    )

    college = models.CharField(
        max_length=200,
        default="Unknown"
    )

    experience = models.IntegerField(
        default=0
    )

    def __str__(self):
        return self.user.username


class Availability(models.Model):
    WEEKDAYS = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='availabilities'
    )

    weekday = models.IntegerField(choices=WEEKDAYS)

    start_time = models.TimeField()

    end_time = models.TimeField()

    slot_length_minutes = models.PositiveIntegerField(default=30)

    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['doctor', 'weekday', 'start_time']
        verbose_name = 'Availability'
        verbose_name_plural = 'Availabilities'

    def __str__(self):
        return f"{self.doctor.username} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"