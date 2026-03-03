#!/usr/bin/env bash

# Updates tags from the remote
git fetch --tags

# Gets the latest tag or 0.0.0
VERSION=$(git tag --sort=v:refname | tail -n 1)
VERSION=${VERSION:-0.0.0}
echo "Latest version: $VERSION"

# Split in major, minor, patch
IFS='.' read -r major minor patch <<< "$VERSION"

# Ask user what to increment
echo "Choose what to increment? (major/minor/patch) "
read -r choice

case "$choice" in
  major)
    major=$((major + 1))
    minor=0
    patch=0
    ;;
  minor)
    minor=$((minor + 1))
    patch=0
    ;;
  patch|*)
    patch=$((patch + 1))
    ;;
esac

NEW_VERSION="${major}.${minor}.${patch}"

# Commit automatically
echo "Automatically committing all modified files..."
git add -A
git commit -m "Release $NEW_VERSION" || echo "Nothing to commit"

# Push the commit
git push origin

# Create and push the tag
git tag "$NEW_VERSION"
git push origin "$NEW_VERSION"

# Update the VERSION file
echo "$NEW_VERSION" > VERSION

echo "New tag: $NEW_VERSION"