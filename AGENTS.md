# Repository Guidelines

## Project Structure & Module Organization

`photoarch/` contains the Python package and CLI entry points. Core orchestration lives in `main.py`; domain models and configuration are in `models.py` and `config.py`. Keep specialized code in the existing subpackages: image and metadata processing in `analysis/`, filesystem organization in `fileops/`, keyword and caption logic in `language/`, and external integrations in `services/`. Tests mirror these responsibilities under `tests/`; reusable image fixtures belong in `tests/data/input/`. Runtime caches, downloaded models, and generated photo trees (`.photoarch/`, `models/`, `input_photos/`, and `sorted_photos/`) are local artifacts and must not be committed.

## Build, Test, and Development Commands

- `python -m venv .venv && source .venv/bin/activate` creates an isolated environment.
- `pip install -e '.[dev]'` installs the package, CLI, pytest, Black, and Ruff in editable mode.
- `pytest -v --log-cli-level=INFO tests/` runs the same test command used in CI.
- `pytest -m 'not longrunning' tests/` skips model-heavy integration cases during quick development.
- `ruff check photoarch tests` checks Python lint issues; `black --check photoarch tests` verifies formatting.
- `python -m photoarch --input input_photos --output sorted_photos --dry-run` exercises the CLI without copying photos.

ExifTool must be installed and on `PATH` for video metadata support and related tests.

## Coding Style & Naming Conventions

Target Python 3.14 and use four-space indentation. Follow Black formatting and Ruff diagnostics. Use `snake_case` for modules, functions, and variables; `PascalCase` for classes; and `UPPER_SNAKE_CASE` for constants. Add type annotations to public functions and keep imports grouped as standard library, third-party, then local. Extend the existing package boundaries instead of adding unrelated logic to `main.py`.

## Testing Guidelines

Tests use pytest, with many cases written as `unittest.TestCase`. Name files `test_<module>.py` and methods `test_<behavior>`. Mock network calls, model loading, and filesystem boundaries where practical. Mark expensive model or end-to-end cases with `@pytest.mark.longrunning`. No numeric coverage threshold is configured; new behavior and bug fixes should include focused regression tests.

## Commit & Pull Request Guidelines

Recent commits use short, imperative summaries such as `Fixed a bug when caption is empty` and `Add support for GIT image captioning model`. Keep each commit focused and avoid mixing refactors with behavior changes. Pull requests should explain the motivation and user-visible effect, list verification commands, link relevant issues, and call out model downloads, network behavior, or cache changes. Include sample CLI output when behavior changes; screenshots are only useful for generated folder layouts or other visual results.
