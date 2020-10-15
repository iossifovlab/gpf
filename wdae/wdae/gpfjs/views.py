import os

from django.shortcuts import render
from django.conf import settings


def index(request):
    gpfjs_index = os.path.join(
        settings.PROJECT_ROOT, 
        "gpfjs", "static", "gpfjs", "index.html")
    if os.path.exists(gpfjs_index):
        return render(request, "index.html")
    return render(request, "empty.html")
