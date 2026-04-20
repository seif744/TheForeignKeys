import os
import streamlit as st

_ASSETS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')
)
LOGO_PATH = os.path.join(_ASSETS_DIR, "logo.png")


def inject_global_css() -> None:
    st.markdown("""
    <style>
    #MainMenu, footer { visibility: hidden; }

    /* keep header in the DOM so the sidebar toggle stays clickable */
    header[data-testid="stHeader"] {
        background: #0a0a0a !important;
        border-bottom: 1px solid #1a1a1a !important;
    }

    .stApp { background: #0a0a0a; }

    /* ── typography ─────────────────────────────────────────────── */
    .page-title {
        font-size: 2rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.01em;
        margin-bottom: 0.2rem;
    }
    .page-sub {
        font-size: 0.95rem;
        color: #888;
        margin-bottom: 1.6rem;
    }

    /* ── cards ──────────────────────────────────────────────────── */
    .card {
        background: #111111;
        border: 1px solid #1e1e1e;
        border-radius: 10px;
        padding: 1.6rem 1.8rem;
        margin-bottom: 1rem;
    }
    .card-accent { border-top: 2px solid #cc2222; }

    /* ── section label ──────────────────────────────────────────── */
    .section-label {
        color: #d4621a;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }

    /* ── user chip ──────────────────────────────────────────────── */
    .user-chip {
        background: #111111;
        border: 1px solid #1e1e1e;
        border-radius: 8px;
        padding: 0.7rem 0.9rem;
        margin: 0.4rem 0 0.8rem 0;
    }
    .user-chip .label { color: #555; font-size: 0.67rem; text-transform: uppercase; letter-spacing: 0.1em; }
    .user-chip .name  { color: #f5f5f5; font-weight: 700; margin-top: 0.15rem; font-size: 0.9rem; }
    .user-chip .email { color: #d4621a; font-size: 0.76rem; margin-top: 0.1rem; }

    /* ── sidebar ────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: #080808;
        border-right: 1px solid #1a1a1a;
    }
    </style>
    """, unsafe_allow_html=True)


# ── Nav helpers ────────────────────────────────────────────────────────────

def user_select_nav() -> None:
    st.sidebar.page_link("pages/00_user_select.py", label="Switch User",     icon="👤")

def alert_creation_nav() -> None:
    st.sidebar.page_link("pages/01_alert_creation.py", label="Add Alert",    icon="🔔")

def statistics_nav() -> None:
    st.sidebar.page_link("pages/02_statistics.py",  label="Statistics",      icon="📊")

def feedback_nav() -> None:
    st.sidebar.page_link("pages/05_feedback.py",    label="Submit Feedback", icon="💬")


# ── Sidebar assembly ───────────────────────────────────────────────────────

def SideBarLinks(show_home=False) -> None:
    inject_global_css()

    if os.path.exists(LOGO_PATH):
        with st.sidebar:
            st.image(LOGO_PATH, use_container_width=True)

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.switch_page("Home.py")

    if show_home:
        st.sidebar.page_link("Home.py", label="Home", icon="🏠")

    if st.session_state.get("authenticated"):
        user_name = st.session_state.get("user_name", "")
        if user_name:
            st.sidebar.markdown(f"""
            <div class="user-chip">
                <div class="label">Signed in as</div>
                <div class="name">{user_name}</div>
            </div>
            """, unsafe_allow_html=True)

        st.sidebar.markdown("---")
        st.sidebar.markdown('<div class="section-label">Menu</div>', unsafe_allow_html=True)

        if st.session_state.get("role") == "user":
            alert_creation_nav()
            statistics_nav()
            feedback_nav()
            st.sidebar.markdown("---")
            user_select_nav()

        if st.sidebar.button("Logout", use_container_width=True):
            for key in ("role", "authenticated", "user_id", "user_name"):
                st.session_state.pop(key, None)
            st.switch_page("Home.py")
