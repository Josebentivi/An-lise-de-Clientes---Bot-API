# Repository Guidelines

## Project Structure & Module Organization
- `visualizardados.py`: Streamlit entrypoint and all dashboard rendering.
- `analytics.py`: reusable analytics layer for event cleaning, classification, cohorts, funnels, and summaries. Keep UI code out of this module.
- `tests/test_analytics.py`: unit tests for analytics behavior.
- `requirements.txt`: pinned Python dependencies.
- `README.md`: local setup and usage notes.
- `scriptsql.sql` and `resultados.txt`: reference/demo artifacts, not part of the Streamlit runtime.
- Ignore `__pycache__/` files in reviews; they are generated artifacts.

## Build, Test, and Development Commands
- `python -m pip install -r requirements.txt`
  Installs the project dependencies.
- `streamlit run visualizardados.py`
  Starts the dashboard locally.
- `python -m unittest discover -s tests -v`
  Runs the unit test suite.
- `python -c "import analytics, visualizardados; print('imports ok')"`
  Quick import smoke test after refactors.

## Coding Style & Naming Conventions
- Use 4-space indentation and follow standard Python style.
- Prefer `snake_case` for functions, variables, and file-level helpers.
- Keep analytics transformations pure and deterministic inside `analytics.py`.
- Keep Streamlit-specific layout, widgets, and plotting in `visualizardados.py`.
- Use short, targeted comments only where logic is not obvious.
- Preserve ASCII in new files unless the file already depends on accented text.

## Testing Guidelines
- Use Python `unittest`.
- Add tests for every new aggregation or classification rule, especially for cohorts, session boundaries, transitions, and failure-rate logic.
- Name test files `test_*.py` and test methods `test_*`.
- Prefer small in-memory fixtures over external files or API calls.

## Commit & Pull Request Guidelines
- Current history uses very short messages like `update` and `Update visualizardados.py`; improve this by using imperative, scoped messages such as `Add cohort retention heatmap`.
- Keep each commit focused on one change area.
- PRs should include:
  - a short summary of behavior changes
  - test commands executed
  - screenshots or short screen recordings for dashboard UI changes
  - any config or API dependency changes

## Security & Configuration Tips
- Never commit secrets.
- Configure `CHAVE` via Streamlit secrets or environment variables.
- Optional runtime settings: `JURISAI_API_URL` and `JURISAI_TIMEOUT_SECONDS`.
