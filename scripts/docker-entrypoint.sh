#!/usr/bin/env sh

set -e

poetry run alembic upgrade head
exec poetry run python -O -m bot
