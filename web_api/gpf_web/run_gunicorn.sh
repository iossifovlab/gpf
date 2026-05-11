#!/usr/bin/env bash


gunicorn \
    --preload \
    --worker-class gthread \
    --workers 4 \
    --threads 4 \
    --bind=127.0.0.1:8000 \
    --timeout=600 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    wdae.gunicorn_wsgi:application
