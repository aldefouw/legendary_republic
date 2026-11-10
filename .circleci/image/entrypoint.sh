#!/bin/sh
set -eu

cd /app
if ! sha256sum --check /opt/ci-dependencies/dependencies.sha256; then
  echo "Dependency files differ from the CI image. Publish the matching image with .circleci/ci-image.py build APP_PATH --push." >&2
  exit 1
fi
bundle check
exec "$@"
