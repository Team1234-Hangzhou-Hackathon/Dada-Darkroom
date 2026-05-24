# Voice And Pixel UI Merge Plan

**Goal:** Merge the uploaded pixel-window frontend ideas into the runnable MoodCanvas application while preserving its backend-driven image processing and five-result workflow.

## Behavior To Preserve

- Upload and camera captures must continue to submit a real `File`/`Blob` to the backend.
- Generation must continue through `generatePaintings()` and produce five backend results.
- API health feedback and the existing product workshop flow must remain available.
- The application must remain directly accessible through the FastAPI-hosted page at `http://localhost:8000/`.

## Implementation

1. Add a small tested voice-input helper for safe speech transcript composition and browser API selection.
2. Add voice recognition state and controls to the existing `App.jsx` without replacing current generation handlers.
3. Restyle the upload, camera, and description areas with the pixel application-window presentation from the provided UI draft.
4. Add deterministic motion styles and title animation classes without runtime-random rendering.
5. Run unit tests and lint, build frontend output into the backend static directory, and verify the served page in the browser.

## Verification

- `node --test src/moodcanvas-api.test.js src/voice-input.test.js`
- `npm run lint`
- `npm run build -- --outDir "E:\MoodCanvas\workspace\backend\static" --emptyOutDir`
- Browser check at `http://localhost:8000/` for the new voice/input windows and retained API/five-result status.
