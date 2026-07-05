#!/usr/bin/env bash
# Build a release archive (.tar.gz and .zip) of this repository with
# AI-operating files excluded, for distribution outside GitHub Releases
# (e.g. manual distribution, or vendoring into another project instead of
# using this repo as a git submodule).
#
# This is a thin wrapper around `git archive`, which already excludes the
# paths marked `export-ignore` in .gitattributes. Do not duplicate that
# exclusion list here; edit .gitattributes if the excluded paths need to
# change.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REF="${1:-HEAD}"

OUT_DIR="${REPO_ROOT}/dist"
NAME="llm-cluster-router-$(cd "${REPO_ROOT}" && git rev-parse --short "${REF}")"

mkdir -p "${OUT_DIR}"

cd "${REPO_ROOT}"
git archive --format=tar.gz --prefix="${NAME}/" -o "${OUT_DIR}/${NAME}.tar.gz" "${REF}"
git archive --format=zip --prefix="${NAME}/" -o "${OUT_DIR}/${NAME}.zip" "${REF}"

echo "built: ${OUT_DIR}/${NAME}.tar.gz"
echo "built: ${OUT_DIR}/${NAME}.zip"
