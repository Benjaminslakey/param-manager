from django.http import HttpRequest


def get_request_arg(*args, **kwargs):
    request = None
    for arg in list(args) + kwargs.values():
        if isinstance(arg, HttpRequest):
            request = arg
            break

    if request is None:
        raise TypeError("Request object not present in arguments")
    return request