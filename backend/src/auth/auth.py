from functools import wraps

import jwt
from flask import request

AUTH0_DOMAIN = 'dev-2m33ryh3.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'dev'

# AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# Auth Header
def get_token_auth_header():
    '''
    it should attempt to get the header from the request
    it should raise an AuthError if no header is present
    it should attempt to split bearer and the token
    it should raise an AuthError if the header is malformed

    return the token part of the header
    '''

    auth = request.header.get('Authorization', None)

    if not auth:
        raise AuthError({
            'code': 'authorization header is missing',
            'description': 'Authorization header is expected.'
        }, 401)

    try:
        schema, token, *other = auth.split()
    except ValueError:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Token not found.'
        }, 401)

    if schema.lower != 'bearer':
        raise AuthError({
            'code': 'invalid heder',
            'description': 'The authorization schema used must be "Bearer".'
        }, 401)
    elif other:
        raise AuthError({
            'code': 'invalid heder',
            'description': 'Authorization header must be bearer token'
        }, 401)

    return token


def check_permissions(permission, payload):
    '''
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    it should raise an AuthError if permissions are not included in the payload
        !!NOTE check your RBAC settings in Auth0
    it should raise an AuthError if the requested permission string is not in the payload permissions array
    return true otherwise
    '''

    allowed = payload.get('permissions', None)

    if not allowed:
        raise AuthError({
            'code': 'Forbidden',
            'description': 'No permissions in payload'
        }, 403)
    elif permission not in allowed:
        raise AuthError({
            'code': 'Forbidden',
            'description': 'Action not allowed for user/role'
        }, 403)
    else:
        return True


def verify_decode_jwt(token):
    '''
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload

    !!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
    '''

    header = jwt.get_unverified_header(token)
    if 'kid' not in header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    url = f'https://{AUTH0_DOMAIN}/.well-known/jwks.json'
    jwks_client = jwt.PyJWKClient(url)

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        data = jwt.decode(
            token,
            signing_key.key,
            algorithms=ALGORITHMS,
            options={'require': ['exp', 'iss', 'aud']},
            audience=API_AUDIENCE,
            issuer=f'https://{AUTH0_DOMAIN}/'
        )
        return data

    except jwt.MissingRequiredClaimError:
        raise AuthError({
            'code': 'invalid claims',
            'Description': 'Missing required claims'
        }, 401)
    except jwt.InvalidKeyError:
        raise AuthError({
            'code': 'invalid key',
            'Description': 'Key is not in the proper format'
        }, 401)
    except jwt.InvalidIssuerError:
        raise AuthError({
            'code': 'invalid issuer',
            'description': '"iss" claim does not match expected issuer.'
        }, 401)
    except jwt.InvalidAudienceError:
        raise AuthError({
            'code': 'invalid audience',
            'description': '"aud" claim does not match expected audience.'
        }, 401)
    except jwt.ExpiredSignatureError:
        raise AuthError({
            'code': 'token expired',
            'description': 'Token expired.'
        }, 401)
    except jwt.InvalidSignatureError:
        raise AuthError({
            'code': 'invalid signature',
            'description': 'Signature does not match the one provided.'
        }, 401)
    except jwt.DecodeError:
        raise AuthError({
            'code': 'decode error',
            'description': 'Token failed validation.'
        }, 400)
    except jwt.InvalidTokenError:
        raise AuthError({
            'code': 'invalid token',
            'description': 'Token could not be decoded.'
        }, 400)


'''
@TODO: implement @requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims and check the requested permission
    return the decorator which passes the decoded payload to the decorated method
'''


def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator
