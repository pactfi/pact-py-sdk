#!/bin/sh

set -e

case "$1" in
-h|--help|help)
  echo "Usage: $0 [--autoformat]"
  exit
  ;;
--autoformat)
  ;;
"")
  # lint
  BLACK_FLAGS="--check"
  ISORT_FLAGS="--check"
  ;;
*)
  echo "Usage: $0 [--autoformat]"
  exit 1
  ;;
esac

poetry run mypy .
poetry run black . $BLACK_FLAGS
poetry run isort . $ISORT_FLAGS
poetry run flake8