from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from doctor.views import RescheduleAppointment

urlpatterns = [
    path('admin/', admin.site.urls),
    path('doctor/', include('doctor.urls')),
    # additional API-style route for rescheduling (keeps existing routes intact)
    path('api/doctor/appointments/<int:id>/reschedule/', RescheduleAppointment.as_view()),
 path('api-token-auth/', obtain_auth_token),
  path("api/", include("authentication.urls")),
]