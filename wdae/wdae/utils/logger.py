'''
Created on Jun 12, 2015

@author: lubo
'''
import logging

LOGGER = logging.getLogger('wdae.api')


def log_filter(request, message):
    request_method = getattr(request, 'method', '-')
    path_info = getattr(request, 'path_info', '-')
    username = 'guest'
    if request.user.is_authenticated:
        username = request.user.email

    # Headers
    META = getattr(request, 'META', {})
    remote_addr = META.get('REMOTE_ADDR', '-')
    # server_protocol = META.get('SERVER_PROTOCOL', '-')
    # http_user_agent = META.get('HTTP_USER_AGENT', '-')
    return f'user: {username}; remote addr: {remote_addr}; ' + \
        f'method: {request_method}; path: {path_info}; {message}'


def request_logging(_LOGGER):
    def request_logging_decorator(func):
        def func_wrapper(self, request):
            _LOGGER.info(log_filter(request, '').strip())

            return func(self, request)
        return func_wrapper
    return request_logging_decorator
