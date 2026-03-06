# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
python -m pip install -r requirements.txt

# Run dashboard locally (http://localhost:8501)
streamlit run visualizardados.py

# Run tests
python -m unittest discover -s tests -v

# Quick import smoke test after refactors
python -c "import analytics, visualizardados; print('imports ok')"
```

## Configuration

Required: Set `CHAVE` (API auth key) via Streamlit secrets (`.streamlit/secrets.toml`) or as an environment variable.

Optional env vars:
- `JURISAI_API_URL`: API endpoint (default: `http://52.2.202.37/streamlit/`)
- `JURISAI_TIMEOUT_SECONDS`: Request timeout (default: 30)

Copy `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml` and fill in `CHAVE`.

## Architecture

This is a Streamlit analytics dashboard for the JurisAI platform with strict module separation:

- **`analytics.py`**: Pure, UI-agnostic analytics logic. All event/user transformations, session detection, segmentation, cohort computation, and feature classification live here. Never add Streamlit code here.
- **`visualizardados.py`**: All Streamlit UI — sidebar filters, tab rendering, API calls with 10-minute cache (`@st.cache_data`), and download button for PPTX export.
- **`presentation_export.py`**: PPTX generation (5-slide deck) from aggregated analytics context.
- **`tests/`**: Unit tests using Python `unittest` with small in-memory fixtures; no API calls.

### Data Flow

```
JurisAI API (POST) → raw lists → analytics.py transforms → Streamlit tabs
                                                          → presentation_export.py → .pptx download
```

The API returns two datasets (POST with `produto: "jurisai"` or `"jurisaiusuarios"`):
- **Events**: `[usuario_id, acao, data]` — raw user action log
- **Users/Snapshots**: `[usuario_id, data, fonte, obs, creditos_chat, creditos_consulta]`

No persistent database — all processing is in-memory Pandas DataFrames.

### Key Analytics Concepts

- **Session detection**: 30-minute idle gap splits sessions; session ID = `{user_id}-{session_number}`
- **Feature classification**: Keyword-based via `FEATURE_RULES` dict in `analytics.py`; action strings in Portuguese
- **User segments**: Power user / Recorrente / Explorador / Novo — defined by thresholds on actions, active days, unique features, and sessions
- **Date format**: `%Y/%m/%d %H:%M:%S`; cohorts use monthly periods

### Dashboard Tabs

1. **Visão Geral**: KPI cards, growth charts, credit distribution
2. **Retenção**: Retention histogram, cohort heatmap, segmentation
3. **Features**: Adoption table, failure rates, activity heatmap
4. **Jornada**: Engagement funnel, session table, feature transitions, per-user time analysis
5. **Qualidade**: Data quality profiles, uncategorized actions

## Coding Style

- 4-space indentation, `snake_case` naming
- Keep analytics transformations pure and deterministic in `analytics.py`
- Add `unittest` tests for every new aggregation or classification rule
- Use imperative, scoped commit messages (e.g., `Add cohort retention heatmap`)
