# taxis/api_views.py (O en tu views.py principal, pero es mejor separarlos)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate # Solo necesitamos authenticate, ya que no estamos usando sesiones web para la API
from rest_framework.authtoken.models import Token # Para generar/obtener tokens

# Importa tu modelo AppUser para asegurarte de que estás trabajando con él
# from .models import AppUser # Si AppUser está en models.py de la misma app
# from your_project_name.taxis.models import AppUser # Si necesitas una ruta más explícita

class LoginAPIView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {"error": "Se requieren usuario y contraseña."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Autentica al usuario usando las credenciales.
        # Esto usará tu AppUser Customizado si lo configuraste como AUTH_USER_MODEL
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Obtén o crea el token para el usuario autenticado
            token, created = Token.objects.get_or_create(user=user)

            # ⭐⭐⭐ AQUÍ ESTÁ EL CAMBIO CLAVE: Usa user.role directamente ⭐⭐⭐
            user_role = user.role

            # Validar si el usuario tiene el rol de "driver" para esta app específica
            if user_role == 'driver':
                return Response(
                    {
                        "message": "Inicio de sesión exitoso.",
                        "user_id": user.id,      # El ID del usuario
                        "role": user_role,       # El rol del usuario obtenido de tu modelo AppUser
                        "token": token.key       # El token de autenticación
                    },
                    status=status.HTTP_200_OK
                )
            else:
                # Si el usuario no es un conductor, se le niega el acceso a esta app.
                return Response(
                    {"error": "Acceso denegado: Esta aplicación es solo para conductores.",
                     "role": user_role}, # Puedes incluir el rol para depuración
                    status=status.HTTP_403_FORBIDDEN # 403 Forbidden para acceso no autorizado (rol incorrecto)
                )
        else:
            # Credenciales inválidas (usuario o contraseña incorrectos)
            return Response(
                {"error": "Usuario o contraseña incorrectos."},
                status=status.HTTP_401_UNAUTHORIZED # 401 Unauthorized
            )