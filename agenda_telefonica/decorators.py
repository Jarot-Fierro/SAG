from functools import wraps

from django.http import Http404


def user_editor_module(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise Http404()

        try:
            if request.user.perfilagenda.editor:
                return view_func(request, *args, **kwargs)
        except Exception:
            pass

        raise Http404()

    return _wrapped_view
