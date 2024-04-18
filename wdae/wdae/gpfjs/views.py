from django.conf import settings
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.views import serve
from django.shortcuts import render


def index(request):
    if finders.find("gpfjs/gpfjs/index.html"):
        return serve(request, "gpfjs/gpfjs/index.html", settings.STATIC_ROOT)
    return render(request, "gpfjs/empty/empty.html")


def favicon(request):
    if finders.find("gpfjs/gpfjs/favicon.ico"):
        return serve(request, "gpfjs/gpfjs/favicon.ico", settings.STATIC_ROOT)
    return render(request, "gpfjs/empty/favicon.ico")
