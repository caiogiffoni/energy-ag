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

### 3. Run

```bash
python -m robocorp.tasks run tasks.py
```

To test a single scraper in isolation:

```bash
python workflow/process.py
python workflow/solis.py
```

Artifacts (screenshots on failure, report images) are written to `output/`.

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
tasks.py                    # @task entry point — loads .env, opens Playwright, calls Process.start()
workflow/
  process.py                # Orchestrator: runs all 4 scrapers → sums production → sends email
  weg.py                    # Playwright scraper for WEG/Huawei FusionSolar
  saj.py                    # Playwright scraper for SAJ portal
  solis.py                  # Playwright scraper for SolisCloud
  growatt.py                # REST API client for Growatt (no browser needed)
utils/
  email_util.py             # SMTP sender with multiple image attachments
  secrets_util.py           # Credential lookup: Robocorp Vault → os.environ
  utils.py                  # send_generated_energy_email() — assembles and sends the report
libraries/
  logger.py                 # Shared logging setup
  decorators.py             # @screenshot_on_error — saves screenshot on scraper failure
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
