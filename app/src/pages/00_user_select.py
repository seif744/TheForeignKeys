import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import logging
logging.basicConfig(format='%(filename)s:%(lineno)s:%(levelname)s -- %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

import streamlit as st
import requests
from modules.nav import SideBarLinks, LOGO_PATH

API_BASE = os.getenv("API_BASE", "http://api:4000")

st.set_page_config(page_title="Select User | BargainHunters", page_icon="👤", layout="wide")

SideBarLinks()

# ── Auth guard ─────────────────────────────────────────────────────────────
if not st.session_state.get('authenticated'):
    st.switch_page('Home.py')
if st.session_state.get('role') != 'user':
    st.switch_page('Home.py')

# ── Logo + title ───────────────────────────────────────────────────────────
logo_col, title_col = st.columns([1, 6])
with logo_col:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=110)
with title_col:
    st.markdown('<div class="page-title" style="margin-top:0.6rem;">Select Account</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Choose an existing account or create a new one.</div>', unsafe_allow_html=True)

st.markdown("---")

# ── Fetch existing users ───────────────────────────────────────────────────
users = []
try:
    resp = requests.get(f'{API_BASE}/u/', timeout=5)
    resp.raise_for_status()
    users = [u for u in resp.json() if u.get('is_active', True)]
    logger.info(f"Fetched {len(users)} active users")
except requests.exceptions.ConnectionError:
    st.error("Cannot reach the API server. Is the backend running?")
    st.stop()
except requests.exceptions.HTTPError as e:
    st.error(f"API error: {e}")
    st.stop()
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    st.error("Something went wrong loading users.")
    st.stop()

# ── Tabs ───────────────────────────────────────────────────────────────────
left, _, right = st.columns([3, 1, 3])

with left:
    tab_existing, tab_new = st.tabs(["Existing User", "New User"])

    # ── Tab 1: existing user ───────────────────────────────────────
    with tab_existing:
        if not users:
            st.markdown('<div class="card" style="color:#555;">No active users found.</div>', unsafe_allow_html=True)
        else:
            user_map = {f"{u['name']}  ·  {u['email']}": u for u in users}
            selected_label = st.selectbox(
                "Active users",
                list(user_map.keys()),
                label_visibility="collapsed",
                key="existing_user_select",
            )
            selected_user = user_map[selected_label]
            st.session_state['_preview_user'] = selected_user

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Continue →", type="primary", use_container_width=True, key="btn_existing"):
                st.session_state['user_id']   = selected_user['user_id']
                st.session_state['user_name'] = selected_user['name']
                logger.info(f"Session user: {selected_user['name']} (id={selected_user['user_id']})")
                st.switch_page('pages/01_alert_creation.py')

    # ── Tab 2: new user ────────────────────────────────────────────
    with tab_new:
        with st.form("new_user_form", clear_on_submit=True):
            name  = st.text_input("Full name",  placeholder="Jane Smith")
            email = st.text_input("Email",      placeholder="jane@example.com")
            submitted = st.form_submit_button("Create Account →", type="primary", use_container_width=True)

        if submitted:
            name  = name.strip()
            email = email.strip()

            if not name or not email:
                st.warning("Name and email are both required.")
            elif "@" not in email:
                st.warning("Enter a valid email address.")
            else:
                try:
                    r = requests.post(
                        f"{API_BASE}/u/",
                        json={"name": name, "email": email},
                        timeout=5,
                    )
                    if r.status_code == 201:
                        new_user = r.json()
                        st.session_state['user_id']   = new_user['user_id']
                        st.session_state['user_name'] = new_user['name']
                        logger.info(f"Created user: {new_user['name']} (id={new_user['user_id']})")
                        st.switch_page('pages/01_alert_creation.py')
                    elif r.status_code == 409:
                        st.error("An account with that email already exists. Select it from the Existing User tab.")
                    else:
                        st.error(f"Could not create account ({r.status_code}).")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot reach the API server.")
                except Exception as e:
                    logger.error(f"Error creating user: {e}")
                    st.error("Added user successfully!")

# ── Preview card (right column) ────────────────────────────────────────────
with right:
    preview = st.session_state.get('_preview_user') or (users[0] if users else None)
    if preview:
        u        = preview
        initials = "".join(p[0].upper() for p in u['name'].split()[:2])
        st.markdown(f"""
        <div class="card">
            <div class="section-label">Preview</div>
            <div style="
                display:inline-flex; align-items:center; justify-content:center;
                width:48px; height:48px; border-radius:50%;
                background:#cc2222;
                font-size:1.1rem; font-weight:800; color:#fff;
                margin: 0.5rem 0 0.9rem 0;
            ">{initials}</div>
            <div style="font-size:1.1rem; font-weight:700; color:#f5f5f5; margin-bottom:0.25rem;">{u['name']}</div>
            <div style="color:#d4621a; font-size:0.82rem; margin-bottom:0.6rem;">{u['email']}</div>
            <div style="color:#555; font-size:0.75rem;">ID &nbsp;#{u['user_id']}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="card" style="color:#555;">Select or create a user to see a preview.</div>', unsafe_allow_html=True)

# ── Feedback footer ────────────────────────────────────────────────────────
with st._bottom:
    st.page_link("pages/05_feedback.py", label="Feedback", icon='💬')
