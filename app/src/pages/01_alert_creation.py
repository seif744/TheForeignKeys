import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import logging
logging.basicConfig(format='%(filename)s:%(lineno)s:%(levelname)s -- %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

import streamlit as st
import requests
from modules.nav import SideBarLinks, LOGO_PATH

st.set_page_config(page_title="Add Alert | BargainHunters", page_icon="🔔", layout="wide")

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
    st.markdown('<div class="page-title" style="margin-top:0.6rem;">Create Alerts</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Choose items that you would like to recieve alerts ' \
    'about if they go on sale''</div>', unsafe_allow_html=True)

st.markdown("---")

