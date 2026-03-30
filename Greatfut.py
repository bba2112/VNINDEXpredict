import pyodbc
import streamlit as st

def get_conn():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=DESKTOP-S5JDT28\\SQLEXPRESS;"
        "DATABASE=StockDB;"
        "trusted_connection=yes;"
        "TrustServerCertificate=yes;"
    )
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)


st.title("Đăng nhập")
def login_ui():
    st.subheader("Đăng nhập")
    with st.form("login_form", clear_on_submit=False):
        u = st.text_input("Tài khoản")
        p = st.text_input("Mật khẩu", type="password")
        submitted = st.form_submit_button("Đăng nhập")

    if submitted:
        if not u or not p:
            st.warning("Vui lòng nhập đúng tài khoản và mật khẩu.")
            return
        if login_user(u, p):
            st.session_state["user"] = u
            st.success("Đăng nhập thành công")
            st.rerun()
        else:
            st.error("Sai tài khoản hoặc mật khẩu")

def register_user(username, password, mail=None, sdt=None, birthdate=None, addr=None):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "EXEC dbo.sp_register_user ?, ?, ?, ?, ?, ?",
            (username, password, mail, sdt, birthdate, addr),
        )
        conn.commit()


def login_user(username, password) -> bool:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("EXEC dbo.sp_login_user ?, ?", (username, password))
        row = cur.fetchone()
        return bool(row[0]) if row else False


def register_ui():
    st.subheader("Đăng ký")
    with st.form("register_form", clear_on_submit=True):
        u = st.text_input("Tài khoản", key="reg_u")
        p = st.text_input("Mật khẩu", type="password", key="reg_p")
        c = st.text_input("Nhập lại mật khẩu", type="password", key="reg_c")
        mail = st.text_input("Email", key="reg_m")
        sdt = st.text_input("Số điện thoại", key="reg_s")
        birth = st.date_input("Ngày sinh", key="reg_b")
        addr = st.text_input("Địa chỉ", key="reg_a")
        submitted = st.form_submit_button("Đăng ký")

    if submitted:
        if not u or not p:
            st.warning("Vui lòng nhập đủ tên tài khoản hoặc mật khẩu")
            return
        while p != c:
            st.warning("Vui lòng nhập đúng hai ô mật khẩu")
            return
        specials = ["@","!","#","$","%","^","&","*","(",")"]
        digits = ["0","1","2","3","4","5","6","7","8","9"]

        has_special = any(ch in specials for ch in p)
        has_digit = any(ch in digits for ch in p)

        if len(p) < 8 or not has_special or not has_digit:
            st.warning("Mật khẩu phải dài hơn 8, có ký tự đặc biệt và có số")
            return

        if mail == "":
            st.warning("Thiếu email")
            return
        if not mail.endswith("@gmail.com"):
            st.warning ("Không đúng định dạng email, phải là đuôi @gmail.com")
            return
        if sdt == "":
            st.warning ("Thiếu số điện thoại")
            return
        if not sdt.isdigit():
            st.warning ("Không đúng định dạng số điện thoại")
            return
        if len(sdt) not in [10]:
            st.warning ("Số điện thoại phải 10 số")
            return
        while birth == "":
            st.warning("Thiếu ngày sinh")
            return
        while addr == "":
            st.warning("Thiếu địa chỉ")
            return
        try:
            register_user(u, p, mail, sdt, birth, addr)
            st.success("Đăng ký thành công, vui lòng đăng nhập.")
            
        except Exception as e:
            raw = str(e)
            part = raw.split(']')[-1]
            msg = part.split('(')[0].strip()
            st.error(msg)


def auth_gate():
    if st.session_state.get("user"):
        st.success(f"Xin chào {st.session_state['user']}")
        st.switch_page("pages/dashboard.py")
        if st.button("Đăng xuất"):
            st.session_state.pop("user", None)
            st.rerun()
        return True
    else:
        tab1, tab2 = st.tabs(["Đăng nhập", "Đăng ký"])
        with tab1:
            login_ui()
        with tab2:
            register_ui()
        return False


auth_gate()

