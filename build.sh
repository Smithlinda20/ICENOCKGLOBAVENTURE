#!/usr/bin/env bash

# Render / production build script for ICE NOCK GLOBAL VENTURE Sales System

set -o errexit

pip install --upgrade pip

pip install -r requirements.txt

python manage.py collectstatic --no-input

# Repair only the known accounts/admin migration-history mismatch.
# This does NOT reset or delete the existing database.
python manage.py repair_migration_history

python manage.py migrate --no-input

python manage.py bootstrap_admin
