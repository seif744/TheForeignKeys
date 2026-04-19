import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import logging
logging.basicConfig(format='%(filename)s:%(lineno)s:%(levelname)s -- %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

import streamlit as st
<<<<<<< HEAD
from modules.nav import SideBarLinks, LOGO_PATH

st.set_page_config(page_title="Statistics | BargainHunters", page_icon="📊", layout="wide")

SideBarLinks()

=======
import requests
from modules.nav import SideBarLinks, LOGO_PATH

st.set_page_config(page_title="Select User | BargainHunters", page_icon="👤", layout="wide")

SideBarLinks()

# ── Auth guard ─────────────────────────────────────────────────────────────
>>>>>>> 6dd349b20300b66223676a4913ac3d277f63a671
if not st.session_state.get('authenticated'):
    st.switch_page('Home.py')
if st.session_state.get('role') != 'user':
    st.switch_page('Home.py')

<<<<<<< HEAD
=======
# ── Logo + title ───────────────────────────────────────────────────────────
>>>>>>> 6dd349b20300b66223676a4913ac3d277f63a671
logo_col, title_col = st.columns([1, 6])
with logo_col:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=110)
with title_col:
<<<<<<< HEAD
    st.markdown('<div class="page-title" style="margin-top:0.6rem;">Statistics</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Price trends and history across your watched items.</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div class="card" style="color:#555;">Statistics and charts coming soon.</div>', unsafe_allow_html=True)
=======
    st.markdown('<div class="page-title" style="margin-top:0.6rem;">View Statistics</div>'
                , unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Look at some cool stats'
    '</div>', unsafe_allow_html=True)

st.markdown("---")
>>>>>>> 6dd349b20300b66223676a4913ac3d277f63a671
