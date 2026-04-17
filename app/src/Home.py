import logging
logging.basicConfig(format='%(filename)s:%(lineno)s:%(levelname)s -- %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

import os
import streamlit as st
from modules.nav import SideBarLinks, LOGO_PATH

st.set_page_config(page_title="BargainHunters", page_icon="🎯", layout="wide", initial_sidebar_state= "expanded")

st.session_state['authenticated'] = False
SideBarLinks(show_home=True)

logger.info("Loading Home page")

# ── Logo + title ───────────────────────────────────────────────────────────
logo_col, title_col = st.columns([1, 6])
with logo_col:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=110)
with title_col:
    st.markdown('<div class="page-title" style="margin-top:0.6rem;">BargainHunters</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Track eBay prices. Get notified when they drop.</div>', unsafe_allow_html=True)

st.markdown("---")

# ── Sign-in + feature columns ──────────────────────────────────────────────
signin_col, gap_col, info_col = st.columns([2, 1, 3])

with signin_col:
    st.markdown('<div class="card card-accent">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Sign in</div>', unsafe_allow_html=True)
    st.markdown("#### Select your account")
    st.markdown(
        "<p style='color:#888; font-size:0.88rem; margin-bottom:1.2rem;'>"
        "No password needed — pick your account on the next screen."
        "</p>",
        unsafe_allow_html=True,
    )
    if st.button("Continue as User", type="primary", use_container_width=True):
        st.session_state['authenticated'] = True
        st.session_state['role'] = 'user'
        logger.info("Entering as regular user")
        st.switch_page('pages/00_user_select.py')
    st.markdown('</div>', unsafe_allow_html=True)

with info_col:
    features = [
        ("🔔", "Price Alerts",   "Dollar or % drop thresholds on any listing, item, or category."),
        ("👁️", "Watchlist",      "One view for everything you're tracking."),
        ("📧", "Notifications",  "Email alerts the moment a condition is met."),
        ("📊", "Statistics",     "Price trends across your watched items."),
    ]
    for icon, title, desc in features:
        st.markdown(f"""
        <div style="display:flex; gap:0.9rem; align-items:flex-start; margin-bottom:1rem;">
            <div style="font-size:1.2rem; margin-top:0.1rem;">{icon}</div>
            <div>
                <div style="font-weight:700; color:#f5f5f5; font-size:0.9rem;">{title}</div>
                <div style="color:#888; font-size:0.82rem; line-height:1.5;">{desc}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
