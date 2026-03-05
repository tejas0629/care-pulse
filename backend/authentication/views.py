from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response


class LoginView(ObtainAuthToken):

    def post(self, request, *args, **kwargs):

        response = super().post(request, *args, **kwargs)

        token = Token.objects.get(key=response.data["token"])

        return Response({
            "token": token.key,
            "user_id": token.user_id,
            "username": token.user.username,
        })