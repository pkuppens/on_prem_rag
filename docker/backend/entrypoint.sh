#!/bin/sh
# Ensure uploaded_files directory exists and is writable by appuser (uid 1000).
# Named volumes are root-owned by default; this fixes permissions before app starts.
set -e
mkdir -p /app/uploaded_files
chown -R appuser:appuser /app/uploaded_files
exec runuser -u appuser -- "$@"
