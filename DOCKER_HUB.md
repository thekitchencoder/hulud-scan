# Publishing to Docker Hub

This guide explains how to publish the package-scan Docker image to Docker Hub under the `kitchencoder` account.

## Prerequisites

- Docker installed and running
- Docker Hub account (username: `kitchencoder`)
- Image built locally (`docker build -t package-scan .`)

## Step 1: Log in to Docker Hub

```bash
docker login
```

Enter your Docker Hub credentials when prompted:
- Username: `kitchencoder`
- Password: (your Docker Hub password or access token)

## Step 2: Tag Your Image

Tag the image with your Docker Hub username and desired repository name:

```bash
# Tag with 'latest'
docker tag package-scan kitchencoder/package-scan:latest

# Also tag with a version number (recommended)
docker tag package-scan kitchencoder/package-scan:0.1.0

# Optional: tag with additional labels
docker tag package-scan kitchencoder/package-scan:0.1.0-lockfile-support
```

## Step 3: Push to Docker Hub

```bash
# Push the latest tag
docker push kitchencoder/package-scan:latest

# Push the versioned tag
docker push kitchencoder/package-scan:0.1.0

# Or push all tags at once
docker push kitchencoder/package-scan --all-tags
```

## Step 4: Verify

Visit `https://hub.docker.com/r/kitchencoder/package-scan` to see your published image.

## How Others Can Use It

Once pushed, anyone can pull and run your scanner:

```bash
# Pull and run in one command - super simple!
docker run --rm -v "$(pwd):/workspace" kitchencoder/package-scan:latest

# That's it! Report saved as ./package_scan_report.json
```

**Advanced usage:**

```bash
# Custom output filename
docker run --rm -v "$(pwd):/workspace" kitchencoder/package-scan:latest --output my-report.json

# Scan subdirectory
docker run --rm -v "$(pwd):/workspace" kitchencoder/package-scan:latest --dir ./src

# Use custom CSV
docker run --rm -v "$(pwd):/workspace" kitchencoder/package-scan:latest --csv /workspace/custom.csv

# List all compromised packages in the embedded database
docker run --rm kitchencoder/package-scan:latest --list-affected-packages

# Export threat database as raw CSV
docker run --rm kitchencoder/package-scan:latest --list-affected-packages-csv > threats.csv
```

## Automated Build & Push Script

Create a script for consistent releases:

```bash
#!/bin/bash
# tag-and-push.sh

VERSION="0.1.0"
IMAGE_NAME="kitchencoder/package-scan"

echo "Building image..."
docker build -t package-scan .

echo "Tagging with version ${VERSION} and latest..."
docker tag package-scan ${IMAGE_NAME}:${VERSION}
docker tag package-scan ${IMAGE_NAME}:latest

echo "Pushing to Docker Hub..."
docker push ${IMAGE_NAME}:${VERSION}
docker push ${IMAGE_NAME}:latest

echo "✓ Pushed ${IMAGE_NAME}:${VERSION} and ${IMAGE_NAME}:latest"
echo "✓ View at: https://hub.docker.com/r/kitchencoder/package-scan"
```

Make it executable:
```bash
chmod +x tag-and-push.sh
./tag-and-push.sh
```

## Version Tagging Best Practices

Use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes (e.g., 1.0.0 → 2.0.0)
- **MINOR**: New features, backward compatible (e.g., 0.1.0 → 0.2.0)
- **PATCH**: Bug fixes (e.g., 0.1.0 → 0.1.1)

```bash
# Patch release (bug fixes)
docker tag package-scan kitchencoder/package-scan:0.1.1

# Minor release (new features, like lock file support)
docker tag package-scan kitchencoder/package-scan:0.2.0

# Major release (breaking changes)
docker tag package-scan kitchencoder/package-scan:1.0.0
```

Always maintain a `latest` tag pointing to the most recent stable release.

## Full Workflow Example

```bash
# 1. Build the image
docker build -t package-scan .

# 2. Test locally
docker run --rm -v "$(pwd)/examples:/scan" package-scan --dir /scan --no-save

# 3. Tag for Docker Hub
docker tag package-scan kitchencoder/package-scan:0.1.0
docker tag package-scan kitchencoder/package-scan:latest

# 4. Push to Docker Hub
docker push kitchencoder/package-scan:0.1.0
docker push kitchencoder/package-scan:latest

# 5. Test the public image
docker run --rm -v "$(pwd)/examples:/scan" \
  kitchencoder/package-scan:latest --dir /scan --no-save
```

## Docker Hub Repository Settings

### Recommended Description

On Docker Hub (`https://hub.docker.com/r/kitchencoder/package-scan`), add this description:

```
Multi-Ecosystem Package Threat Scanner

Scans JavaScript (npm), Java (Maven/Gradle), and Python projects to identify
compromised packages across multiple supply chain threats.

Features:
• Multi-threat scanning with --threat flag
• Multi-ecosystem support (npm, Maven/Gradle, pip/poetry/pipenv/conda)
• Three-phase detection (manifests, lock files, installed packages)
• Semantic version range matching for all ecosystems
• Actionable remediation guidance with color-coded output
• Runs as non-root user for security
• Based on python:3.11-slim (~150MB)

Quick Start:
docker run --rm -v "$(pwd):/workspace" kitchencoder/package-scan:latest

Documentation: https://github.com/kitchencoder/package-scan
```

### Recommended README for Docker Hub

Add a comprehensive README on Docker Hub:

```markdown
# package-scan

Multi-Ecosystem Package Threat Scanner for identifying compromised packages across
JavaScript (npm), Java (Maven/Gradle), and Python projects.

## Usage

### Basic Scan

Scan for all threats across all detected ecosystems:

```bash
docker run --rm -v "$(pwd):/workspace" kitchencoder/package-scan:latest
```

### Scan for Specific Threat

Focus on a specific supply chain attack (e.g., sha1-Hulud):

```bash
docker run --rm -v "$(pwd):/workspace" kitchencoder/package-scan:latest --threat sha1-Hulud
```

### Scan Specific Ecosystem

Target a specific package ecosystem:

```bash
# Scan only npm packages
docker run --rm -v "$(pwd):/workspace" kitchencoder/package-scan:latest --ecosystem npm

# Scan only Java packages (Maven/Gradle)
docker run --rm -v "$(pwd):/workspace" kitchencoder/package-scan:latest --ecosystem maven

# Scan only Python packages
docker run --rm -v "$(pwd):/workspace" kitchencoder/package-scan:latest --ecosystem pip
```

### List Compromised Packages

View all packages in the embedded threat database:

```bash
# Formatted display
docker run --rm kitchencoder/package-scan:latest --list-affected-packages

# Raw CSV output (for piping/saving)
docker run --rm kitchencoder/package-scan:latest --list-affected-packages-csv > threats.csv
```

### Custom Threat Database

```bash
docker run --rm \
  -v "$(pwd):/workspace" \
  -v "$(pwd)/custom-threat.csv:/app/custom.csv" \
  kitchencoder/package-scan:latest --csv /app/custom.csv
```

### Save Report to Host

```bash
docker run --rm -v "$(pwd):/workspace" \
  kitchencoder/package-scan:latest --output /workspace/report.json

# Report saved at: ./report.json on your host
```

## What Gets Scanned

### npm (JavaScript/Node.js)
- **Manifests**: package.json
- **Lock files**: package-lock.json, yarn.lock, pnpm-lock.yaml
- **Installed**: node_modules/

### Maven/Gradle (Java)
- **Manifests**: pom.xml, build.gradle, build.gradle.kts
- **Lock files**: gradle.lockfile

### pip (Python)
- **Manifests**: requirements.txt, pyproject.toml, Pipfile, environment.yml
- **Lock files**: poetry.lock, Pipfile.lock

## Features

- ✓ Multi-threat scanning with --threat flag
- ✓ Multi-ecosystem support (npm, Maven/Gradle, pip/poetry/pipenv/conda)
- ✓ Comprehensive three-phase detection (manifests, lock files, installed packages)
- ✓ Semantic version range matching for all ecosystems
- ✓ Support for all major package managers
- ✓ Color-coded terminal output with emoji
- ✓ Actionable remediation guidance
- ✓ JSON report output with threat tracking
- ✓ Runs as non-root user
- ✓ Secure python:3.11-slim base image (~150MB)

## Source Code

https://github.com/kitchencoder/package-scan
```

## Verify Image Details

Check your image before pushing:

```bash
# Check image size
docker images kitchencoder/package-scan

# Inspect image metadata
docker inspect kitchencoder/package-scan:latest

# Test the image
docker run --rm kitchencoder/package-scan:latest --help
```

## Troubleshooting

### Authentication Failed

```bash
# Use access token instead of password
docker logout
docker login -u kitchencoder
```

Generate an access token at: https://hub.docker.com/settings/security

### Image Too Large

The image should be ~235MB. If it's significantly larger:

```bash
# Check what's taking space
docker history kitchencoder/package-scan:latest

# Rebuild with --no-cache
docker build --no-cache -t package-scan .
```

### Push Denied

Ensure you're logged in with the correct account:

```bash
docker logout
docker login -u kitchencoder
```

## Updating the Image

When you make changes:

1. Update version in `pyproject.toml`
2. Rebuild: `docker build -t package-scan .`
3. Test locally
4. Tag with new version
5. Push both version tag and latest tag

```bash
# Example: releasing v0.2.0
docker build -t package-scan .
docker tag package-scan kitchencoder/package-scan:0.2.0
docker tag package-scan kitchencoder/package-scan:latest
docker push kitchencoder/package-scan:0.2.0
docker push kitchencoder/package-scan:latest
```

## CI/CD Integration (Optional)

For automated builds on GitHub Actions, create `.github/workflows/docker-publish.yml`:

```yaml
name: Docker Publish

on:
  push:
    tags:
      - 'v*'

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: kitchencoder
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Extract version
        id: meta
        run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          push: true
          tags: |
            kitchencoder/package-scan:${{ steps.meta.outputs.VERSION }}
            kitchencoder/package-scan:latest
```

Add `DOCKERHUB_TOKEN` to your GitHub repository secrets.
