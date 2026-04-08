import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
from constants import index_options
import json

from vnstock import Company, Listing, Quote, Trading
try:
    from streamlit_elements import elements, mui, html
except Exception:
    elements = None
    mui = None
    html = None

import os
try:
    from gemini_ai import GeminiAI
except Exception:
    GeminiAI = None
from constants import (
    index_options,
    quote_symbols,
    group_symbols,
    GROUP_ELIGIBLE,
    INDEX_TO_QUOTE,
)
from common import load_css, render_topbar

st.set_page_config(page_title="Dữ liệu - Greatfut iBoard", layout="wide")
load_css()
REFRESH_MAIN_CHART_SECONDS = 60

### Đóng SIDEBAR ### 
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ### BAR ###
# # Auto-refresh page to pick up ticker file changes.
# st.components.v1.html(
#     "<script>setTimeout(() => window.location.reload(), 3600000);</script>",
#     height=0,
# )

# # Placeholder ticker text (used if no file-driven content yet)
# _ticker_default = (
#     "Tin nhanh: VNINDEX biến động mạnh trong phiên | VN30 giữ nhịp | "
#     "Thanh khoản cải thiện | Cập nhật từ nguồn API sẽ thay thế nội dung này"
# )

# TICKER_FILE = os.path.join(os.path.dirname(__file__), "ticker_text.txt")

# def load_ticker_text(default_text: str) -> str:
#     try:
#         if os.path.exists(TICKER_FILE):
#             with open(TICKER_FILE, "r", encoding="utf-8", errors="replace") as f:
#                 text = f.read().strip()
#                 if text:
#                     return text
#     except Exception:
#         pass
#     return default_text

# ticker_text = load_ticker_text(_ticker_default)

# logo_path = os.path.join(
#     os.path.dirname(__file__),
#     "image",
#     "Gemini_Generated_Image_uvz9l1uvz9l1uvz9.png",
# )
# render_topbar(
#     ticker_text=ticker_text,
#     ticker_text_en=(
#         "Breaking: VNINDEX volatile | VN30 steady | Liquidity improving | "
#         "API feed will replace this"
#     ),
#     logo_path=logo_path,
#     clock_timezone="Asia/Ho_Chi_Minh",
#     extra_class="topbar--dashboard",
# )
_ticker_default = (
    "Tin nhanh: VNINDEX biến động mạnh trong phiên | VN30 giữ nhịp | "
    "Thanh khoản cải thiện | Cập nhật từ nguồn API sẽ thay thế nội dung này"
)
TICKER_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ticker_text.txt")

def load_ticker_text(default_text: str) -> str:
    try:
        if os.path.exists(TICKER_FILE):
            with open(TICKER_FILE, "r", encoding="utf-8", errors="replace") as f:
                text = f.read().strip()
                if text:
                    return text
    except Exception:
        pass
    return default_text

ticker_text = load_ticker_text(_ticker_default)
logo_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "image",
    "Gemini_Generated_Image_uvz9l1uvz9l1uvz9.png",
)
render_topbar(
    ticker_text=ticker_text,
    ticker_text_en=(
        "Breaking: VNINDEX volatile | VN30 steady | Liquidity improving | "
        "API feed will replace this"
    ),
    logo_path=logo_path,
    clock_timezone="Asia/Ho_Chi_Minh",
    extra_class="topbar--vnindex",
)

def _nav_button(label: str, page_path: str) -> None:
    if hasattr(st, "switch_page"):
        if st.button(label, use_container_width=True):
            st.switch_page(page_path)
        return
    if hasattr(st, "page_link"):
        st.page_link(page_path, label=label, use_container_width=True)
        return
    st.info("Streamlit không hỗ trợ chuyển trang trong phiên bản này.")

@st.cache_data(ttl=3600)
def get_hose_symbols() -> list[str]:
    try:
        df = Listing(source="VCI").symbols_by_exchange(exchange="HOSE")
        if isinstance(df, pd.Series):
            return df.dropna().astype(str).unique().tolist()
        if isinstance(df, pd.DataFrame) and "symbol" in df.columns:
            return df["symbol"].dropna().astype(str).unique().tolist()
    except Exception:
        pass
    return []

FAV_LOCAL_KEY = "favorite_symbols"

def _localstorage_remove_favorites(symbols: list[str]) -> None:
    if not symbols:
        return
    safe_symbols = json.dumps([str(s) for s in symbols if str(s).strip()])
    components.html(
        f"""
        <script>
        (function() {{
            const key = {json.dumps(FAV_LOCAL_KEY)};
            const removeList = {safe_symbols};
            const raw = window.localStorage.getItem(key) || "[]";
            const list = JSON.parse(raw).filter(s => !removeList.includes(s));
            window.localStorage.setItem(key, JSON.stringify(list));
        }})();
        </script>
        """,
        height=0,
    )
    # Update local cache file
    cache_path = os.path.join(os.path.dirname(__file__), ".favorites_cache.json")
    try:
        existing = []
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                existing = json.loads(f.read() or "[]")
        if not isinstance(existing, list):
            existing = []
        existing = [s for s in existing if s not in set(symbols)]
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(existing, ensure_ascii=False))
    except Exception:
        pass


def _localstorage_add_favorite(symbol: str) -> None:
    if not symbol:
        return
    symbol = str(symbol).strip().upper()
    if not symbol:
        return

    safe_symbol = json.dumps(symbol)
    components.html(
        f"""
        <script>
        (function() {{
            const key = {json.dumps(FAV_LOCAL_KEY)};
            const sym = {safe_symbol};
            let list = [];
            try {{
                const raw = window.localStorage.getItem(key) || "[]";
                list = JSON.parse(raw);
                if (!Array.isArray(list)) list = [];
            }} catch (e) {{
                list = [];
            }}
            if (sym && !list.includes(sym)) {{
                list.push(sym);
                window.localStorage.setItem(key, JSON.stringify(list));
            }}
        }})();
        </script>
        """,
        height=0,
    )

    cache_path = os.path.join(os.path.dirname(__file__), ".favorites_cache.json")
    try:
        existing = []
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                existing = json.loads(f.read() or "[]")
        if not isinstance(existing, list):
            existing = []
        if symbol not in existing:
            existing.append(symbol)
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(existing, ensure_ascii=False))
    except Exception:
        pass
def _localstorage_remove_favorites(symbols: list[str]) -> None:
    symbols = [str(s).strip().upper() for s in symbols if str(s).strip()]
    if not symbols:
        return
    safe_symbols = json.dumps(symbols)
    components.html(
        f"""
        <script>
        (function() {{
            const key = {json.dumps(FAV_LOCAL_KEY)};
            const removeList = {safe_symbols};
            let list = [];
            try {{
                const raw = window.localStorage.getItem(key) || "[]";
                list = JSON.parse(raw);
                if (!Array.isArray(list)) list = [];
            }} catch (e) {{
                list = [];
            }}
            list = list.filter(s => !removeList.includes(String(s).toUpperCase()));
            window.localStorage.setItem(key, JSON.stringify(list));
        }})();
        </script>
        """,
        height=0,
    )

    cache_path = os.path.join(os.path.dirname(__file__), ".favorites_cache.json")
    try:
        existing = []
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                existing = json.loads(f.read() or "[]")
        if not isinstance(existing, list):
            existing = []
        existing = [str(s).strip().upper() for s in existing if str(s).strip()]
        existing = [s for s in existing if s not in set(symbols)]
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(existing, ensure_ascii=False))
    except Exception:
        pass



def _inject_localstorage_sync() -> None:
    components.html(
        f"""
        <script>
        (function() {{
            const key = {json.dumps(FAV_LOCAL_KEY)};
            function findTarget() {{
                const doc = window.parent && window.parent.document ? window.parent.document : document;
                const candidates = Array.from(doc.querySelectorAll("textarea"));
                return candidates.find(el =>
                    el.getAttribute("aria-label") === "fav_store_sync" ||
                    el.getAttribute("placeholder") === "fav_store_sync"
                );
            }}
            function sync() {{
                const el = findTarget();
                if (!el) return;
                const raw = window.localStorage.getItem(key) || "[]";
                if (el.value !== raw) {{
                    el.value = raw;
                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
            }}
            setTimeout(sync, 0);
            setTimeout(sync, 200);
            setTimeout(sync, 800);
        }})();
        </script>
        """,
        height=0,
    )

def _get_favorites_from_localstorage() -> list[str]:
    # Prefer localStorage sync field (source of truth), fallback to cache file.
    raw = st.session_state.get("fav_store_sync", "")
    if not raw:
        cache_path = os.path.join(os.path.dirname(__file__), ".favorites_cache.json")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    raw = f.read().strip()
            except Exception:
                raw = ""
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    return sorted({str(s).strip().upper() for s in data if str(s).strip()})


a1, a2, a3, a4 = st.columns(4)
with a1:
    _nav_button("Toàn cảnh thị trường", "pages/Toancanh_thitruong.py")
with a2:
    _nav_button("Danh sách các quỹ", "pages/Quymo.py")
with a3:
    _nav_button("VNData", "pages/VNIndex.py")
with a4:
    _nav_button("Giá vàng", "pages/GoldPrice.py")


c1, c2 = st.columns([1, 1])
with c1:
    start_date = st.date_input("Từ ngày", pd.Timestamp.today().date())
with c2:
    end_date = st.date_input("Đến ngày", pd.Timestamp.today().date())

if start_date > end_date:
    st.error("Từ ngày không được lớn hơn đến ngày")
    st.stop()

selected_label = index_options[0]
if len(index_options) != len(quote_symbols) or len(index_options) != len(group_symbols):
    st.error("Cấu hình index_options/quote_symbols/group_symbols không cùng độ dài.")
    st.stop()

selected_pos = index_options.index(selected_label)
quote_symbol = quote_symbols[selected_pos]
group_symbol = group_symbols[selected_pos]

###GEMINI###

def get_gemini_api_key() -> str:
    env_key = os.getenv("GEMINI_API_KEY", "").strip()
    return env_key

@st.cache_resource
def get_gemini_client(api_key: str):
    if GeminiAI is None or not api_key:
        return None
    return GeminiAI(api_key=api_key, gemini_model="gemini-2.5-flash")


def build_ai_context(price_df: pd.DataFrame, label: str, symbol: str, start_dt, end_dt) -> str:
    first_close = float(price_df["close"].iloc[0])
    last_close = float(price_df["close"].iloc[-1])
    change_pct = ((last_close - first_close) / first_close * 100) if first_close else 0.0
    return (
        f"Chi so: {label} ({symbol})\\n"
        f"Khoang thoi gian: {start_dt} den {end_dt}\\n"
        f"So diem du lieu: {len(price_df)}\\n"
        f"Gia dong dau ky: {first_close:.2f}\\n"
        f"Gia dong cuoi ky: {last_close:.2f}\\n"
        f"Bien dong: {change_pct:.2f}%\\n"
        f"Gia cao nhat: {float(price_df['high'].max()):.2f}\\n"
        f"Gia thap nhat: {float(price_df['low'].min()):.2f}\\n"
        f"Khoi luong TB: {float(price_df['volume'].mean()):.0f}\\n"
    )


@st.dialog("Chi tiết công ty", width="large")
def show_company_popup(symbol: str) -> None:
    st.write(f"### Mã: {symbol}")
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
        [
            "Thông tin",
            "Cổ đông",
            "Ban lãnh đạo",
            "Công ty liên kết",
            "Tin tức",
            "Sự kiện",
            "Giá niêm yết",
            "Giao dịch",
        ]
    )

    with tab1:
        try:
            profile_df = None
            profile_errors = []

            for src in ("KBS", "VCI"):
                try:
                    company = Company(symbol=symbol, source=src)
                    candidate = company.overview() if hasattr(company, "overview") else None
                    if candidate is None:
                        profile_errors.append(f"{src}: overview None")
                        continue

                    if not isinstance(candidate, pd.DataFrame):
                        candidate = pd.DataFrame([candidate]) if isinstance(candidate, dict) else pd.DataFrame(candidate)

                    if candidate.empty:
                        profile_errors.append(f"{src}: overview rỗng")
                        continue

                    profile_df = candidate
                    break
                except Exception as src_exc:
                    profile_errors.append(f"{src}: {type(src_exc).__name__}: {src_exc}")

            if profile_df is None:
                st.warning(
                    "Không có dữ liệu thông tin. "
                    + (" | ".join(profile_errors) if profile_errors else "")
                )
            else:
                st.dataframe(profile_df, use_container_width=True)
                try:
                    profile_df.viz.wordcloud(
                        figsize=(10, 6),
                        title=f"{symbol} - Mô tả công ty",
                        max_words=50,
                        color_palette="stock",
                    )
                    st.pyplot(plt.gcf(), clear_figure=True)
                except Exception as wc_exc:
                    st.info(f"Không vẽ được wordcloud: {wc_exc}")
        except Exception as exc:
            st.warning(f"Không thể tải thông tin {symbol}: {exc}")

    with tab2:
        try:
            company = Company(symbol=symbol, source="VCI")
            shareholders_df = company.shareholders() if hasattr(company, "shareholders") else None

            if shareholders_df is None:
                st.warning("Không có dữ liệu cổ đông.")
            else:
                if not isinstance(shareholders_df, pd.DataFrame):
                    shareholders_df = pd.DataFrame(shareholders_df)

                if shareholders_df.empty:
                    st.warning("Không có dữ liệu cổ đông.")
                else:
                    st.dataframe(shareholders_df, use_container_width=True)

                    required_cols = {"share_holder", "share_own_percent"}
                    if required_cols.issubset(set(shareholders_df.columns)):
                        pie_df = shareholders_df[["share_holder", "share_own_percent"]].copy()
                        pie_df["share_own_percent"] = pd.to_numeric(
                            pie_df["share_own_percent"], errors="coerce"
                        )
                        pie_df = pie_df.dropna(subset=["share_holder", "share_own_percent"])
                        pie_df = pie_df[pie_df["share_own_percent"] > 0]

                        if pie_df.empty:
                            st.info("Không có dữ liệu tỷ lệ cổ đông hợp lệ để vẽ biểu đồ tròn.")
                        else:
                            try:
                                pie_df.viz.pie(
                                    title=f"Cổ đông lớn {symbol}",
                                    labels="share_holder",
                                    values="share_own_percent",
                                    figsize=(10, 6),
                                    ylabel="",
                                    color_palette="stock",
                                )
                                st.pyplot(plt.gcf(), clear_figure=True)
                            except Exception:
                                fig, ax = plt.subplots(figsize=(10, 6))
                                ax.pie(
                                    pie_df["share_own_percent"],
                                    labels=pie_df["share_holder"],
                                    autopct="%1.1f%%",
                                    startangle=90,
                                )
                                ax.set_title(f"Cổ đông lớn {symbol}")
                                ax.axis("equal")
                                st.pyplot(fig, clear_figure=True)
                    else:
                        st.info("Thiếu cột share_holder/share_own_percent để vẽ biểu đồ tròn.")
        except Exception as exc:
            st.warning(f"Không thể tải dữ liệu cổ đông {symbol}: {exc}")

    with tab3:
        try:
            company = Company(symbol=symbol, source="VCI")
            data = company.officers() if hasattr(company, "officers") else None
            st.dataframe(data, use_container_width=True) if data is not None else st.warning("Không có dữ liệu ban lãnh đạo.")
        except Exception as exc:
            st.warning(f"Không thể tải dữ liệu ban lãnh đạo {symbol}: {exc}")

    with tab4:
        try:
            company = Company(symbol=symbol, source="KBS")
            data = company.affiliate() if hasattr(company, "affiliate") else None
            st.dataframe(data, use_container_width=True) if data is not None else st.warning("Không có dữ liệu công ty liên kết.")
        except Exception as exc:
            st.warning(f"Không thể tải dữ liệu công ty liên kết {symbol}: {exc}")

    with tab5:
        try:
            company = Company(symbol=symbol, source="VCI")
            data = company.news() if hasattr(company, "news") else None
            st.dataframe(data, use_container_width=True) if data is not None else st.warning("Không có dữ liệu tin tức.")
        except Exception as exc:
            st.warning(f"Không thể tải dữ liệu tin tức {symbol}: {exc}")

    with tab6:
        try:
            company = Company(symbol=symbol, source="VCI")
            data = company.events() if hasattr(company, "events") else None
            st.dataframe(data, use_container_width=True) if data is not None else st.warning("Không có dữ liệu sự kiện.")
        except Exception as exc:
            st.warning(f"Không thể tải dữ liệu sự kiện {symbol}: {exc}")

    with tab7:
        try:
            q = Quote(symbol=symbol, source="VCI")
            tab_start_ts = pd.to_datetime(start_date).normalize() + pd.Timedelta(hours=9)
            tab_end_ts = pd.to_datetime(end_date).normalize() + pd.Timedelta(hours=15, minutes=30)
            data = q.history(
                start=tab_start_ts.strftime("%Y-%m-%d %H:%M:%S"),
                end=tab_end_ts.strftime("%Y-%m-%d %H:%M:%S"),
                interval="1m",
            )
            st.dataframe(data, use_container_width=True)

            if data is not None and not data.empty and "time" in data.columns and "close" in data.columns:
                heatmap_df = data.copy()
                heatmap_df["time"] = pd.to_datetime(heatmap_df["time"], errors="coerce")
                heatmap_df["close"] = pd.to_numeric(heatmap_df["close"], errors="coerce")
                heatmap_df = heatmap_df.dropna(subset=["time", "close"]).sort_values("time")

                if not heatmap_df.empty:
                    heatmap_df = heatmap_df.set_index("time")
                    heatmap_df["returns"] = heatmap_df["close"].pct_change() * 100
                    heatmap_df = heatmap_df.dropna(subset=["returns"])

                    if not heatmap_df.empty:
                        return_pivot = pd.pivot_table(
                            heatmap_df,
                            index=heatmap_df.index.year,
                            columns=heatmap_df.index.month,
                            values="returns",
                            aggfunc="mean",
                        )

                        if not return_pivot.empty:
                            st.caption("Heatmap lợi nhuận trung bình theo tháng")
                            cmap = "RdYlGn"
                            return_pivot.viz.heatmap(
                                figsize=(10, 6),
                                title=f"{symbol} - Thống kê lợi nhuận trung bình theo tháng trong năm (%)",
                                annot=True,
                                cmap=cmap,
                            )
                            st.pyplot(plt.gcf(), clear_figure=True)
        except Exception as exc:
            st.warning(f"Không thể tải dữ liệu giá niêm yết {symbol}: {exc}")

    with tab8:
        try:
            chart_start_ts = pd.to_datetime(start_date).normalize() + pd.Timedelta(hours=9)
            chart_end_ts = pd.to_datetime(end_date).normalize() + pd.Timedelta(hours=15, minutes=30)
            now = pd.Timestamp.now(tz="Asia/Ho_Chi_Minh").tz_localize(None)
            chart_end_ts = min(chart_end_ts, now)

            if chart_start_ts > chart_end_ts:
                chart_end_ts = chart_start_ts

            raw = None
            intraday_df = None
            fetch_errors = []

            for src in ("VCI", "TCBS"):
                try:
                    quote = Quote(symbol=symbol, source=src)
                    candidate_raw = quote.history(
                        start=chart_start_ts.strftime("%Y-%m-%d %H:%M:%S"),
                        end=chart_end_ts.strftime("%Y-%m-%d %H:%M:%S"),
                        interval="1m",
                    )

                    if candidate_raw is None or candidate_raw.empty:
                        fetch_errors.append(f"{src}: history rỗng")
                        continue

                    raw = candidate_raw
                    try:
                        intraday_df = quote.intraday(page_size=100)
                    except Exception as intraday_exc:
                        fetch_errors.append(f"{src} intraday: {type(intraday_exc).__name__}: {intraday_exc}")
                        intraday_df = None
                    break
                except Exception as history_exc:
                    fetch_errors.append(f"{src} history: {type(history_exc).__name__}: {history_exc}")

            if raw is None:
                st.warning(
                    f"Không thể tải dữ liệu chart {symbol} từ nguồn VCI/TCBS. "
                    + (" | ".join(fetch_errors) if fetch_errors else "")
                )

            left_tab8, right_tab8 = st.columns([7, 3], gap="small")

            with left_tab8:
                if raw is None or raw.empty:
                    st.info(f"Không có dữ liệu chart cho {symbol}.")
                else:
                    chart_df = raw[["time", "open", "close"]].copy()
                    chart_df["time"] = pd.to_datetime(chart_df["time"], errors="coerce")
                    chart_df["open"] = pd.to_numeric(chart_df["open"], errors="coerce")
                    chart_df["close"] = pd.to_numeric(chart_df["close"], errors="coerce")
                    chart_df = chart_df.dropna(subset=["time", "open", "close"]).sort_values("time")

                    if chart_df.empty:
                        st.info(f"Không có dữ liệu chart hợp lệ cho {symbol}.")
                    else:
                        first_bar = chart_df[chart_df["time"] >= chart_start_ts].head(1)
                        ref_price = float(first_bar.iloc[0]["open"]) if not first_bar.empty else float(chart_df.iloc[0]["open"])

                        if elements is None or mui is None or html is None:
                            st.warning("Chưa cài `streamlit-elements`. Chạy: pip install streamlit-elements")
                        else:
                            points_df = chart_df[["time", "close"]].reset_index(drop=True)
                            chart_width = 900
                            chart_height = 320
                            padding = 24

                            min_close = float(points_df["close"].min())
                            max_close = float(points_df["close"].max())
                            if max_close == min_close:
                                max_close += 1.0
                                min_close -= 1.0

                            x_span = chart_width - (2 * padding)
                            y_span = chart_height - (2 * padding)
                            count = max(len(points_df) - 1, 1)

                            x_coords = [padding + (idx / count) * x_span for idx in range(len(points_df))]
                            y_coords = [
                                padding + (max_close - float(price)) / (max_close - min_close) * y_span
                                for price in points_df["close"]
                            ]
                            ref_y = padding + (max_close - ref_price) / (max_close - min_close) * y_span

                            with elements(f"tab8_chart_{symbol}"):
                                with mui.Box(
                                    sx={
                                        "height": 420,
                                        "border": "1px solid #e2e8f0",
                                        "borderRadius": "8px",
                                        "px": 1.5,
                                        "pt": 1.2,
                                        "pb": 1.0,
                                        "backgroundColor": "#ffffff",
                                    }
                                ):
                                    mui.Typography(symbol, variant="subtitle1", sx={"fontWeight": 700, "mb": 1})
                                    html.svg(
                                        *[
                                            html.line(
                                                x1=f"{x_coords[i - 1]:.2f}",
                                                y1=f"{y_coords[i - 1]:.2f}",
                                                x2=f"{x_coords[i]:.2f}",
                                                y2=f"{y_coords[i]:.2f}",
                                                stroke="#16a34a" if float(points_df.iloc[i]["close"]) >= ref_price else "#dc2626",
                                                strokeWidth="2",
                                            )
                                            for i in range(1, len(points_df))
                                        ],
                                        html.line(
                                            x1=f"{padding}",
                                            y1=f"{ref_y:.2f}",
                                            x2=f"{chart_width - padding}",
                                            y2=f"{ref_y:.2f}",
                                            stroke="#64748b",
                                            strokeWidth="1.5",
                                            strokeDasharray="6 4",
                                        ),
                                        viewBox=f"0 0 {chart_width} {chart_height}",
                                        style={
                                            "width": "100%",
                                            "height": "320px",
                                            "display": "block",
                                            "background": "#f8fafc",
                                            "borderRadius": "6px",
                                        },
                                    )
                                    html.div(
                                        f"Tham chiếu: {ref_price:,.2f} | Min: {min_close:,.2f} | Max: {max_close:,.2f}",
                                        style={"fontSize": "12px", "color": "#334155", "marginTop": "6px"},
                                    )

            with right_tab8:
                st.caption("Khối lượng giao dịch")
                if intraday_df is None or intraday_df.empty:
                    st.info("Không có dữ liệu intraday.")
                else:
                    st.dataframe(intraday_df, use_container_width=True, height=420)

        except Exception as exc:
            st.warning(f"Không thể tải dữ liệu chart {symbol}: {exc}")


@st.cache_data(ttl=300)
def load_index_history(label: str, start_dt, end_dt):
    quote_symbol_local = INDEX_TO_QUOTE.get(label, label)

    chart_start_ts = pd.to_datetime(start_dt).normalize() + pd.Timedelta(hours=9)
    chart_end_ts = pd.to_datetime(end_dt).normalize() + pd.Timedelta(hours=15, minutes=30)
    now = pd.Timestamp.now(tz="Asia/Ho_Chi_Minh").tz_localize(None)
    chart_end_ts = min(chart_end_ts, now)

    if chart_start_ts > chart_end_ts:
        chart_end_ts = chart_start_ts

    raw = None
    fetch_errors = []
    # KBS phù hợp môi trường cloud (VCI có thể bị chặn IP).
    for src in ("KBS", "VCI"):
        try:
            quote = Quote(symbol=quote_symbol_local, source=src)
            raw = quote.history(
                start=chart_start_ts.strftime("%Y-%m-%d %H:%M:%S"),
                end=chart_end_ts.strftime("%Y-%m-%d %H:%M:%S"),
                interval="1m",
            )
            if raw is None or raw.empty:
                raw = quote.history(
                    start=chart_start_ts.strftime("%Y-%m-%d %H:%M:%S"),
                    end=chart_end_ts.strftime("%Y-%m-%d %H:%M:%S"),
                    interval="1D",
                )
            if raw is None or raw.empty:
                fetch_errors.append(f"{src}: history rỗng")
                raw = None
                continue
            break
        except Exception as exc:
            fetch_errors.append(f"{src} history: {type(exc).__name__}: {exc}")
            raw = None

    if raw is None or raw.empty:
        if fetch_errors:
            raise RuntimeError(" | ".join(fetch_errors))
        return pd.DataFrame(), chart_start_ts, chart_end_ts, 0.0

    data = raw[["time", "open", "high", "low", "close", "volume"]].copy()
    data["time"] = pd.to_datetime(data["time"], errors="coerce")
    data = data.dropna(subset=["time"]).sort_values("time")

    for col in ["open", "high", "low", "close", "volume"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    first_bar = data[data["time"] >= chart_start_ts].head(1)
    if not first_bar.empty:
        ref_price = float(first_bar.iloc[0]["open"])
    else:
        ref_price = float(data.iloc[0]["open"])

    return data, chart_start_ts, chart_end_ts, ref_price

def build_index_dropdown_chart(default_label: str, index_data: dict):
    fig = go.Figure()
    shapes_by_index = {}
    annotations_by_index = {}
    visibility_by_index = {}

    for idx, label in enumerate(index_options):
        df_left, ref_left = index_data.get(label, (pd.DataFrame(), 0.0))

        if df_left.empty:
            x_vals = []
            y_green = []
            y_red = []
            ref_val = 0.0
        else:
            ref_val = ref_left
            close_series = df_left["close"]
            y_green = close_series.where(close_series >= ref_val)
            y_red = close_series.where(close_series < ref_val)
            x_vals = df_left["time"]

        show_legend = idx == 0
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_green,
                mode="lines",
                name="",
                line=dict(color="#16a34a", width=2),
                connectgaps=False,
                showlegend=show_legend,
                visible=label == default_label,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_red,
                mode="lines",
                name="",
                line=dict(color="#dc2626", width=2),
                connectgaps=False,
                showlegend=show_legend,
                visible=label == default_label,
            )
        )

        shapes_by_index[label] = [
            {
                "type": "line",
                "x0": 0,
                "x1": 1,
                "xref": "paper",
                "y0": ref_val,
                "y1": ref_val,
                "line": {"color": "#64748b", "width": 1.5, "dash": "dash"},
            }
        ]
        annotations_by_index[label] = [
            {
                "text": f"",
                "xref": "paper",
                "x": 1,
                "xanchor": "right",
                "y": ref_val,
                "yanchor": "bottom",
                "showarrow": False,
                "font": {"size": 12, "color": "#475569"},
                "bgcolor": "rgba(255,255,255,0.6)",
            }
        ]

        visible = [False] * (2 * len(index_options))
        visible[idx * 2] = True
        visible[idx * 2 + 1] = True
        visibility_by_index[label] = visible

    buttons = []
    for label in index_options:
        buttons.append(
            {
                "label": label,
                "method": "update",
                "args": [
                    {"visible": visibility_by_index[label]},
                    {
                        "shapes": shapes_by_index[label],
                        "annotations": annotations_by_index[label],
                    },
                ],
            }
        )

    fig.update_layout(
        xaxis_title="",
        xaxis_showticklabels=False,
        yaxis_title="Giá",
        template="plotly_white",
        height=250,
        updatemenus=[
            {
                "buttons": buttons,
                "direction": "down",
                "showactive": True,
                "x": 0,
                "y": 1.5,
                "xanchor": "left",
                "yanchor": "top",
                "font": {"size": 9},
                "pad": {"r": 0, "t": 10, "l": -35, "b": 0},


            }
        ],
        shapes=shapes_by_index[default_label],
        annotations=annotations_by_index[default_label],
        margin={"t": 80},
    )
    return fig


def render_main_charts() -> None:
    # --- Main chart data for selected index (used by AI context) ---
    try:
        df_main, chart_start_ts, chart_end_ts, ref_price_9h = load_index_history(
            selected_label, start_date, end_date
        )
    except Exception as exc:
        st.error(f"Không thể tải dữ liệu chart {selected_label} (symbol={quote_symbol}): {exc}")
        st.session_state["main_chart_df"] = pd.DataFrame()
        return

    if df_main.empty:
        st.warning(f"Không có dữ liệu chart cho {selected_label} (symbol={quote_symbol})")
        st.session_state["main_chart_df"] = pd.DataFrame()
        return

    index_data = {}
    for label in index_options:
        try:
            if label == selected_label:
                index_data[label] = (df_main, ref_price_9h)
            else:
                df_tmp, _, _, ref_tmp = load_index_history(label, start_date, end_date)
                index_data[label] = (df_tmp, ref_tmp)
        except Exception as exc:
            st.error(f"Không thể tải dữ liệu chart {label}: {exc}")
            return

    st.session_state["main_chart_df"] = df_main
    st.session_state["main_chart_label"] = selected_label
    st.session_state["main_chart_symbol"] = quote_symbol
    st.session_state["main_chart_start"] = start_date
    st.session_state["main_chart_end"] = end_date

    chart1, chart2, chart3, chart4,chart5 = st.columns([5, 5, 5, 5,8], gap="small")
    with chart1:
        st.plotly_chart(
            build_index_dropdown_chart(selected_label, index_data),
            use_container_width=True,
            key="chart_1",
        )
    with chart2:
        st.plotly_chart(
            build_index_dropdown_chart(selected_label, index_data),
            use_container_width=True,
            key="chart_2",
        )
    with chart3:
        st.plotly_chart(
            build_index_dropdown_chart(selected_label, index_data),
            use_container_width=True,
            key="chart_3",
        )
    with chart4:
        st.plotly_chart(
            build_index_dropdown_chart(selected_label, index_data),
            use_container_width=True,
            key="chart_4",
        )
    with chart5:
        column1,column2,column3 = st.columns([1,1,1])
        with column1:
            st.write("Chỉ số")
            st.write("VN-Index")
            st.write("VN30")
            st.write("HNX30")
            st.write("VN100")
            st.write("UPCOM")   
        with column2:
            st.write("Điểm")
            st.write(f"{df_main['close'].iloc[-1]:,.2f}")
            st.write(f"{index_data['VN30'][0]['close'].iloc[-1]:,.2f}")
            st.write(f"{index_data['HNX30'][0]['close'].iloc[-1]:,.2f}")
            st.write(f"{index_data['VN100'][0]['close'].iloc[-1]:,.2f}")
            st.write(f"{index_data['UPCOM'][0]['close'].iloc[-1]:,.2f}")
        with column3:
            st.write("Biến động %")
            st.write(f"{((df_main['close'].iloc[-1] - ref_price_9h) / ref_price_9h * 100):+.2f}%")
            st.write(f"{((index_data['VN30'][0]['close'].iloc[-1] - index_data['VN30'][1]) / index_data['VN30'][1] * 100):+.2f}%")
            st.write(f"{((index_data['HNX30'][0]['close'].iloc[-    1] - index_data['HNX30'][1]) / index_data['HNX30'][1] * 100):+.2f}%")
            st.write(f"{((index_data['VN100'][0]['close'].iloc[-1] - index_data['VN100'][1]) / index_data['VN100'][1] * 100):+.2f}%")
            st.write(f"{((index_data['UPCOM'][0]['close'].iloc[-1] - index_data['UPCOM'][1]) / index_data['UPCOM'][1] * 100):+.2f}%")


if hasattr(st, "fragment"):
    @st.fragment(run_every=REFRESH_MAIN_CHART_SECONDS)
    def _main_chart_fragment() -> None:
        render_main_charts()

    _main_chart_fragment()
else:
    st.info("Phiên bản Streamlit hiện tại không hỗ trợ fragment, nên chart sẽ không tự refresh.")
    render_main_charts()


api_key = get_gemini_api_key()
with st.popover("💬", help="Trợ lí AI", use_container_width=False):
    st.markdown("### Trợ lí AI")
    user_question = st.text_area(
        "Nhập câu hỏi",
        value="",
        height=100,
        key="ai_user_question",
    )

    if st.button("Gửi", use_container_width=True, key="ai_submit_btn"):
        if GeminiAI is None:
            st.error("Không import được gemini_ai trong môi trường chạy Streamlit.")
        elif not api_key:
            st.error("Thiếu GEMINI_API_KEY. Hãy đặt trong biến môi trường hoặc st.secrets.")
        elif not user_question.strip():
            st.warning("Vui lòng nhập nội dung câu hỏi.")
        else:
            try:
                client = get_gemini_client(api_key)
                df_main = st.session_state.get("main_chart_df", pd.DataFrame())
                if df_main is None or df_main.empty:
                    st.warning("Chưa có dữ liệu chart để phân tích.")
                    st.stop()
                context = build_ai_context(df_main, selected_label, quote_symbol, start_date, end_date)
                prompt = (
                    "Bạn là trợ lí phân tích chứng khoán Việt Nam. "
                    "Trả lời ngắn gọn theo mục: Xu hướng, Mốc quan trọng, Rủi ro, Gợi ý hành động.\\n\\n"
                    f"Du lieu thi truong:\\n{context}\\n"
                    f"Yeu cau nguoi dung: {user_question.strip()}"
                )
                with st.spinner("Đang phân tích..."):
                    response = client.model.generate_content(prompt)
                st.session_state["ai_answer_text"] = getattr(response, "text", "").strip() or "AI không trả về nội dung."
            except Exception as exc:
                err_text = str(exc)
                if "reported as leaked" in err_text or "403" in err_text:
                    st.error(
                        "Gemini API key đã bị thu hồi hoặc không hợp lệ (403). "
                        "Hãy tạo key mới và cập nhật GEMINI_API_KEY trong st.secrets hoặc biến môi trường."
                    )
                else:
                    st.error(f"Lỗi gọi Gemini: {exc}")

    if st.session_state.get("ai_answer_text"):
        st.markdown("#### Kết quả AI")
        st.markdown(st.session_state["ai_answer_text"])


### Danh sách công ty trong rổ ###
@st.cache_data(ttl=3600)
def get_group_symbols(group_name: str):
    return Listing(source="VCI").symbols_by_group(group_name)

@st.cache_data(ttl=3600)
def get_industry_options() -> list[str]:
    """Best-effort fetch of industry names from vnstock Listing."""
    try:
        listing = Listing(source="VCI")
        if hasattr(listing, "industries"):
            data = listing.industries()
        elif hasattr(listing, "industry_classification"):
            data = listing.industry_classification()
        elif hasattr(listing, "icb"):
            data = listing.icb()
        else:
            return []

        if isinstance(data, pd.Series):
            values = data.dropna().astype(str).tolist()
        elif isinstance(data, pd.DataFrame):
            name_cols = [
                "icb_name2",
                "industry_name",
                "icb_name3",
                "icb_name",
                "name",
                "industry",
                "sector",
            ]
            pick_col = next((c for c in name_cols if c in data.columns), None)
            if pick_col is None and len(data.columns) == 1:
                pick_col = data.columns[0]
            if pick_col is None:
                return []
            values = data[pick_col].dropna().astype(str).tolist()
        elif isinstance(data, (list, tuple, set)):
            values = [str(v) for v in data if str(v).strip()]
        else:
            return []

        return sorted({v.strip() for v in values if v.strip()})
    except Exception:
        return []
@st.cache_data(ttl=3600)
def get_exchange_symbols(exchange_name: str):
    return Listing(source="VCI").symbols_by_exchange(exchange=exchange_name)

def render_basket_list(target_group_symbol: str, table_key: str) -> None:
    st.subheader(f"Danh sách công ty trong rổ: {target_group_symbol}")

    def _normalize_symbol_col(df: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(df, pd.DataFrame):
            return pd.DataFrame(df)
        if "symbol" in df.columns:
            return df
        for alt in ("code", "ticker", "symbol_code", "stock_code"):
            if alt in df.columns:
                return df.rename(columns={alt: "symbol"})
        return df

    symbol_options = get_hose_symbols()
    if symbol_options:
        search_q = st.text_input(
            "Tìm mã",
            key=f"fav_search_{table_key}",
            label_visibility="collapsed",
            placeholder="Nhập để tìm mã..."
        )
        if search_q:
            q = search_q.strip().upper()
            filtered = [s for s in symbol_options if q in s.upper()]

            # Ưu tiên: bắt đầu bằng q -> sau đó theo alphabet
            filtered.sort(key=lambda s: (not s.upper().startswith(q), s))
        else:
            filtered = symbol_options


    else:
        selected_fav_symbol = st.text_input(
            "Nhập mã cổ phiếu",
            key=f"fav_symbol_input_{table_key}",
            label_visibility="collapsed",
        )

    try:
        if target_group_symbol in ("VNINDEX", "HOSE"):
            basket_df = get_exchange_symbols("HOSE")
        elif target_group_symbol in GROUP_ELIGIBLE:
            basket_df = get_group_symbols(target_group_symbol)
        else:
            basket_df = pd.DataFrame()

        if isinstance(basket_df, pd.Series):
            basket_df = basket_df.to_frame(name="symbol").reset_index(drop=True)
        elif not isinstance(basket_df, pd.DataFrame):
            basket_df = pd.DataFrame(basket_df)
        basket_df = _normalize_symbol_col(basket_df)

        board = None
        symbols_for_board = []
        if isinstance(basket_df, pd.DataFrame) and "symbol" in basket_df.columns:
            symbols_for_board = (
                basket_df["symbol"].dropna().astype(str).str.strip().tolist()
            )
            symbols_for_board = [s for s in symbols_for_board if s]

        if symbols_for_board:
            trading = Trading(source="KBS")
            board = trading.price_board(symbols_list=symbols_for_board)

        if (
            isinstance(board, pd.DataFrame)
            and isinstance(basket_df, pd.DataFrame)
            and "symbol" in basket_df.columns
            and not basket_df.empty
        ):
            board_df = _normalize_symbol_col(board.copy())
            if "symbol" not in board_df.columns:
                board_df = board_df.reset_index().rename(columns={"index": "symbol"})

            board_cols_priority = [
                "symbol",
                "exchange",
                "reference_price",
                "price_change",
                "percent_change",
                "match_price",
                "match_volume",
                "total_volume",
                "total_value",
                "bid_price_1",
                "bid_vol_1",
                "bid_price_2",
                "bid_vol_2",
                "bid_price_3",
                "bid_vol_3",
                "ask_price_1",
                "ask_vol_1",
                "ask_price_2",
                "ask_vol_2",
                "ask_price_3",
                "ask_vol_3",
                "foreign_buy_volume",
                "foreign_sell_volume",
            ]
            board_cols = [c for c in board_cols_priority if c in board_df.columns]
            if len(board_cols) > 1:
                basket_df = basket_df.merge(
                    board_df[board_cols],
                    on="symbol",
                    how="left",
                )
    except Exception as exc:
        st.warning(f"Không lấy được list cho {target_group_symbol}: {exc}")
        basket_df = pd.DataFrame()

    if basket_df.empty:
        st.info(f"Không có danh sách thành phần cho {target_group_symbol}")
        return

    preferred_cols = [
        "symbol",
        "exchange",
        "reference_price",
        "price_change",
        "percent_change",
        "match_price",
        "match_volume",
        "total_volume",
        "total_value",
        "bid_price_1",
        "bid_vol_1",
        "bid_price_2",
        "bid_vol_2",
        "bid_price_3",
        "bid_vol_3",
        "ask_price_1",
        "ask_vol_1",
        "ask_price_2",
        "ask_vol_2",
        "ask_price_3",
        "ask_vol_3",
        "foreign_buy_volume",
        "foreign_sell_volume",
        "organ_name"
    ]
    show_cols = [c for c in preferred_cols if c in basket_df.columns]
    if not show_cols:
        show_cols = basket_df.columns.tolist()

    show_df = basket_df[show_cols].drop_duplicates()
    if "symbol" in show_df.columns:
        show_df = show_df.sort_values("symbol").reset_index(drop=True)

    col_name_map = {
        "exchange": "Sàn",
        "reference_price": "Giá tham chiếu",
        "price_change": "Thay đổi",
        "percent_change": "% Thay đổi",
        "match_price": "Giá khớp",
        "match_volume": "KL khớp",
        "total_volume": "Tổng KL",
        "total_value": "Tổng GT",
        "bid_price_1": "Giá mua 1",
        "bid_vol_1": "KL mua 1",
        "bid_price_2": "Giá mua 2",
        "bid_vol_2": "KL mua 2",
        "bid_price_3": "Giá mua 3",
        "bid_vol_3": "KL mua 3",
        "ask_price_1": "Giá bán 1",
        "ask_vol_1": "KL bán 1",
        "ask_price_2": "Giá bán 2",
        "ask_vol_2": "KL bán 2",
        "ask_price_3": "Giá bán 3",
        "ask_vol_3": "KL bán 3",
        "foreign_buy_volume": "NN mua",
        "foreign_sell_volume": "NN bán",
        "organ_name": "Tên công ty",
        "icb_name2": "Ngành",
        "icb_name3": "Nhóm ngành",
        "symbol": "Mã",
    }
    display_df = show_df.rename(columns=col_name_map)

    event = st.dataframe(
        display_df,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row",
        key=table_key,
    )

    selected_rows = event.selection.rows if event is not None else []
    if selected_rows and "symbol" in show_df.columns:
        row_idx = selected_rows[0]
        selected_symbol = str(show_df.iloc[row_idx]["symbol"])
        show_company_popup(selected_symbol)


### DANH SÁCH CỔ PHIẾU ###


tabs = st.tabs(["VNIndex", "Danh sách các rổ cổ phiếu","Cổ phiếu yêu thích"])
with tabs[0]:
    render_basket_list(group_symbol, "basket_table_select_current")

with tabs[1]:
    other_group_options = ["VNINDEX"] + [g for g in GROUP_ELIGIBLE if g != "VNINDEX"]
    other_group_symbol = st.selectbox(
        "Chọn rổ khác",
        other_group_options,
        index=0,
        key="other_group_symbol_select",
        label_visibility="collapsed",
    )
    render_basket_list(other_group_symbol, "basket_table_select_other")

with tabs[2]:
    st.markdown("---")
    st.text_area(
        "fav_store_sync",
        value="",
        key="fav_store_sync",
        label_visibility="collapsed",
        height=1,
        placeholder="fav_store_sync",
    )
    symbol_options = get_hose_symbols()
    if symbol_options:
        selected_fav_symbol = st.selectbox(
            "Chọn mã cổ phiếu",
            symbol_options,
            index=0,
            key="fav_symbol_select",
            label_visibility="collapsed",
        )
    else:
        selected_fav_symbol = st.text_input(
            "Nhập mã cổ phiếu",
            key="fav_symbol_input",
            label_visibility="collapsed",
        )

    if st.button("Lưu vào yêu thích", use_container_width=True, key="fav_add_btn"):
        symbol_value = str(selected_fav_symbol).strip().upper()
        if symbol_value:
            _localstorage_add_favorite(symbol_value)
            st.toast(f"Đã lưu {symbol_value} vào yêu thích.")
            st.rerun()
        else:
            st.info("Vui lòng chọn hoặc nhập mã cổ phiếu.")

    _inject_localstorage_sync()
    favorites = _get_favorites_from_localstorage()
    if not favorites:
        st.info("Chưa có mã nào trong danh sách yêu thích.")
    else:
        fav_df = pd.DataFrame(
            {
                "Xem": [False] * len(favorites),
                "symbol": favorites,
            }
        )
        edited_fav_df = st.data_editor(
            fav_df,
            use_container_width=True,
            hide_index=True,
            key="fav_table_editor",
            column_config={
                "Xem": st.column_config.CheckboxColumn("Thông tin chi tiết", width="small"),
                "symbol": st.column_config.TextColumn("Mã cổ phiếu", disabled=True),
            },
        )

        selected_symbols = (
            edited_fav_df.loc[edited_fav_df["Xem"] == True, "symbol"].tolist()
            if isinstance(edited_fav_df, pd.DataFrame) and "Xem" in edited_fav_df.columns
            else []
        )
        if selected_symbols:
            show_company_popup(selected_symbols[0])

        remove_symbols = st.multiselect(
            "Chọn mã để xóa khỏi yêu thích",
            favorites,
            key="fav_remove_select",
        )
        if st.button("Xóa mã đã chọn", use_container_width=True, key="fav_remove_btn"):
            if remove_symbols:
                _localstorage_remove_favorites(remove_symbols)
                st.toast("Đã xóa mã đã chọn.")
                st.rerun()
            else:
                st.info("Vui lòng chọn ít nhất một mã để xóa.")

if st.button("Đăng xuất"):
            st.session_state.pop("user", None)
            st.switch_page("C:\\Users\\kenda\\Desktop\\New folder (2)\\Greatfut.py")

