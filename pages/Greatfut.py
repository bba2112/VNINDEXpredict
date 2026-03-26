import pyodbc
import streamlit as st



def get_conn():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=DESKTOP-S5JDT28\SQLEXPRESS;"
        "DATABASE=StockDB;"
        "TrustServerCertificate=yes;"
    )
def login_ui():
    st.subheader("Đăng nhập")
    u = st.text_input("Username")
    p = st.text_input("Mật khẩu", type="password")
    if st.button("Đăng nhập"):
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
    u = st.text_input("Username", key="reg_u")
    p = st.text_input("Mật khẩu", type="password", key="reg_p")
    c = st.text_input("Nhập lại mật khẩu", type="password", key="reg_c")
    mail = st.text_input("Email", key="reg_m")
    sdt = st.text_input("SĐT", key="reg_s")
    birth = st.date_input("Ngày sinh", key="reg_b")
    addr = st.text_input("Địa chỉ", key="reg_a")

    if st.button("Đăng ký"):
        if not u or not p:
            st.warning("Vui lòng nhập đầy đủ username và mật khẩu.")
            return
        if p != c:
            st.warning("Mật khẩu không khớp.")
            return
        try:
            register_user(u, p, mail or None, sdt or None, birth, addr or None)
            st.success("Đăng ký thành công, vui lòng đăng nhập.")
        except Exception as e:
            st.error(f"Lỗi đăng ký: {e}")

def auth_gate():
    if st.session_state.get("user"):
        st.success(f"Xin chào {st.session_state['user']}")
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
