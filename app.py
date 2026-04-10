"""
Entrypoint shim.
- If run via Streamlit, import the main Streamlit script.
- If run as a plain Python module, bootstrap Streamlit.
"""

from __future__ import annotations

from pathlib import Path


def _running_in_streamlit() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        return get_script_run_ctx() is not None
    except Exception:
        return False


APP_SCRIPT = str(Path(__file__).with_name("Greatfut.py"))

if _running_in_streamlit():
    # Streamlit is already running this script; load the real app.
    import Greatfut  # noqa: F401
else:
    # Standard python entrypoint (e.g., python app.py)
    from streamlit.web import bootstrap

    bootstrap.run(APP_SCRIPT, "streamlit run", [], {})
