#!/usr/bin/env bash
set -e

host="$1"
shift
cmd="$@"

until nc -z "$host"; do
  echo "Waiting for $host..."
  sleep 1
done

echo "$host is available. Running the command."
exec $cmd
