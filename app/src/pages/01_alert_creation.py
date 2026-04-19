import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import logging
logging.basicConfig(format='%(filename)s:%(lineno)s:%(levelname)s -- %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks, LOGO_PATH

st.set_page_config(page_title="Add Alert | BargainHunters", page_icon="🔔", layout="wide")

SideBarLinks()

if not st.session_state.get('authenticated'):
    st.switch_page('Home.py')
if st.session_state.get('role') != 'user':
    st.switch_page('Home.py')

logo_col, title_col = st.columns([1, 6])
with logo_col:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=110)
with title_col:
    st.markdown('<div class="page-title" style="margin-top:0.6rem;">Add Alert</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Watch an eBay listing, item, or category for price drops.</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div class="card" style="color:#555;">Alert creation form coming soon.</div>', unsafe_allow_html=True)
