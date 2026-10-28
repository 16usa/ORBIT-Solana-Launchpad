---
name: Artifact production command paths
description: Relative path convention for production build and run commands in this multi-artifact workspace.
---

Artifact production build and run commands resolve relative paths from the workspace root, even when the command belongs to one artifact. Use workspace-root-relative paths such as `artifacts/<slug>/dist/...`; do not assume the production process starts in the artifact directory. Development workflows can use a different working directory.

**Why:** A publish attempt built the frontend and packaged the API successfully, then crash-looped because the run command looked under workspace-root `dist/` instead of the API artifact's `dist/`.

**How to apply:** Check deployment logs for the resolved missing path, then test the exact production command from the workspace root after staging its files. Verify development and production paths independently.
