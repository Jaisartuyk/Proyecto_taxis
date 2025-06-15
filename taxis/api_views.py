from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
  # Asegúrate que el import sea correcto

User = get_user_model()

# 🚕 Login para conductores
class LoginAPIView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {"error": "Se requieren usuario y contraseña."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                token, created = Token.objects.get_or_create(user=user)
                role = getattr(user, 'role', None)

                if role == 'driver':
                    return Response({
                        "message": "Inicio de sesión exitoso.",
                        "user_id": user.id,
                        "role": role,
                        "token": token.key
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        "error": "Acceso denegado: Solo conductores pueden iniciar sesión.",
                        "role": role
                    }, status=status.HTTP_403_FORBIDDEN)

            except Exception as e:
                return Response(
                    {"error": f"Error al generar el token: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(
            {"error": "Usuario o contraseña incorrectos."},
            status=status.HTTP_401_UNAUTHORIZED
        )
