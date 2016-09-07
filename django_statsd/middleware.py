import inspect
import time

from django.http import Http404

from django_statsd.clients import statsd


class GraphiteMiddleware(object):

    def process_response(self, request, response):
        if hasattr(request, '_view_module'):
            data = dict(module=request._view_module,
                        method=request.method,
                        status_code=response.status_code)
            target = 'frontend-web.{method}.{status_code}.requests'
            statsd.incr(target.format(**data))
        return response

    def process_exception(self, request, exception):
        if not isinstance(exception, Http404):
            data = dict(method=request.method)
            statsd.incr('frontend-web.{method}.500.requests'.format(**data))


class GraphiteRequestTimingMiddleware(object):
    """statsd's timing data per view."""

    def process_view(self, request, view_func, view_args, view_kwargs):
        view = view_func
        if not inspect.isfunction(view_func):
            view = view.__class__
        try:
            request._view_module = view.__module__
            request._view_name = view.__name__
            request._start_time = time.time()
        except AttributeError:
            pass

    def process_response(self, request, response):
        self._record_time(request, response)
        return response

    def process_exception(self, request, exception):
        self._record_time(request, exception)

    def _record_time(self, request, response):
        if hasattr(request, '_start_time'):
            ms = int((time.time() - request._start_time) * 1000)
            if hasattr(response, 'status_code'):
                data = dict(method=request.method,
                            status_code=response.status_code)
                target = 'frontend-web.{method}.{status_code}.duration'
            else:
                data = dict(method=request.method)
                target = 'frontend-web.{method}.duration'
            statsd.timing(target.format(**data), ms)


class TastyPieRequestTimingMiddleware(GraphiteRequestTimingMiddleware):
    """statd's timing specific to Tastypie."""

    def process_view(self, request, view_func, view_args, view_kwargs):
        try:
            request._view_module = view_kwargs['api_name']
            request._view_name = view_kwargs['resource_name']
            request._start_time = time.time()
        except (AttributeError, KeyError):
            super(TastyPieRequestTimingMiddleware, self).process_view(
                request, view_func, view_args, view_kwargs)
