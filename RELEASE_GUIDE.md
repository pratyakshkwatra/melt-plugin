# 🚀 Melt Plugin Release Guide

Because OctoPrint relies on GitHub `.zip` archives (and caches them), it is critical to tag proper releases so users (and yourself) can fetch specific, stable versions.

Follow this exact sequence before pushing a new release to GitHub.

## Step 1: Bump the Version
Open `setup.py` and increment the version number following Semantic Versioning (e.g., `0.1.3` to `0.1.4`).
```python
setup(
    name="OctoPrint-Melt",
    version="0.1.4", # <--- UPDATE THIS
    ...
```

## Step 2: Commit the Version Bump
Ensure all your files are saved and commit the version bump.
```bash
git add .
git commit -m "chore(release): bump version to 0.1.4"
```

## Step 3: Tag the Release
Create an annotated git tag for the exact version you just set in `setup.py`. The `v` prefix is standard (e.g., `v0.1.4`).
```bash
git tag -a v0.1.4 -m "Version 0.1.4 release"
```

## Step 4: Push to GitHub
Push your commits and your tags simultaneously to the remote repository.
```bash
git push origin main --tags
```

## Step 5: Create a GitHub Release (REQUIRED)
OctoPrint users install plugins via ZIP URLs. **You do NOT need to manually create a ZIP file**—GitHub automatically generates the correct source code `.zip` archive for you when you create a release!

1. Go to your GitHub repository -> **Releases** -> **Draft a new release**.
2. Select the `v0.1.4` tag you just pushed.
3. **Add a Description**: You *must* add a detailed description/release notes outlining what changed (e.g., bug fixes, new features) so users know what they are updating to.
4. Click **Publish release**.

OctoPrint users can now safely install or update your plugin using the auto-generated ZIP URL:
`https://github.com/pratyakshkwatra/melt-plugin/archive/refs/tags/v0.1.4.zip`
