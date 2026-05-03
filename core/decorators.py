from functools import wraps
from django.shortcuts import redirect


def staff_required(view_func):
    """Decorator that checks if the user is authenticated AND is_staff."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def voter_required(view_func):
    """Decorator that checks if the user is authenticated AND NOT is_staff."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

