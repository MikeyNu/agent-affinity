# Desktop Commander, Codex and other-agent routing

## Goal and priority

The author's Windows computer is the editing workstation. **Do not equate
chat access to GUI access.** Pick the first route actually available:

| Route | Requirements | Allowed work | Evidence to collect |
|---|---|---|---|
| Affinity native MCP | Affinity by Canva running, MCP enabled and connected | Native `execute_script`, `render_spread`, `render_selection` if exposed | Actual tool outputs and rendered inspection |
| Codex local desktop | Agent can call approved desktop/process/GUI tools on the correct PC | File work, verified native scripts and UI operations | Process result, screenshots, saved file |
| Remote Desktop Commander MCP | No usable local Codex route; authorized device online | Shell, filesystem, start processes; UI via separately verified interface | Device ID, shell exit, file hashes, optional UI evidence |
| Offline contract-only | All device routes unavailable | Validate locally available inputs, write plan, prepare handoff | Explicit offline status; no fabricated GUI work |

**Claude and agents other than Codex:** if Affinity MCP is exposed, use it.
Otherwise try Remote Desktop Commander MCP to the authorized Windows PC.
If the agent cannot invoke the remote tool, it cannot remotely edit Affinity.
Do not require a Codex-only shell or assume another agent sees the same tools.

## Device discovery and authentication

1. Discover the MCP catalog for a Desktop Commander connection. Invoke
   `list_devices`, identify the **authorized** online Windows workstation,
   select its returned `deviceId`. If multiple are online, use the
   explicitly authorized device. Never hardcode a GUID from prior sessions.
2. Call `get_config` to learn shell, OS, allowed directories and blocked
   commands. Respect all reported restrictions. Do not reconfigure the
   server to bypass restrictions.
3. Use `list_directory` and `read_file` for local project checks. Use
   `start_process` for non-destructive PowerShell/Python commands.
   Windows paths must be quoted, and PowerShell should run without an
   extra nested powershell -Command wrapper when the remote shell
   already is PowerShell.
4. For long calls, poll `read_process_output` by returned PID; if a remote
   invocation itself provides a `call_id`, query `get_tool_result`. Do not
   restart a side-effecting operation just because the response timed out.
5. Establish user/project authorization for any write or launch. Avoid
   sweeping searches of unrelated desktop folders. Never read credentials
   or secrets into model context. No unapproved installs or account logins.
6. Never modify active project controller, source queue, claims, art or
   other agent-owned output just to gain editor access. Own the downstream
   native master and publishing subfolder, with an explicit writer lease.
7. Log the actual transport and device identifier in the page handoff.
   Device IDs should remain in local production logs, not public repos.

## Windows preflight

Run this read-only probe through an authorized Desktop Commander terminal:

```powershell
python scripts/affinity_contract.py preflight --workspace "C:/Users/USER/Desktop/Gatsheni"
Get-AppxPackage | Where-Object Name -Match 'Affinity'
Get-Process | Where-Object ProcessName -Match 'Affinity'
Get-ChildItem "C:/Program Files" -Directory | Where-Object Name -Match 'Affinity'
```

A blank process list is not proof that software is absent; an MSIX install
may be present without a running process. If the app is being installed,
report installation pending and retry in a *new real task turn*, not by
inventing completion. Verify app identity and installed version by a
trusted application location, AppX package or in-app About dialog.
Running a version 2 application is not equivalent to the 2026 Affinity
unified app and its scripting.

To launch: use an executable path already verified on the user machine
and an actual approved process call, or use the Windows Start menu via
a verified GUI tool. Do not guess a private executable or AppUserModelID.

## Desktop Commander is not a mouse controller

The connected Remote Desktop Commander described here exposes filesystem,
terminal and process management actions; it does **not** automatically expose
screenshot, click, keyboard or Windows UI Automation APIs. A shell can
launch an app and inspect saved files, but that is not proof it edited a
layer, found the correct window or exported a page.

When UI is required, use one of:
- a connected Affinity MCP with verified `execute_script` and render calls;
- an explicitly available, authorized desktop automation tool with actual
  screenshots and target-window verification;
- a tested PowerShell/Python UI Automation integration installed on that
  desktop and confirmed to work on this Affinity build;
- a human editor handoff when those capabilities are absent.

Never run blind coordinate-click macros against an unknown window or locked
screen. Never install accessibility/screen-capture tools solely to imply
capability. Require a before and after screenshot or rendered output plus
changed native file evidence for every critical GUI action.

## Parallel agent safety

Use page-level exclusive leases:
`publishing/locks/<page-id>.lock` containing owner, source digest, target,
and expiry/recovery policy. Obtain exclusivity using atomic creation
(`open(..., "x")`) when a dedicated controller does not already manage locks.
Do not take locks over the existing Gatsheni controller. Expired locks are
**not** permission to replace another writer's work without checking owner,
live sessions and output revision. Favor one publisher with multiple
read-only reviewers.

Before save, reread source hashes and target revision; reject changed
dependencies. Save to a new versioned native path. Update `HANDOFF.md` only
after actual verified save and export checks. Publish master files to Git
only when explicitly requested and after checking filename/size/rights.

## Recovery matrix

| Situation | Safe outcome |
|---|---|
| No Codex desktop | Discover Desktop Commander device |
| Claude has local Affinity MCP | Use it; retain normal local-file protection |
| Desktop Commander offline | Stage offline handoff; do not claim edit |
| Terminal online but no GUI | Perform structural checks; request GUI-capable route for live visual work |
| App install incomplete | Record as pending, no false Affinity smoke pass |
| Remote command uncertain | Poll PID or call_id before retry |
| Permission prompt or unexpected app | Stop UI action, verify with operator |
| Another page owner active | Do read-only parity review |
| Stale approved image hash | Block and re-run Mangaka acceptance |
| Native project cannot reopen | Preserve prior file and regenerate a candidate revision from verified inputs |
