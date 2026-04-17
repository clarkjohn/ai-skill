#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"${BASE_DIR}/mvnw" -q -DskipTests package >/dev/null
exec java -jar "${BASE_DIR}/target/spring-config-dump-0.1.0.jar" "$@"
