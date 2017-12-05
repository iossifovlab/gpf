#!/usr/bin/env bash


gunicorn \
    --workers=16 \
    --bind=127.0.0.1:8000 \
    --timeout=600 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --preload \
    wdae.gunicorn_wsgi:application