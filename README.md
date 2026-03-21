# energy-ag

## Robocorp + Playwright boilerplate

Browser automation uses [robocorp-browser](https://pypi.org/project/robocorp-browser/) (Playwright under the hood) and [robocorp.tasks](https://pypi.org/project/robocorp/).

### Prerequisites

- [RCC](https://github.com/robocorp/rcc) (command-line robot runner), or [Robocorp Code](https://robocorp.com/docs/developer-tools/visual-studio-code/extension) in VS Code / Cursor.

### Run

From this directory:

```bash
rcc run
```

Or run the task directly inside the conda environment created from `conda.yaml`:

```bash
python -m robocorp.tasks run tasks.py
```

First run may need Playwright browsers installed in that environment:

```bash
python -m playwright install chromium
```

Artifacts (screenshots on failure, etc.) go to `output/` as configured in `robot.yaml`.

### Layout

| File        | Role                                              |
| ----------- | ------------------------------------------------- |
| `robot.yaml` | Task names, env config, `artifactsDir`, paths   |
| `conda.yaml` | Python + pip deps for reproducible RCC env       |
| `tasks.py`   | `@task` functions; use `browser.goto`, locators  |

### References

- [Robocorp Python browser template](https://github.com/robocorp/template-python-browser) (official example with Excel + RPA extras)
- [Robot YAML recipes (RCC)](https://github.com/robocorp/rcc/blob/master/docs/recipes.md)
