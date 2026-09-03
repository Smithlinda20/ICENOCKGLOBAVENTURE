#!/usr/bin/env bash

# Render / production build script for ICE NOCK GLOBAL VENTURE Sales System

set -o errexit

pip install --upgrade pip

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate --no-input

python manage.py bootstrap_admin