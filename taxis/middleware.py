"""
Middleware para autenticación de WebSockets con Token
"""
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from urllib.parse import parse_qs


class TokenAuthMiddleware(BaseMiddleware):
    """
    Middleware para autenticar WebSockets usando Token de DRF
    
    Busca el token en:
    1. Query string: ?token=xxxxx
    2. Headers: Authorization: Token xxxxx
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
        
        # Autenticar usuario con el token
        if token_key:
            scope['user'] = await self.get_user_from_token(token_key)
        else:
            # Importar aquí para evitar AppRegistryNotReady
            from django.contrib.auth.models import AnonymousUser
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)
    
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
