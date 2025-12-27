"""
Middleware para autenticación de WebSockets con Token y Sesiones
"""
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack
from urllib.parse import parse_qs


class TokenAuthMiddleware(BaseMiddleware):
    """
    Middleware para autenticar WebSockets usando:
    1. Token de DRF (para apps móviles)
    2. Sesiones de Django (para web)
    
    Busca el token en:
    1. Query string: ?token=xxxxx
    2. Headers: Authorization: Token xxxxx
    3. Sesión de Django (fallback para web)
    """
    
    async def __call__(self, scope, receive, send):
        # Intentar obtener token de query string
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token_key = query_params.get('token', [None])[0]
        
        # Si no está en query string, buscar en headers
        if not token_key:
            headers = dict(scope.get('headers', []))
            auth_header = headers.get(b'authorization', b'').decode()
            
            if auth_header.startswith('Token '):
                token_key = auth_header.split(' ')[1]
        
        # Si hay token, autenticar con token
        if token_key:
            scope['user'] = await self.get_user_from_token(token_key)
        # Si no hay token, intentar con sesión de Django (para web)
        elif 'session' in scope:
            # Usar AuthMiddleware de Channels para sesiones
            scope['user'] = await self.get_user_from_session(scope)
        else:
            # Sin token ni sesión
            from django.contrib.auth.models import AnonymousUser
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)
    
    @database_sync_to_async
    def get_user_from_session(self, scope):
        """Obtener usuario desde la sesión de Django"""
        from django.contrib.auth.models import AnonymousUser
        from channels.auth import _get_user_session_key
        
        try:
            session_key = _get_user_session_key(scope.get('session', {}))
            if session_key:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                return User.objects.get(pk=session_key)
        except Exception as e:
            print(f"⚠️ Error obteniendo usuario de sesión: {e}")
        
        return AnonymousUser()
    
    @database_sync_to_async
    def get_user_from_token(self, token_key):
        """Obtener usuario desde el token"""
        # Importar aquí para evitar AppRegistryNotReady
        from django.contrib.auth.models import AnonymousUser
        from rest_framework.authtoken.models import Token
        
        try:
            token = Token.objects.select_related('user').get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            return AnonymousUser()


def TokenAuthMiddlewareStack(inner):
    """
    Stack de middleware para WebSockets con autenticación por token
    """
    return TokenAuthMiddleware(inner)
