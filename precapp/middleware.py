"""
Middleware for tracking user context in Django applications.

This middleware captures the current user and stores it in thread-local storage,
making it available for use in model save methods and other contexts where
the request object is not directly accessible.
"""

import threading
from django.utils.deprecation import MiddlewareMixin


class UserTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track the current user in thread-local storage.
    
    This middleware captures the authenticated user from each request
    and stores it in thread-local storage, making it available for
    audit tracking in model save methods.
    
    The user information is automatically available in model save methods
    via: threading.current_thread().user
    
    Usage:
        1. Add to MIDDLEWARE in settings.py:
           'precapp.middleware.UserTrackingMiddleware'
        
        2. Access in model save methods:
           current_user = getattr(threading.current_thread(), 'user', None)
           if current_user:
               self.modified_by = current_user.get_full_name()
    """
    
    def process_request(self, request):
        """
        Store the current user in thread-local storage.
        
        Args:
            request: Django HttpRequest object containing user information
        
        Returns:
            None: Middleware continues processing
        """
        # Store user in thread-local storage
        threading.current_thread().user = getattr(request, 'user', None)
        return None
    
    def process_response(self, request, response):
        """
        Clean up thread-local storage after request processing.
        
        Args:
            request: Django HttpRequest object
            response: Django HttpResponse object
        
        Returns:
            HttpResponse: The original response object
        """
        # Clean up thread-local storage
        if hasattr(threading.current_thread(), 'user'):
            delattr(threading.current_thread(), 'user')
        return response
    
    def process_exception(self, request, exception):
        """
        Clean up thread-local storage if an exception occurs.
        
        Args:
            request: Django HttpRequest object
            exception: The exception that occurred
        
        Returns:
            None: Let Django handle the exception normally
        """
        # Clean up thread-local storage on exception
        if hasattr(threading.current_thread(), 'user'):
            delattr(threading.current_thread(), 'user')
        return None
