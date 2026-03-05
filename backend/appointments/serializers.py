from rest_framework import serializers
from .models import Appointment

class AppointmentSerializer(serializers.ModelSerializer):

    # Appointment model stores `patient_name` as a CharField.
    # Expose it directly rather than referencing a non-existent `patient` relation.
    patient_name = serializers.CharField(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id',
            'patient_name',
            'date',
            'time',
            'status'
        ]