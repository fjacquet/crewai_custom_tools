# ADR 0004: Native GitHub Actions Pages Deployment

**Date**: 2026-07-05  
**Author**: Gemini CLI & Collaborative Engineering Team  
**Status**: ACCEPTED  

---

## Context & Problem Statement

To publish our package documentation, we used MkDocs to generate static HTML pages. Standard practice often involves using a tool like `gh-deploy` to build the website locally and push the static files to a separate `gh-pages` branch in our Git repository. However, this pollutes the repository's git history, leaves messy automated commit traces, and requires managing separate branch tracking.

We needed a cleaner, more secure, and fully automated deployment pipeline.

---

## Considered Alternatives

1. **Push static files to `gh-pages` branch**: Use standard `mkdocs gh-deploy` from a local terminal or CI runner.
   - *Verdict*: Rejected. Causes git history bloat, requires managing branch permissions, and leaves unreviewed commit logs.
2. **Native GitHub Actions Pages Deployment** [Chosen]: Configure the documentation workflow to build the site, upload the compiled static files as a secure pages artifact, and trigger native GitHub Pages serving directly via GitHub's deployment APIs.

---

## Architectural Decisions

- **Native Actions Deployment (`docs.yml`)**: We configured `.github/workflows/docs.yml` to request Pages and Id-Token permissions (`permissions: pages: write, id-token: write`).
- **Eliminate `gh-pages` Branch**: The workflow compiles the site using `mkdocs build`, uploads the output via `actions/upload-pages-artifact`, and deploys it natively via `actions/deploy-pages`, enabling us to permanently **delete** the `gh-pages` branch from both local and remote origins.

---

## Implications & Consequences

- **Pristine Branch Structure**: The repository contains only a single `main` branch with zero automated branch pollution or commit traces.
- **Secure and Fast**: Documents are built and hosted natively on GitHub's secure CDN entirely within the Actions pipeline, with zero manual Git push friction.
