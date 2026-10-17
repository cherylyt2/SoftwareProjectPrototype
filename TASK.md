# Tasks

## 2026-10-15: Build the learning platform MVP

- [x] Validate the Flask health route through Vercel's local Python runtime.
- [x] Validate Vercel Services locally; cloud deployment deferred per user instruction.
- [x] Scaffold Vue 3 and Quasar frontend; combine services with shared routing.
- [x] Add environment configuration, Neon database models, and migrations.
- [x] Implement authentication and admin, instructor, and student workflows.
- [x] Add OpenRouter content generation and document text extraction.
- [x] Finish setup documentation and final integration checks.
- [x] Start the local application after final verification.
- [ ] Complete cloud build/deployment only when requested.

## Discovered During Work

- [x] Vercel's current combined frontend/backend deployment uses Services (Beta); its local service router detects Vue/Vite and Flask and passed frontend/API smoke checks.
- [x] Legacy `.doc` extraction depends on the `antiword` executable; without it, the upload endpoint directs users to convert the file to `.docx`.
- [x] Vercel cloud build was previously blocked by invalid saved CLI authentication; no cloud deployment is needed for this task.