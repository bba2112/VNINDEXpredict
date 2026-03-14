import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import matplotlib.pyplot as plt
from constants import index_options
import html as html_std

from vnstock import Company, Listing, Quote
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

st.set_page_config(page_title="Dữ liệu - Greatfut iBoard", layout="wide")

# Auto-refresh page to pick up ticker file changes.
st.components.v1.html(
    "<script>setTimeout(() => window.location.reload(), 3600000);</script>",
    height=0,
)

# Placeholder ticker text (used if no file-driven content yet)
_ticker_default = (
    "Tin nhanh: VNINDEX biến động mạnh trong phiên | VN30 giữ nhịp | "
    "Thanh khoản cải thiện | Cập nhật từ nguồn API sẽ thay thế nội dung này"
)

TICKER_FILE = os.path.join(os.path.dirname(__file__), "ticker_text.txt")

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
ticker_text_html = html_std.escape(ticker_text)

import base64

def _img_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")

logo_b64 = _img_to_base64("C:\\Users\\kenda\\Desktop\\New folder (2)\\image\\Gemini_Generated_Image_uvz9l1uvz9l1uvz9.png")

st.components.v1.html(
    f"""
    <style>
    .topbar {{
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 4px 6px;
        border-radius: 10px;
        # background: #f8fafc;
        # color: #0f172a;
    }}
    .topbar__logo {{
        width: 60px;
        height: 60px;
        object-fit: contain;
        border-radius: 8px;
    }}
    .topbar__controls {{
        display: flex;
        gap: 6px;
    }}
    .topbar__btn {{
        padding-left: 5px;
        border: 1px solid #cbd5f5;
        # background: #ffffff;
        # color: #0f172a;
        border-radius: 999px;
        padding: 10px 10px;
        font-size: 12px;
        font-weight: 700;
        cursor: pointer;
        transition: transform 2000ms ease, box-shadow 2000ms ease, filter 2000ms ease;
    }}
    .news-ticker {{
        flex: 1;
        overflow: hidden;
        white-space: nowrap;
        padding: 8px 12px;
        color: #f8fafc;
        font-weight: 800;
        letter-spacing: 0.2px;
        border-radius: 10px;
        background: #0f172a;
    }}
    .news-ticker__track {{
        display: inline-block;
        padding-left: 100%;
        animation: news-ticker-scroll 20s linear infinite;
    }}
    @keyframes news-ticker-scroll {{
        0% {{ transform: translateX(0); }}
        100% {{ transform: translateX(-100%); }}
    }}
    .topbar__clock {{
        min-width: 96px;
        font-weight: 800;
        letter-spacing: 0.5px;
    }}
    .news-ticker__track[data-lang="en"] {{
        display: none;
    }}
    /* Topbar theme */
    .topbar.theme-dark {{
        background: #4F4F4F;
        # color: #f8fafc;
        
    }}
    .topbar.theme-dark .topbar__btn {{
        background: #0b1220;
        color: #f8fafc;
        border-color: #1e293b;
    }}
    .topbar.theme-dark .news-ticker {{
        # background: #111827;
        color: #e2e8f0;
    }}

    /* Global theme */
    body.theme-dark {{
        background: #0b1220 !important;
        color: #e5e7eb !important;
    }}
    body.theme-dark .stApp {{
        background: #0b1220 !important;
        color: #e5e7eb !important;
    }}
    body.theme-dark h1,
    body.theme-dark h2,
    body.theme-dark h3,
    body.theme-dark h4,
    body.theme-dark h5,
    body.theme-dark h6,
    body.theme-dark p,
    body.theme-dark span,
    body.theme-dark label,
    body.theme-dark div {{
        color: #e5e7eb !important;
    }}
    body.theme-light {{
        background: #ffffff !important;
        color: #0f172a !important;
    }}
    body.theme-light .stApp {{
        background: #ffffff !important;
        color: #0f172a !important;
    }}
    </style>

    <div class="topbar">
        <img class="topbar__logo" src="data:image/png;base64,{logo_b64}" alt="logo" />
        <div class="topbar__clock" id="topbar-clock">--:--:--</div>
        <div class="topbar__controls">
            <button class="topbar__btn" id="toggle-theme">Light</button>
            <button class="topbar__btn" id="toggle-lang">VI</button>
        </div>
        <div class="news-ticker">
            <span class="news-ticker__track" data-lang="vi">{ticker_text_html}</span>
            <span class="news-ticker__track" data-lang="en">
                Breaking: VNINDEX volatile | VN30 steady | Liquidity improving | API feed will replace this
            </span>
        </div>
    </div>

    <script>
    (function() {{
        const clockEl = document.getElementById("topbar-clock");
        const topbar = document.querySelector(".topbar");
        const themeBtn = document.getElementById("toggle-theme");
        const langBtn = document.getElementById("toggle-lang");
        const trackVi = document.querySelector('.news-ticker__track[data-lang="vi"]');
        const trackEn = document.querySelector('.news-ticker__track[data-lang="en"]');
        function pad(n) {{ return String(n).padStart(2, "0"); }}
        function tick() {{
            const now = new Date();
            const fmt = new Intl.DateTimeFormat("en-GB", {{
                timeZone: "Asia/Ho_Chi_Minh",
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
                hour12: false
            }});
            clockEl.textContent = fmt.format(now);
        }}
        tick();
        setInterval(tick, 1000);

        function applyTheme(isDark) {{
            topbar.classList.toggle("theme-dark", isDark);
            document.body.classList.toggle("theme-dark", isDark);
            document.body.classList.toggle("theme-light", !isDark);
            themeBtn.textContent = isDark ? "Dark" : "Light";
        }}
        // Initialize as light theme by default
        applyTheme(false);

        themeBtn.addEventListener("click", () => {{
            const isDark = !document.body.classList.contains("theme-dark");
            applyTheme(isDark);
        }});
        langBtn.addEventListener("click", () => {{
            const viOn = trackVi.style.display !== "none";
            trackVi.style.display = viOn ? "none" : "inline-block";
            trackEn.style.display = viOn ? "inline-block" : "none";
            langBtn.textContent = viOn ? "EN" : "VI";
        }});
    }})();
    </script>
    """,
    height=80,
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

a1, a2, a3 = st.columns(3)
with a1:
    _nav_button("Giá vàng", "pages/GoldPrice.py")
with a2:
    _nav_button("Danh sách các quỹ", "pages/Quymo.py")
with a3:
    _nav_button("VNData", "pages/VNIndex.py")


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
            st.warning(f"Không thể tải dữ liệu chartt {symbol}: {exc}")


@st.cache_data(ttl=300)
def load_index_history(label: str, start_dt, end_dt):
    quote_symbol_local = INDEX_TO_QUOTE.get(label, label)

    chart_start_ts = pd.to_datetime(start_dt).normalize() + pd.Timedelta(hours=9)
    chart_end_ts = pd.to_datetime(end_dt).normalize() + pd.Timedelta(hours=15, minutes=30)
    now = pd.Timestamp.now(tz="Asia/Ho_Chi_Minh").tz_localize(None)
    chart_end_ts = min(chart_end_ts, now)

    if chart_start_ts > chart_end_ts:
        chart_end_ts = chart_start_ts

    quote = Quote(symbol=quote_symbol_local, source="VCI")
    raw = quote.history(
        start=chart_start_ts.strftime("%Y-%m-%d %H:%M:%S"),
        end=chart_end_ts.strftime("%Y-%m-%d %H:%M:%S"),
        interval="1m",
    )

    if raw is None or raw.empty:
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

# --- Main chart data for selected index (used by AI context) ---
try:
    df_main, chart_start_ts, chart_end_ts, ref_price_9h = load_index_history(
        selected_label, start_date, end_date
    )
except Exception as exc:
    st.error(f"Không thể tải dữ liệu chartt {selected_label} (symbol={quote_symbol}): {exc}")
    st.stop()

if df_main.empty:
    st.warning(f"Không có dữ liệu chart cho {selected_label} (symbol={quote_symbol})")
    st.stop()

index_data = {}
for label in index_options:
    try:
        if label == selected_label:
            index_data[label] = (df_main, ref_price_9h)
        else:
            df_tmp, _, _, ref_tmp = load_index_history(label, start_date, end_date)
            index_data[label] = (df_tmp, ref_tmp)
    except Exception as exc:
        st.error(f"Không thể tải dữ liệu chartt {label}: {exc}")
        st.stop()


def build_index_dropdown_chart(default_label: str):
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
        height=560,
        updatemenus=[
            {
                "buttons": buttons,
                "direction": "down",
                "showactive": True,
                "x": 0,
                "y": 1.12,
                "xanchor": "left",
                "yanchor": "top",
            }
        ],
        shapes=shapes_by_index[default_label],
        annotations=annotations_by_index[default_label],
        margin={"t": 80},
    )
    return fig


chart1, chart2, chart3, chart4 = st.columns([5, 5, 5, 5], gap="small")
with chart1:
    st.plotly_chart(
        build_index_dropdown_chart(selected_label),
        use_container_width=True,
        key="chart_1",
    )
with chart2:
    st.plotly_chart(
        build_index_dropdown_chart(selected_label),
        use_container_width=True,
        key="chart_2",
    )
with chart3:
    st.plotly_chart(
        build_index_dropdown_chart(selected_label),
        use_container_width=True,
        key="chart_3",
    )
with chart4:
    st.plotly_chart(
        build_index_dropdown_chart(selected_label),
        use_container_width=True,
        key="chart_4",
    )


st.markdown(
    """
    <style>
    @keyframes ai-pop-in {
        from {
            opacity: 0;
            transform: translateY(10px) scale(0.92);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }
    @keyframes ai-pop-out {
        from {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
        to {
            opacity: 0;
            transform: translateY(8px) scale(0.95);
        }
    }

    div[data-testid="stPopover"] {
        position: fixed;
        right: 20px;
        bottom: 20px;
        z-index: 999;
    }

    div[data-testid="stPopover"] button {
        width: 56px;
        height: 56px;
        border-radius: 999px;
        padding: 0;
        font-size: 24px;
        border: 0;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.20);
        transition: transform 180ms ease, box-shadow 180ms ease, filter 180ms ease;
    }

    div[data-testid="stPopover"] button:hover {
        transform: translateY(-1px) scale(1.04);
        box-shadow: 0 12px 28px rgba(0, 0, 0, 0.24);
        filter: saturate(1.08);
    }

    /* Open state: apply pop-in when popover is visible */
    div[data-baseweb="popover"]:not([data-popper-reference-hidden="true"]):not([aria-hidden="true"]):not([hidden]) > div {
        transform-origin: bottom right !important;
        animation: ai-pop-in 2200ms cubic-bezier(0.2, 0.9, 0.2, 1) both;
        border-radius: 14px !important;
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.22) !important;
    }

    /* Close state: cover multiple hidden-state variants across BaseWeb/Streamlit versions */
    div[data-baseweb="popover"][data-popper-reference-hidden="true"] > div,
    div[data-baseweb="popover"][aria-hidden="true"] > div,
    div[data-baseweb="popover"][hidden] > div,
    div[data-baseweb="popover"][style*="visibility: hidden"] > div,
    div[data-baseweb="popover"][style*="opacity: 0"] > div {
        animation: ai-pop-out 2200ms cubic-bezier(0.4, 0, 1, 1) both !important;
        pointer-events: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

api_key = get_gemini_api_key()
with st.popover("💬", help="Trợ lí AI", use_container_width=False):
    st.markdown("### Trợ lí AI")
    user_question = st.text_area(
        "Nhập câu hỏi",
        value="Phân tích xu hướng ngắn hạn, vùng hỗ trợ/kháng cự, rủi ro và hành động đề xuất.",
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

st.markdown("---")
st.subheader(f"Danh sách công ty trong rổ: {group_symbol}")

@st.cache_data(ttl=3600)
def get_group_symbols(group_name: str):
    return Listing(source="VCI").symbols_by_group(group_name)

@st.cache_data(ttl=3600)
def get_exchange_symbols(exchange_name: str):
    return Listing(source="VCI").symbols_by_exchange(exchange=exchange_name)

show_df = pd.DataFrame()

try:
    # --- List uses group_symbol ---
    if group_symbol == "VNINDEX":
        basket_df = get_exchange_symbols("HOSE")
    elif group_symbol in GROUP_ELIGIBLE:
        basket_df = get_group_symbols(group_symbol)
    else:
        basket_df = pd.DataFrame()

    if isinstance(basket_df, pd.Series):
        basket_df = basket_df.to_frame(name="symbol").reset_index(drop=True)
    elif not isinstance(basket_df, pd.DataFrame):
        basket_df = pd.DataFrame(basket_df)
except Exception as exc:
    st.warning(f"Không lấy được list cho {group_symbol}: {exc}")
    basket_df = pd.DataFrame()

if basket_df.empty:
    st.info(f"Không có danh sách thành phần cho {group_symbol}")
else:
    preferred_cols = ["symbol", "organ_name", "exchange", "icb_name2", "icb_name3"]
    show_cols = [c for c in preferred_cols if c in basket_df.columns]
    if not show_cols:
        show_cols = basket_df.columns.tolist()

    show_df = basket_df[show_cols].drop_duplicates()
    if "symbol" in show_df.columns:
        show_df = show_df.sort_values("symbol").reset_index(drop=True)

    event = st.dataframe(
        show_df,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row",
        key="basket_table_select",
    )
    st.caption(f"Số mã trong list {group_symbol}: {len(show_df)}")

    selected_rows = event.selection.rows if event is not None else []
    if selected_rows and "symbol" in show_df.columns:
        row_idx = selected_rows[0]
        selected_symbol = str(show_df.iloc[row_idx]["symbol"])
        show_company_popup(selected_symbol)
