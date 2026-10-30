# SAHIBEX Multi-Device Assistant — initial implementation

Status: **software baseline implemented; cross-device physical acceptance pending**.
This capability is part of the existing SAHIBEX repository, not a separate brain.

## What is implemented

- Cross-platform Python Desktop Agent for Windows, macOS and Linux.
- Authenticated request signatures (HMAC-SHA256), timestamp freshness checks and replay protection.
- Default loopback-only listener; non-loopback binding is refused unless TLS certificate/key are supplied.
- TLS 1.2+ for LAN access; the SAHIBEX client supports the system trust store or a dedicated CA via `SAHIBEX_DESKTOP_CA`.
- Unified Main Brain tool: `sahibex_control_bridge` routes work to the phone or the currently paired laptop/desktop using an explicit target.
- Phone target supports project-root listing/reading/writing, project-root command execution, and the existing permission-gated Android UI adapter. It does not claim unrestricted access to Android's private/system files.
- Desktop target supports status, bounded directory listing, text file creation/overwrite (48 KiB request-content limit), and allowlisted program execution (argv list, no shell, 1–60 second timeout), plus HTTP(S) browser opening.
- Desktop writes, command execution and browser opening each require a separate approval typed on that desktop's interactive console. Without a console, they fail closed.
- Requests use HMAC-SHA256, timestamp freshness, nonce replay protection, and strict body bounds. Remote connections require TLS; there is no plain-HTTP LAN fallback.
- Main Brain tool registration retains SAHIBEX's canonical permission gateway and explicit confirmation. The desktop target is available only when `SAHIBEX_DESKTOP_AGENT_URL` and `SAHIBEX_DEVICE_TOKEN` are configured.
- Arbitrary shell, automatic approval, stealth access and credential extraction are not exposed. The desktop agent allows only named program launchers, but approved programs may perform the work requested within the allowlisted workspace; approve commands carefully.

## Pairing and launch

Pairing uses a high-entropy shared secret, stored privately as `SAHIBEX_DEVICE_TOKEN` on both endpoints. Never put it in screenshots, chat, source control or logs. Generate a different secret for each paired desktop.

On the **desktop/laptop**, install Python 3.11+ and obtain the SAHIBEX project code. From the repository root:

Linux/macOS:
```sh
export SAHIBEX_DEVICE_TOKEN='paste-a-private-random-secret-of-at-least-32-characters'
python -m tools.sahibex_desktop_agent --host 127.0.0.1 --port 38743 --root workspace=/path/to/approved/workspace
```

Windows PowerShell:
```powershell
$env:SAHIBEX_DEVICE_TOKEN = 'paste-a-private-random-secret-of-at-least-32-characters'
python -m tools.sahibex_desktop_agent --host 127.0.0.1 --port 38743 --root workspace=C:\\Users\\YourUser\\Documents\\ApprovedWorkspace
```

Loopback is for testing on the desktop itself. It is not reachable from the phone.

## LAN connection (TLS required)

1. On the desktop, create/provision a TLS certificate whose Subject Alternative Name includes the desktop's LAN IP or DNS name. Do not expose the agent over plain HTTP.
2. Copy/trust the issuing CA certificate on the SAHIBEX phone in a private location. Avoid disabling certificate verification.
3. Start the agent on the desktop with `--host 0.0.0.0 --port 38743 --tls-cert /path/to/cert.pem --tls-key /path/to/private-key.pem --root workspace=/path/to/approved/workspace` (Windows paths can be supplied normally). Keep the key private. Only the chosen workspace is exposed for directory listing; no root is exposed by default.
4. In the Termux session that starts SAHIBEX, set:
   ```sh
   export SAHIBEX_DEVICE_TOKEN='the-same-private-pairing-secret'
   export SAHIBEX_DESKTOP_AGENT_URL='https://DESKTOP-LAN-IP:38743'
   export SAHIBEX_DESKTOP_CA='/private/path/to/issuing-ca.pem'
   ```
   Then restart the SAHIBEX Main Brain process so its runtime registry sees the configuration.
5. Check the desktop agent's health endpoint locally, then ask SAHIBEX to inspect the paired device. The agent's authenticated endpoint is `/v1/device`; the public `/health` endpoint reveals no device information.
6. For `open_url`, the person at the desktop must type `YES` in that computer's own interactive console. If the agent has no interactive console, the action fails closed.

Firewall access should be restricted to the phone's trusted LAN address where practical. Never port-forward this agent to the public internet.

## Verification boundaries

- Software acceptance: `tests/unit/test_sahibex_device_fabric.py` tests signatures, replay/staleness rejection, directory-root confinement, client transport policy and a local HTTP integration path.
- No laptop is currently connected to this Termux session. Therefore Windows/macOS/Linux packaging, phone-to-laptop TLS connectivity, actual desktop browser launch, network firewall behavior and physical end-to-end assistance remain **PENDING external-device acceptance**.
- Android Companion remains the existing app; its local voice bridge is still loopback-bound. This desktop agent is a separate endpoint that the phone's Main Brain can call when LAN/TLS configuration is supplied.
- No P1–P12 gate is automatically passed by adding this feature. P6/P7/P8/P10/P11 statuses remain governed by the phase-gate registry.

## How the Main Brain routes work

The registered tool name is `sahibex_control_bridge`. The Main Brain selects the target and action from the user's request; it does not guess that a desktop is paired.

Examples of the internal routed request shape:
```json
{"target":"phone","action":"list_directory","parameters":{"path":"docs"}}
{"target":"phone","action":"write_file","parameters":{"path":"notes/example.txt","content":"Hello from SAHIBEX"}}
{"target":"laptop","action":"device_status","parameters":{}}
{"target":"laptop","action":"write_file","parameters":{"root":"workspace","path":"hello.py","content":"print('hello')"}}
{"target":"laptop","action":"run_command","parameters":{"root":"workspace","cwd":".","argv":["python","hello.py"],"timeout_seconds":20}}
```
These are tool request examples, not commands for the user to paste into chat. A protected action still requires the Main Brain's permission/confirmation, and desktop writes/commands require the local desktop approval prompt too.

The current version supports one configured desktop endpoint. Multiple named computers need a device registry and separate credentials/endpoints; do not point one shared token at untrusted devices.

## Current acceptance state

- Software integration tests: **15 passed** across the new bridge tests and adjacent registry/permission/tool suites.
- Python syntax/compile and whitespace checks are re-run after the final code changes; the checkpoint log records the current result.
- Physical phone-to-laptop TLS pairing and desktop-console approval remain pending because no separate computer is connected to this Termux session.
