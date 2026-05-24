# Absurdist Image Reinterpretation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Change MoodCanvas prompts so generated candidates reinterpret recognizable elements of the uploaded photo in an absurdist surreal style.

**Architecture:** Keep the current two-stage `glm-4v-flash` to `cogview-3-flash` pipeline and API schema. Strengthen the analysis system prompt so it extracts scene anchors and writes constrained generation prompts; mirror the prompt in both runnable backend copies because the checked-in test location and the documented launch location differ.

**Tech Stack:** Python, `unittest`, FastAPI prompt pipeline, ZhipuAI models.

---

### Task 1: Prompt Contract Regression Tests

**Files:**
- Modify: `E:\Douyin-Hangzhou-Hackathon-backend\backend\tests\test_prompts.py`

- [ ] **Step 1: Write failing prompt contract tests**

Add tests that assert `SYSTEM_PROMPT` requires an absurdist reinterpretation prefix, original subject/silhouette/composition/spatial relationships/key objects preservation, and that `build_messages` still sends the uploaded image. Load the documented nested prompt module from `mood-canvas/app/prompts/mood_art.py` and require the same phrases there.

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
cd E:\Douyin-Hangzhou-Hackathon-backend\backend
python -m unittest tests.test_prompts -v
```

Expected: failures because the existing prompts still require `Abstract painting,` and lack the preservation constraints.

### Task 2: Implement Absurdist Scene-Preserving Prompt

**Files:**
- Modify: `E:\Douyin-Hangzhou-Hackathon-backend\backend\app\prompts\mood_art.py`
- Modify: `E:\Douyin-Hangzhou-Hackathon-backend\backend\mood-canvas\app\prompts\mood_art.py`

- [ ] **Step 1: Replace the system prompt content**

Write a concise Chinese instruction prompt that requires:

```text
Absurdist surreal reinterpretation of the original scene,
preserve the recognizable main subject and silhouette
preserve the original composition and spatial relationships
keep the key objects identifiable
```

It must instruct the model to retain the photograph's visual anchors while varying five controlled absurdist transformations and return the existing JSON fields only.

The refined prompt additionally builds internal `INPUT_ELEMENTS` and `USER_MOOD` variables, turns mood into an explicit emotional metaphor, and uses five contrast settings: a classical opera house, desolate desert, star-lit unknown ruins, folded interior theater, and black-humor ritual.

- [ ] **Step 2: Run prompt tests to verify GREEN**

Run:

```powershell
cd E:\Douyin-Hangzhou-Hackathon-backend\backend
python -m unittest tests.test_prompts -v
```

Expected: all prompt contract tests pass.

### Task 3: Regression Verification

**Files:**
- Test: `E:\Douyin-Hangzhou-Hackathon-backend\backend\tests\test_prompts.py`
- Test: `E:\Douyin-Hangzhou-Hackathon-backend\backend\tests\test_analyzer.py`
- Test: `E:\Douyin-Hangzhou-Hackathon-backend\backend\tests\test_generator.py`

- [ ] **Step 1: Run the existing suite**

Run:

```powershell
cd E:\Douyin-Hangzhou-Hackathon-backend\backend
python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 2: Verify the documented nested app imports**

Run:

```powershell
cd E:\Douyin-Hangzhou-Hackathon-backend\backend\mood-canvas
python -c "from app.prompts.mood_art import SYSTEM_PROMPT; from app.main import app; assert 'Absurdist surreal reinterpretation of the original scene,' in SYSTEM_PROMPT; print(app.title)"
```

Expected: outputs `MoodCanvas API`.

## Self-Review

- The plan is limited to prompt behavior and regression coverage; it does not promise strict image-to-image preservation.
- The existing response fields remain unchanged, so no schema or frontend update is required.
- The documented nested launch path and the tested outer backend path are both covered.
