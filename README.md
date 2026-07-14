# energy-ag

Daily automation that scrapes solar energy production from four inverter dashboards (WEG/FusionSolar, SAJ, SolisCloud, Growatt) and emails a consolidated report with screenshots.

## Running without RCC (recommended for local dev)

### 1. Install dependencies

Requires Python 3.11+ and [uv](https://github.com/astral-sh/uv).

```bash
uv sync
source .venv/bin/activate
```

### 2. Configure credentials

```bash
cp .env.example .env
# fill in credentials for each inverter and SMTP
```

> **Note:** `.env` is only loaded when running directly via uv/Python (`load_dotenv()` in `tasks.py`). When running via `rcc run` or Control Room, credentials must come from Robocorp Vault or Control Room environment variables instead.

### 3. Run

```bash
python -m robocorp.tasks run tasks.py
```

To test a single scraper in isolation:

```bash
python workflow/process.py
python workflow/solis.py
```

Artifacts (screenshots on failure or timeout retry, report images) are written to `output/`.

---

## Running with RCC

[RCC](https://github.com/robocorp/rcc) builds an isolated conda environment from `conda.yaml` automatically.

```bash
rcc run
```

---

## Deployment (Robocorp Control Room)

Pushing to `main` automatically deploys to Robocorp via GitHub Actions. The workflow uses `rcc cloud push` — no manual zipping or uploading needed.

Required GitHub secrets:

| Secret | Where to find it |
|---|---|
| `ROBOCORP_CREDENTIALS` | Control Room → profile → Access credentials → Generate |
| `ROBOCORP_WORKSPACE_ID` | UUID from `rcc cloud workspace` or Control Room URL |
| `ROBOCORP_ROBOT_ID` | Numeric ID from `rcc cloud workspace --workspace <id>` |

To deploy manually from the command line:

```bash
rcc cloud push --account "$ROBOCORP_CREDENTIALS" --workspace "$ROBOCORP_WORKSPACE_ID" --robot "$ROBOCORP_ROBOT_ID"
```

---

## Project layout

```
tasks.py                    # @task entry point — loads .env, calls Process.start()
workflow/
  process.py                # Orchestrator: runs WEG/SAJ/Solis in parallel threads + Growatt on main thread → sends email
  weg.py                    # Playwright scraper for WEG/Huawei FusionSolar
  saj.py                    # Playwright scraper for SAJ portal
  solis.py                  # Playwright scraper for SolisCloud
  growatt.py                # REST API client for Growatt (no browser needed)
utils/
  email_util.py             # SMTP sender with multiple image attachments
  secrets_util.py           # Credential lookup: Robocorp Vault → os.environ
  utils.py                  # send_generated_energy_email() — assembles and sends the report; appends a Notes block when scrapers emit runtime flags
libraries/
  logger.py                 # Shared logging setup
  decorators.py             # @screenshot_on_error — saves screenshot on scraper failure; @retry_on_timeout — retries on Playwright timeout with increasing timeout and per-attempt screenshots
```

## Environment variables

| Variable | Description |
|---|---|
| `FUSION_URL/LOGIN/PASSWORD` | WEG/Huawei FusionSolar |
| `SAJ_URL/LOGIN/PASSWORD` | SAJ portal |
| `SOLIS_URL/LOGIN/PASSWORD` | SolisCloud |
| `SOLIS_STATION` | Station name as it appears in the SolisCloud dashboard |
| `GROWATT_URL/TOKEN/SN/TYPE` | Growatt API |
| `SMTP_HOST/PORT/USER/PASSWORD` | Outbound mail server |
| `EMAIL_FROM` | Sender address |
| `EMAIL_TO` | Recipient(s), comma-separated |
| `HEADLESS` | Set to `false` locally to see the browser window (default: `true`) |
| `ROBOCORP_CREDENTIALS` | `rcc cloud push` auth token (CI/CD only) |
| `ROBOCORP_WORKSPACE_ID` | Robocorp workspace UUID (CI/CD only) |
| `ROBOCORP_ROBOT_ID` | Robocorp robot ID (CI/CD only) |

---

## Parallel scraper execution

The three browser scrapers (WEG, SAJ, Solis) previously ran one after another on a single Playwright page, taking ~90s total. They are now parallelised using Python threads.

**Why one `sync_playwright()` per thread, not one shared instance:** Playwright's sync API is not thread-safe — sharing a single Playwright or Browser object across threads causes race conditions. The solution is to give each thread its own isolated `sync_playwright()` context, which means each scraper gets its own browser process. This is safe and idiomatic for Playwright's sync API.

**How it works in `process.py`:**
1. Three threads are created, one per browser scraper.
2. Each thread calls `_run_browser_scraper`, which opens `sync_playwright() → browser → page`, runs the scraper, then closes the browser.
3. Growatt (a plain HTTP call, no browser) runs on the main thread while the three browser threads are in flight.
4. The main thread joins all three threads, then checks for errors.
5. If any scraper raised an exception, the first error is re-raised (after logging all of them).

**Expected timing improvement:** ~90s sequential → ~44s parallel (bottlenecked by SAJ, the slowest scraper). Growatt finishes in under a second and waits on the others.

---

## Backlog

- **SAJ — session still active on retry**: when `retry_on_timeout` re-runs `get_production`, the portal session from the first attempt is still alive and the login form is skipped. Currently handled with an `is_visible()` guard, but the root fix is to properly clear or expire the session between attempts.
- **Workflow performance**: parallel scrapers are implemented (see section above). Remaining item: `solis.py` has `sleep(5)` and `saj.py` has `sleep(3)` before screenshots — evaluate whether these are still needed and remove if not.
- **Replace browser scrapers with APIs**: WEG/FusionSolar, SAJ, and SolisCloud are currently scraped via Playwright. Growatt already uses a REST API — investigate whether the other three expose official or undocumented APIs that could replace the browser automation entirely (faster, more reliable, no Chromium needed).
  - **SAJ investigation**: SAJ has an official open platform called **Elekeeper** (`eop.saj-electric.com`, developer portal at `developer.saj-electric.com`). Access requires emailing `consulta@saj-electric.com` with your inverter serial number. However, the platform targets distributors and installers managing multiple plants at scale — not viable for a personal single-account user. A more practical alternative would be to intercept the network requests the `iop.saj-electric.com` portal makes in the browser and replicate those calls directly (same approach as Growatt).
