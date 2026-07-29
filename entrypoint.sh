#!/bin/sh
set -e

# Ensure the volume-backed media dir exists (DB path is created by migrate).
mkdir -p "${MEDIA_ROOT:-/data/media}"

# Apply database migrations against the persistent volume.
python manage.py migrate --noinput

# Reconcile expired jobs/tasks periodically. SQLite lives on this machine's
# volume, so the sweep must run in-process here rather than on a separate
# scheduled machine. Runs once at boot, then hourly in the background.
(
  python manage.py expire_jobs_tasks || true
  python manage.py process_billing_cycles || true
  while true; do
    sleep 3600
    python manage.py expire_jobs_tasks || true
    python manage.py process_billing_cycles || true
  done
) &

# Start the ASGI server (handles both HTTP and WebSockets via Channels/Daphne).
exec daphne -b 0.0.0.0 -p 8000 jobwebsite.asgi:application
