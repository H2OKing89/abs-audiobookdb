#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
version=$(cat internal/buildinfo/VERSION)
revision=$(git rev-parse HEAD)
tag="v$version"
if [[ -n "$(git status --porcelain)" ]]; then
  printf 'Release requires a clean checkout. Commit reviewed changes first.\n' >&2
  exit 1
fi
if [[ "$(git rev-list -n 1 "$tag")" != "$revision" ]]; then
  printf 'Release requires HEAD to match %s. Tags are never moved.\n' "$tag" >&2
  exit 1
fi
if [[ "$(docker info --format '{{.Architecture}}')" != x86_64 ]]; then
  printf 'This release packages linux/amd64 only; use an x86_64 Docker host.\n' >&2
  exit 1
fi
destination="dist/$tag"
if [[ -e "$destination" ]]; then
  printf '%s already exists; preserve it and choose a new release version.\n' "$destination" >&2
  exit 1
fi
./scripts/ci.sh
image="abs-audiobookdb:$version"
docker tag abs-audiobookdb:local-ci "$image"
mkdir -p "$destination"
python3 spikes/MVP-001/load.py --image "$image" --warm-seconds 180 --output "$destination/load.json"
docker run --rm --network none "$image" version > "$destination/version.json"
container_id=$(docker create "$image")
trap 'docker rm "$container_id" >/dev/null 2>&1 || true' EXIT
docker cp "$container_id:/adapter" "$destination/abs-audiobookdb-linux-amd64"
docker cp "$container_id:/licenses/Go-BSD.txt" "$destination/Go-LICENSE"
docker rm "$container_id" >/dev/null
trap - EXIT
docker save "$image" | gzip -n > "$destination/abs-audiobookdb-$version-linux-amd64-image.tar.gz"
cp LICENSE "$destination/LICENSE"
docker image inspect --format '{{.Id}}' "$image" > "$destination/image-id.txt"
(
  cd "$destination"
  sha256sum LICENSE Go-LICENSE abs-audiobookdb-linux-amd64 *.tar.gz image-id.txt version.json load.json > SHA256SUMS
)
printf 'Validated local release artifacts: %s\n' "$destination"
printf 'Registry publication and GitHub release upload are separate explicit commands; see docs/releases.md.\n'
