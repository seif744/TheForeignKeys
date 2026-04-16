import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import logging
logging.basicConfig(format='%(filename)s:%(lineno)s:%(levelname)s -- %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

import streamlit as st
import requests
from modules.nav import SideBarLinks, LOGO_PATH

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
    st.markdown('<div class="page-sub">Choose who you are to load your watchlist and alerts.</div>', unsafe_allow_html=True)

st.markdown("---")

# ── Fetch users ────────────────────────────────────────────────────────────
users = []
try:
    resp = requests.get('http://api:4000/u/', timeout=5)
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

if not users:
    st.warning("No active users found.")
    st.stop()

# ── Selection ──────────────────────────────────────────────────────────────
left, _, right = st.columns([3, 1, 3])

with left:
    st.markdown('<div class="card card-accent">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Account</div>', unsafe_allow_html=True)

    user_map = {f"{u['name']}  ·  {u['email']}": u for u in users}
    selected_label = st.selectbox("Active users", list(user_map.keys()), label_visibility="collapsed")
    selected_user  = user_map[selected_label]

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Continue →", type="primary", use_container_width=True):
        st.session_state['user_id']   = selected_user['user_id']
        st.session_state['user_name'] = selected_user['name']
        logger.info(f"Session user: {selected_user['name']} (id={selected_user['user_id']})")
        st.switch_page('pages/04_watchlist.py')
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    u        = selected_user
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
