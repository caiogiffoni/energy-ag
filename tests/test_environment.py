from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_ENV_KEYS = {
    "FUSION_URL", "FUSION_LOGIN", "FUSION_PASSWORD",
    "SAJ_URL", "SAJ_LOGIN", "SAJ_PASSWORD",
    "SOLIS_URL", "SOLIS_LOGIN", "SOLIS_PASSWORD",
    "GROWATT_URL", "GROWATT_TOKEN", "GROWATT_SN", "GROWATT_TYPE",
    "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD",
    "EMAIL_FROM", "EMAIL_TO",
    "HEADLESS",
}


def test_all_modules_import_cleanly():
    from workflow.process import Process
    import workflow.weg  # noqa: F401
    import workflow.saj  # noqa: F401
    import workflow.solis  # noqa: F401
    import workflow.growatt  # noqa: F401
    import utils.utils  # noqa: F401
    import utils.email_util  # noqa: F401
    import utils.secrets_util  # noqa: F401
    import libraries.decorators  # noqa: F401
    import libraries.logger  # noqa: F401

    assert isinstance(Process, type)


def test_env_example_declares_all_required_keys():
    env_example = REPO_ROOT / ".env.example"
    declared_keys = set()
    for line in env_example.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        declared_keys.add(line.split("=", 1)[0].strip())

    missing = REQUIRED_ENV_KEYS - declared_keys
    assert not missing, f".env.example is missing required keys: {sorted(missing)}"


def test_ensure_chromium_skips_install_when_binary_present(monkeypatch, tmp_path):
    from workflow.process import Process

    monkeypatch.setenv("HOME", str(tmp_path))
    chrome_path = tmp_path / ".cache" / "ms-playwright" / "chromium-1234" / "chrome-linux64" / "chrome"
    chrome_path.parent.mkdir(parents=True)
    chrome_path.touch()

    def fail_if_called(*args, **kwargs):
        raise AssertionError("subprocess.run should not be called when chromium is already installed")

    monkeypatch.setattr("workflow.process.subprocess.run", fail_if_called)

    process = Process(playwright=object())
    process._ensure_chromium()


def test_ensure_chromium_installs_when_binary_missing(monkeypatch, tmp_path):
    from workflow.process import Process

    monkeypatch.setenv("HOME", str(tmp_path))

    calls = []
    monkeypatch.setattr("workflow.process.subprocess.run", lambda *a, **k: calls.append((a, k)))

    process = Process(playwright=object())
    process._ensure_chromium()

    assert len(calls) == 1
    args, kwargs = calls[0]
    assert args[0] == ["playwright", "install", "chromium"]
    assert kwargs.get("check") is True
