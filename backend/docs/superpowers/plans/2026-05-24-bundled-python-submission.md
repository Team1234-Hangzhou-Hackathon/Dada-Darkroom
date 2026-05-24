# Bundled Python Competition Submission Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a Windows competition submission ZIP that launches MoodCanvas by double-clicking `START.bat` without requiring Python to be installed on the reviewer computer.

**Architecture:** Preserve the verified application and source bundle, but replace host-Python bootstrapping with an application-local Python 3.13 x64 runtime. Preinstall backend wheels into that runtime during package assembly; the launcher only selects a free port and starts FastAPI from bundled files.

**Tech Stack:** PowerShell launcher, official CPython Windows embeddable distribution, FastAPI/Uvicorn, existing offline wheel set, React static bundle.

---

### Task 1: Verify The Current Distribution Gap

**Files:**
- Read: `E:\MoodCanvas-Competition-Submission-20260524.zip`

- [ ] Extract the existing submission into a clean temporary assembly folder.
- [ ] Run an assertion requiring `MoodCanvas\runtime\python\python.exe`.
- [ ] Confirm it fails because the existing ZIP still requires host-installed Python.

### Task 2: Add Application-Local Python Runtime

**Files:**
- Create: `MoodCanvas\runtime\python\*` inside the assembly directory
- Modify: `MoodCanvas\start.ps1` inside the assembly directory

- [ ] Download the official Python 3.13 x64 embeddable distribution and verify its SHA-256 checksum from the official release page.
- [ ] Extract it into `runtime\python`, enable application and `Lib\site-packages` imports in `python313._pth`.
- [ ] Install the existing `wheels\py313` requirements to `runtime\python\Lib\site-packages` during package assembly.
- [ ] Modify `start.ps1` to require and run only `runtime\python\python.exe`, without creating `.venv` or invoking a host Python.

### Task 3: Document And Package The Deliverable

**Files:**
- Modify: `README-比赛提交与运行说明.md`
- Modify: `MoodCanvas\使用说明.md`
- Create: `E:\MoodCanvas-Competition-Submission-NoPython-20260524.zip`

- [ ] State that reviewers only extract and double-click `START.bat`; no Python or Node.js installation is needed.
- [ ] Keep the existing API key confidentiality and network/API quota warning.
- [ ] Generate a new ZIP while leaving runtime logs, cache folders, and test environments out of the deliverable.

### Task 4: Verify The Final ZIP

**Files:**
- Test: `E:\MoodCanvas-Competition-Submission-NoPython-20260524.zip`

- [ ] Extract the final ZIP to a fresh test folder.
- [ ] Start the extracted `START.bat` workflow with a PATH that does not expose an installed Python interpreter.
- [ ] Verify `/api/health`, the newest pixel/voice frontend bundle, and dynamic port fallback while port `8000` is already used.
- [ ] Remove the smoke-test directory after validation and retain only the final ZIP.
