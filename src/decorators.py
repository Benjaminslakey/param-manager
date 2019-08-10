from functools import wraps, partial

from django.http import HttpRequest, HttpResponse

from src.utils import get_request_arg


def persist_params(params_to_persist):
    """
        Load data sent by client in GET params into request session data so it can be accessed by other requests in
        this browsing session
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapper(*args, **kwargs):
            request = get_request_arg(*args, **kwargs)
            # persist data between requests using session
            for param_name in params_to_persist:
                param_val = request.GET.get(param_name)
                if param_val is not None:
                    request.session[param_name] = param_val
            return view_func(*args, **kwargs)
        return _wrapper
    return decorator


def requirement_decorator_factory(requirements_validator):
    if not callable(requirements_validator):
        raise TypeError("requirements_validator parameter must be a function")

    def require_params(requirements, on_error=None):
        try:
            if isinstance(requirements, str) or isinstance(requirements, unicode):
                raise TypeError
            # check valid iteration
            for _ in requirements:
                break
        except TypeError:
            raise TypeError("requirements must be an iterable")

        def decorator(view_func):
            @wraps(view_func)
            def _wrapper(*args, **kwargs):
                params = get_request_arg(*args, **kwargs).GET.copy()
                param_err = requirements_validator(requirements, params)
                if param_err:
                    return on_error() if callable(on_error) else HttpResponse(param_err, status=404)
                return view_func(*args, **kwargs)
            return _wrapper
        return decorator
    return require_params


def is_param_present(params, params_spec):
    if not isinstance(params_spec, str) and not isinstance(params_spec, unicode):
        raise TypeError("Required param must be a string")
    return params.get(params_spec) is not None


def require_all_validator(requirements, params):
    checker = partial(is_param_present, params)
    if all(map(checker, requirements)):
        return ""
    return "Missing required param(s): {}".format(",".join(filter(checker, requirements)))


def require_any_validator(requirements, params):
    checker = partial(is_param_present, params)
    if any(map(checker, requirements)):
        return ""
    return "One of {} is required".format(",".join(requirements))


def is_param_value_valid(params, params_spec):
    if not isinstance(params_spec, tuple) or len(params_spec) != 2:
        raise TypeError("Required param_spec must be 2-tuple (key, value)")
    elif not callable(params_spec[1]):
        raise TypeError("Required param_spec must contain a function to check the value")
    param_name, value_check_func = params_spec
    return value_check_func(params.get(param_name))


def require_param_value_validator(requirements, params):
    kv_pairs = requirements.items() if isinstance(requirements, dict) else requirements
    checker = partial(is_param_value_valid, params)
    if all(map(checker, kv_pairs)):
        return ""
    return "Params: {} have an invalid value".format(",".join(filter(checker, kv_pairs)))


require_any_param = requirement_decorator_factory(require_any_validator)
require_all_params = requirement_decorator_factory(require_all_validator)
require_param_value = requirement_decorator_factory(require_param_value_validator)
