# Screenshot Attempt Log (2026-04-10)

Requested output: screenshots of the current web design with a dummy project.

## Attempted steps

1. `bash scripts/bootstrap.sh`
   - Result: failed because Python 3.12+ is required in this environment.
2. `npm ci`
   - Result: succeeded.
3. `npx playwright install chromium`
   - Result: failed due repeated `403 Forbidden` downloading Playwright Chromium binaries from CDN.

## Blocking issues

- Browser automation runtime is unavailable in the current environment.
- The dedicated `browser_container` screenshot tool is not available in this session.

## Environment fixes (recommended)

### 1) Upgrade Python to 3.12+

Current interpreter: `Python 3.10.19`.

Use one of these approaches:

- `pyenv` (developer workstation):
  - `pyenv install 3.12.10`
  - `pyenv local 3.12.10`
- system package manager (container image/base VM):
  - install `python3.12`, `python3.12-venv`, and ensure `python3` resolves to 3.12+

After upgrade, rerun:

- `bash scripts/bootstrap.sh`

### 2) Resolve Playwright browser download failures

The repeated `403 Forbidden` indicates the environment cannot fetch binaries from `https://cdn.playwright.dev`.

Options:

- Allow outbound access to:
  - `https://cdn.playwright.dev`
  - `https://playwright.download.prss.microsoft.com`
- If your network requires an internal mirror, configure:
  - `PLAYWRIGHT_DOWNLOAD_HOST=<your-approved-mirror>`
- If your network requires a proxy, set standard env vars:
  - `HTTPS_PROXY`, `HTTP_PROXY`, `NO_PROXY`

Then rerun:

- `npx playwright install chromium`

### 3) Clean npm proxy misconfiguration warning

This environment shows:

- `npm warn Unknown env config "http-proxy"`

Clear invalid env config and use canonical proxy env vars (`HTTP_PROXY` / `HTTPS_PROXY`) instead of legacy `http-proxy`.

## Next step when environment permits

- Install a working browser runtime (or enable `browser_container`) and run a scripted Playwright capture flow against `apps/web` with mocked or seeded dummy project data.
