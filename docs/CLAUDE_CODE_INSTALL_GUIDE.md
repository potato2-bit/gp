# Claude Code — Install & Setup Guide (Windows)

**Generated:** 2026-04-25 (scheduled task — user not present)
**Target machine:** Windows (paths under `C:\Users\rizk\...`)
**Project folder:** `C:\Users\rizk\Desktop\GRADUATION PROJECT`

This guide gets Claude Code working in (1) the Windows terminal and (2) an IDE so you can start working on the autonomous TEC-based PV-cleaning robot project.

---

## 1. Prerequisites

- **Node.js 18+** (LTS) — install from <https://nodejs.org> (keep default options).
- **Windows 10 (1809+)** or **Windows 11**.
- An **Anthropic / Claude account** (same login as Claude.ai).
- Recommended: **PowerShell** (not CMD) and, optionally, **WSL2** for a Unix-like environment.

Verify Node:

```powershell
node --version
npm --version
```

Both should print versions. If not, reinstall Node from the official installer.

---

## 2. Install Claude Code in the Terminal

Pick **one** of the options below.

### Option A — Native Windows installer (recommended)

Open **PowerShell** and run:

```powershell
irm https://claude.ai/install.ps1 | iex
```

### Option B — npm

```powershell
npm install -g @anthropic-ai/claude-code
```

Do **not** prefix with `sudo` on Windows; it causes permission issues.

### Option C — WSL2 (most robust)

If WSL2 is installed, open your Ubuntu terminal and run the same install command as Option A or B. WSL eliminates almost all Windows path/permission gotchas.

### First-run authentication

```powershell
claude
```

A browser window opens — sign in with your Anthropic account. After that, the CLI is authorized.

### Verify

```powershell
claude --version
```

---

## 3. IDE Integration

### VS Code (recommended for this project)

1. Open VS Code.
2. `Ctrl + Shift + X` → Extensions panel.
3. Search **"Claude Code"** (publisher: Anthropic).
4. Click **Install**.
5. Reload if prompted. The Claude panel will appear in the sidebar; you can also launch it from the command palette (`Ctrl + Shift + P` → "Claude Code").

The extension gives you a chat panel, file `@`-mentions, conversation history, and checkpointing.

### Visual Studio (full Microsoft IDE)

There is **no official Claude Code plugin for the full Visual Studio IDE** at the time of writing. Recommended workarounds, in order:

1. **Use VS Code** with the Claude Code extension (it handles LaTeX + Python well, which is what this project needs).
2. Run **Claude Code in the terminal** alongside Visual Studio — open a PowerShell pane and use `claude` from there.
3. If you switch to a JetBrains IDE (PyCharm, etc.), there is an official **JetBrains plugin** in the marketplace.

### JetBrains (alternative)

In any JetBrains IDE: **Settings → Plugins → Marketplace → search "Claude Code" → Install**.

---

## 4. First Session on This Project

Open PowerShell:

```powershell
cd "C:\Users\rizk\Desktop\GRADUATION PROJECT"
claude
```

Useful first commands inside Claude Code:

- `/init` — create or refresh `CLAUDE.md` (you already have one — Claude will read it on every run).
- `read memory/project_context.md and summarize the pivot` — confirms Claude has loaded the project context.
- `review REE598_proposal.tex against docs/REE598_PROPOSAL_REVIEW.md and list outstanding fixes` — kicks off real work.

Because `CLAUDE.md` already pins:

- The pivot to the autonomous TEC PV-cleaning robot at three scales,
- The terse-chat style,
- IEEE citations / SI units / chapter-based numbering,

…Claude Code will pick up those conventions automatically in every session you start from this folder.

---

## 5. Windows-Specific Gotchas

- **Use PowerShell** rather than CMD. The native installer requires PowerShell, and quoting paths with spaces is easier.
- **Folder name has a space** (`GRADUATION PROJECT`). Always wrap in double quotes when using `cd`:
  `cd "C:\Users\rizk\Desktop\GRADUATION PROJECT"`.
- **Antivirus / Defender** sometimes flags global npm installs. If `claude` isn't found after install, check `npm root -g` is on your PATH.
- **WSL fallback**: if anything misbehaves on native Windows (path issues, EOL conversions in `.tex` files, Python venv quirks), reinstall Claude Code inside WSL2 and run it from there — your project folder is reachable as `/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT`.
- **LaTeX toolchain**: Claude Code does not bundle a TeX distribution. Install **MiKTeX** or **TeX Live** separately if you want Claude to compile `.tex` files locally.

---

## 6. Official Documentation

- Quickstart: <https://code.claude.com/docs/en/quickstart>
- VS Code integration: <https://code.claude.com/docs/en/vs-code>
- Platforms / advanced setup: <https://code.claude.com/docs/en/platforms>
- Overview: <https://code.claude.com/docs/en/overview>

---

## 7. Recommended Next Step (when you're back)

1. Run the PowerShell installer (Section 2, Option A).
2. Install the VS Code extension (Section 3).
3. Open VS Code on `C:\Users\rizk\Desktop\GRADUATION PROJECT`, launch Claude, and ask:
   *"Read CLAUDE.md and docs/REE598_PROPOSAL_REVIEW.md, then propose a prioritized work plan for the proposal fixes."*

That gets you straight back into the proposal work the pivot brief is pointing at.
