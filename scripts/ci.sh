#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf 'Usage: %s [--no-docker]\n' "$0"
  printf 'Run local CI; --no-docker explicitly skips container checks.\n'
}

include_docker=true
if (( $# > 1 )); then
  usage >&2
  exit 2
fi
case "${1:-}" in
  '') ;;
  --no-docker) include_docker=false ;;
  --help|-h) usage; exit 0 ;;
  *) usage >&2; exit 2 ;;
esac

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
for tool in git go python3 node; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    printf 'Required tool missing: %s\n' "$tool" >&2
    exit 1
  fi
done
if [[ "$include_docker" == true ]]; then
  if ! command -v docker >/dev/null 2>&1; then
    printf 'Docker is required; use --no-docker for source checks only.\n' >&2
    exit 1
  fi
  docker info >/dev/null
fi

container_id=''
cleanup() {
  local result=$?
  trap - EXIT
  if [[ -n "$container_id" ]]; then
    if (( result != 0 )); then
      docker logs "$container_id" >&2 || true
    fi
    docker rm -f "$container_id" >/dev/null 2>&1 || true
  fi
  if (( result != 0 )); then
    printf 'Local CI failed (exit %s).\n' "$result" >&2
  fi
  exit "$result"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

printf 'Checking repository syntax and documentation links...\n'
python3 scripts/check_repository.py
printf 'Running Python regression tests...\n'
python3 -m unittest discover -s scripts -p 'test_*.py' -v
git diff --check
git diff --cached --check

printf 'Checking Go formatting...\n'
unformatted=$(gofmt -l cmd internal)
if [[ -n "$unformatted" ]]; then
  printf 'Run gofmt on these files:\n%s\n' "$unformatted" >&2
  exit 1
fi

printf 'Checking module consistency without changing module files...\n'
go mod tidy -diff
printf 'Running race tests...\n'
go test -race ./...
printf 'Running go vet...\n'
go vet ./...
printf 'Building adapter...\n'
mkdir -p bin
go build -trimpath -o bin/abs-audiobookdb ./cmd/abs-audiobookdb

if [[ "$include_docker" == false ]]; then
  printf 'Local source checks passed; Docker checks skipped (--no-docker).\n'
  exit 0
fi

printf 'Building container...\n'
image='abs-audiobookdb:local-ci'
revision=$(git rev-parse HEAD)
dirty=false
if [[ -n "$(git status --porcelain)" ]]; then dirty=true; fi
version=$(cat internal/buildinfo/VERSION)
docker build --build-arg VERSION="$version" --build-arg SOURCE_REVISION="$revision" \
  --build-arg BUILD_DIRTY="$dirty" -t "$image" .
printf 'Checking image version and source revision...\n'
docker run --rm --network none "$image" version | python3 -c \
  'import json,sys; i=json.load(sys.stdin); assert (i["version"],i["revision"],i["dirty"])==tuple(sys.argv[1:])' \
  "$version" "$revision" "$dirty"
[[ "$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.version"}}' "$image")" == "$version" ]]
[[ "$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$image")" == "$revision" ]]
printf 'Checking container health and graceful shutdown without network access...\n'
container_id=$(docker run -d --network none --read-only --memory 256m \
  --cap-drop ALL --security-opt no-new-privileges \
  --label abs-audiobookdb.local-ci=true \
  -e AUDIOBOOKDB_CONTACT=ci@example.invalid "$image")
[[ "$(docker inspect --format '{{.Config.User}}' "$container_id")" == '99:100' ]]
healthy=false
for (( attempt=0; attempt<30; attempt++ )); do
  if docker exec "$container_id" /adapter health >/dev/null 2>&1; then
    healthy=true
    break
  fi
  sleep 0.2
done
if [[ "$healthy" != true ]]; then
  printf 'Container health check failed.\n' >&2
  exit 1
fi
docker stop --time 10 "$container_id" >/dev/null
[[ "$(docker inspect --format '{{.State.ExitCode}}' "$container_id")" == 0 ]]
printf 'Local CI passed, including container health and graceful shutdown.\n'
