# Media Artifact Hygiene Policy

Mode: Documentation/policy guard only. Runtime unchanged.

## Purpose

Generated image and media artifacts must not create dirty Git commits or accidental privacy leaks. This policy controls how generated media is stored, reviewed, staged, and approved.

## Default Rule

Generated image/media files must not be committed by default.

## Preferred Storage Locations

Generated media artifacts should be stored in a dedicated ignored folder, such as:

- `runtime/artifacts/media/`
- `.openclaw_artifacts/media/`

These locations should be treated as runtime/generated output, not source material.

## Git Commit Rules

- Git commits must never include generated media unless explicitly approved.
- Exact-file staging is required.
- Never use:

```bash
git add .
```

Before any PR or commit, verify staged files with:

```bash
git diff --cached --name-only
```

## Generated Media Examples to Exclude

Do not stage or commit these by default:

- `*.png`
- `*.jpg`
- `*.jpeg`
- `*.webp`
- `*.gif`
- `artifacts/`
- `temp_page_*.png`
- `frame_*.jpg`
- `page_image.png`
- generated image outputs
- media test outputs

## Exception Process

If media must be included in Git, require all of the following before staging:

1. Explicit user approval.
2. Reason for inclusion.
3. Exact file list.
4. Size check.
5. Privacy check.

Approved media must still use exact-file staging only. Never stage media through broad directory or wildcard commands unless the exact reviewed file list is equivalent and explicitly approved.

## PR Review Checklist

Before opening or updating a PR:

1. Run:

```bash
git diff --cached --name-only
```

2. Confirm no generated media is staged by default.
3. Confirm no runtime/cache/test output is staged.
4. Confirm no private, sensitive, or personally identifying image content is included without approval.
5. Confirm workflow files were not changed unless explicitly approved.

## Blocked Actions

- Do not delete existing artifacts automatically.
- Do not move existing artifacts automatically.
- Do not modify runtime behavior.
- Do not activate media delivery.
- Do not use `git add .`.
- Do not stage generated media without explicit approval.
