# taxis/api_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model

# Obtener el modelo de usuario personalizado (AppUser si lo configuraste correctamente)
User = get_user_model()

class LoginAPIView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {"error": "Se requieren usuario y contraseña."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Autenticar usuario
        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                # Obtener o crear token
                token, created = Token.objects.get_or_create(user=user)

                user_role = getattr(user, 'role', None)  # Asegúrate de que el campo 'role' exista

                if user_role == 'driver':
                    return Response(
                        {
                            "message": "Inicio de sesión exitoso.",
                            "user_id": user.id,
                            "role": user_role,
                            "token": token.key
                        },
                        status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        {
                            "error": "Acceso denegado: Esta aplicación es solo para conductores.",
                            "role": user_role
                        },
                        status=status.HTTP_403_FORBIDDEN
                    )

            except Exception as e:
                return Response(
                    {"error": f"Error al generar el token: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(
            {"error": "Usuario o contraseña incorrectos."},
            status=status.HTTP_401_UNAUTHORIZED
        )
