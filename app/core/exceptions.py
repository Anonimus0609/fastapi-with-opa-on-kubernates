# This file will contain custom exceptions for the application
class OPAException(Exception):
    """Exception raised for OPA-related errors"""
    pass

class PermissionDeniedException(Exception):
    """Exception raised when permission is denied"""
    pass