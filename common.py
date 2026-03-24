from __future__ import annotations

from pathlib import Path
import base64
import html as html_std
import json
import streamlit as st


def load_css(relative_path: str = "styles/app.css") -> None:
    css_path = Path(__file__).resolve().parent / relative_path
    if not css_path.exists():
        return
    css = css_path.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def _img_to_base64(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except Exception:
        return ""


def _load_css_text(relative_path: str = "styles/app.css") -> str:
    css_path = Path(__file__).resolve().parent / relative_path
    if not css_path.exists():
        return ""
    return css_path.read_text(encoding="utf-8")


def render_topbar(
    ticker_text: str,
    ticker_text_en: str,
    logo_path: str | None = None,
    clock_timezone: str = "Asia/Ho_Chi_Minh",
    extra_class: str = "",
    show_logo: bool = True,
    show_clock: bool = True,
    show_controls: bool = True,
    show_ticker: bool = True,
) -> None:
    safe_ticker = html_std.escape(ticker_text or "")
    safe_ticker_en = html_std.escape(ticker_text_en or "")
    logo_html = ""
    if show_logo and logo_path:
        logo_b64 = _img_to_base64(logo_path)
        if logo_b64:
            logo_html = (
                f'<img class="topbar__logo" src="data:image/png;base64,{logo_b64}" alt="logo" />'
            )

    extra_class = extra_class.strip()
    extra_class = f" {extra_class}" if extra_class else ""

    clock_html = (
        '<div class="topbar__clock" id="topbar-clock">--:--:--</div>'
        if show_clock
        else ""
    )
    controls_html = (
        """
        <div class="topbar__controls">
            <button class="topbar__btn" id="toggle-theme">Light</button>
            <button class="topbar__btn" id="toggle-lang">VI</button>
        </div>
        """
        if show_controls
        else ""
    )
    ticker_html = (
        f"""
        <div class="news-ticker">
            <span class="news-ticker__track" data-lang="vi">{safe_ticker}</span>
            <span class="news-ticker__track" data-lang="en">{safe_ticker_en}</span>
        </div>
        """
        if show_ticker
        else ""
    )

    tz_json = json.dumps(clock_timezone)

    iframe_css = _load_css_text()

    st.components.v1.html(
        f"""
        <style>
        {iframe_css}
        </style>
        <div class="topbar{extra_class}" style="display:flex;flex-direction:row;align-items:center;gap:8px;">
            {logo_html if show_logo else ""}
            {clock_html}
            {controls_html}
            {ticker_html}
        </div>

        <script>
        (function() {{
            const clockEl = document.getElementById("topbar-clock");
            const topbar = document.querySelector(".topbar");
            const themeBtn = document.getElementById("toggle-theme");
            const langBtn = document.getElementById("toggle-lang");
            const trackVi = document.querySelector('.news-ticker__track[data-lang="vi"]');
            const trackEn = document.querySelector('.news-ticker__track[data-lang="en"]');
            const parentDoc = (window.parent && window.parent.document) ? window.parent.document : document;
            const parentBody = parentDoc.body || document.body;
            const storage = (window.parent && window.parent.localStorage) ? window.parent.localStorage : window.localStorage;
            const THEME_KEY = "topbar_theme";
            const LANG_KEY = "topbar_lang";

            function tick() {{
                const now = new Date();
                const fmt = new Intl.DateTimeFormat("en-GB", {{
                    timeZone: {tz_json},
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                    hour12: false
                }});
                if (clockEl) {{
                    clockEl.textContent = fmt.format(now);
                }}
            }}
            if (clockEl) {{
                tick();
                setInterval(tick, 1000);
            }}

            function applyTheme(isDark) {{
                if (topbar) {{
                    topbar.classList.toggle("theme-dark", isDark);
                    topbar.classList.toggle("theme-light", !isDark);
                }}
                if (parentBody) {{
                    parentBody.classList.toggle("theme-dark", isDark);
                    parentBody.classList.toggle("theme-light", !isDark);
                }}
                if (themeBtn) {{
                    themeBtn.textContent = isDark ? "Dark" : "Light";
                }}
                try {{
                    storage.setItem(THEME_KEY, isDark ? "dark" : "light");
                }} catch (e) {{}}
            }}

            function applyLang(lang) {{
                if (!trackVi || !trackEn) return;
                const useVi = (lang || "vi").toLowerCase() === "vi";
                trackVi.style.display = useVi ? "inline-block" : "none";
                trackEn.style.display = useVi ? "none" : "inline-block";
                if (langBtn) {{
                    langBtn.textContent = useVi ? "VI" : "EN";
                }}
                try {{
                    storage.setItem(LANG_KEY, useVi ? "vi" : "en");
                }} catch (e) {{}}
            }}

            if (themeBtn) {{
                let storedTheme = "light";
                try {{
                    storedTheme = storage.getItem(THEME_KEY) || "light";
                }} catch (e) {{}}
                applyTheme(storedTheme === "dark");
                themeBtn.addEventListener("click", () => {{
                    const isDark = !parentBody.classList.contains("theme-dark");
                    applyTheme(isDark);
                }});
            }}

            if (langBtn && trackVi && trackEn) {{
                let storedLang = "vi";
                try {{
                    storedLang = storage.getItem(LANG_KEY) || "vi";
                }} catch (e) {{}}
                applyLang(storedLang);
                langBtn.addEventListener("click", () => {{
                    const isVi = trackVi.style.display !== "none";
                    applyLang(isVi ? "en" : "vi");
                }});
            }}

            // Button flash to white on click
            document.querySelectorAll(".topbar__btn").forEach((btn) => {{
                btn.addEventListener("click", () => {{
                    btn.style.transition = "background-color 1200ms ease, color 600ms ease, box-shadow 600ms ease";
                    btn.classList.add("btn-white");
                    setTimeout(() => btn.classList.remove("btn-white"), 1200);
                }});
            }});
        }})();
        </script>
        """,
        height=80,
    )
