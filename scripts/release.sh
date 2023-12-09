#!/usr/bin/env bash
set -o pipefail
set -e

ENV_PREFIX=$1
git tag
echo "WARNING: This operation will create s version tag and push to github"
read -p "Version? (provide the next x.y.z semver) : " TAG
if [[ -z "${TAG}" ]]; then
    printf "ERROR: failed to read valid version got '%s'\\m" "$TAG"
    exit 5
fi
echo "Will tag to version ${TAG} after tests"
python3 -m runem.runem --check
echo "${TAG}" > runem/VERSION
${ENV_PREFIX}gitchangelog > HISTORY.md
git add runem/VERSION HISTORY.md
git commit -m "release: version ${TAG} 🚀"
echo "creating git tag : ${TAG}"
git tag ${TAG}
git push -u origin HEAD --tags
echo "Github Actions will detect the new tag and release the new version."
