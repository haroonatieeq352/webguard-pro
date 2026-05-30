"""
WebGuard Pro — Custom Exception Handler
Formats all DRF errors in consistent JSON structure
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger('apps')


def custom_exception_handler(exc, context):
    """
    Custom DRF exception handler.
    Wraps all error responses in a consistent format:

    {
        "error": "error_code",
        "message": "Human readable message",
        "details": {...}  // Optional field-level errors
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            'error': get_error_code(response.status_code),
            'message': get_error_message(response),
            'status_code': response.status_code,
        }

        # Add field-level validation errors
        if isinstance(response.data, dict):
            if 'detail' not in response.data and 'error' not in response.data:
                error_data['details'] = response.data

        response.data = error_data

    else:
        # Unhandled exceptions
        logger.exception(f"Unhandled exception in {context.get('view')}: {exc}")
        response = Response(
            {
                'error': 'internal_server_error',
                'message': 'An unexpected error occurred. Please try again.',
                'status_code': 500,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response


def get_error_code(status_code: int) -> str:
    codes = {
        400: 'bad_request',
        401: 'unauthorized',
        403: 'forbidden',
        404: 'not_found',
        405: 'method_not_allowed',
        408: 'request_timeout',
        409: 'conflict',
        429: 'too_many_requests',
        500: 'internal_server_error',
        503: 'service_unavailable',
    }
    return codes.get(status_code, 'error')


def get_clean_message(val) -> str:
    """Helper to recursively extract a clean string from DRF's ErrorDetail or lists/dicts."""
    if isinstance(val, list):
        if len(val) > 0:
            return get_clean_message(val[0])
        return 'An error occurred.'
    if isinstance(val, dict):
        if 'detail' in val:
            return get_clean_message(val['detail'])
        if 'error' in val:
            return get_clean_message(val['error'])
        if len(val) > 0:
            first_key = list(val.keys())[0]
            return get_clean_message(val[first_key])
        return 'An error occurred.'
    # For DRF's ErrorDetail, str(val) extracts the raw message string without the class representation.
    return str(val)


def get_error_message(response) -> str:
    return get_clean_message(response.data)
