import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import logging
logging.basicConfig(format='%(filename)s:%(lineno)s:%(levelname)s -- %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

import streamlit as st
import requests
from datetime import datetime
from modules.nav import SideBarLinks, LOGO_PATH

st.set_page_config(page_title="Feedback | BargainHunters", page_icon="💬", layout="wide")

SideBarLinks(True)

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
    st.markdown('<div class="page-title" style="margin-top:0.6rem;">Submit Feedback</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Share your thoughts, report issues, or suggest improvements.</div>', unsafe_allow_html=True)

st.markdown("---")

# ── Submit feedback form ───────────────────────────────────────────────────
left, _ , right = st.columns([3, 1, 3])

with left:
    st.markdown('<div class="section-label">New Feedback</div>', unsafe_allow_html=True)

    feedback_text = st.text_area(
        "Your feedback",
        placeholder="Tell us what you think…",
        height=160,
        label_visibility="collapsed",
    )

    submitted = st.button("Submit →", type="primary", use_container_width=True)

    if submitted:
        if not feedback_text.strip():
            st.warning("Please enter some feedback before submitting.")
        else:
            try:
                resp = requests.post(
                    "http://api:4000/feedback/",
                    json={
                        "content": feedback_text.strip(),
                        "user_id": st.session_state.get("user_id"),
                    },
                    timeout=5,
                )
                resp.raise_for_status()
                st.success("Thanks! Your feedback has been submitted.")
                logger.info(f"Feedback submitted by user_id={st.session_state.get('user_id')}")
                st.rerun()
            except requests.exceptions.ConnectionError:
                st.error("Cannot reach the API server. Is the backend running?")
            except requests.exceptions.HTTPError as e:
                st.error(f"API error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error submitting feedback: {e}")
                st.error("Something went wrong. Please try again.")

    st.markdown('</div>', unsafe_allow_html=True)

# ── Recent feedback feed ───────────────────────────────────────────────────
with right:
    st.markdown('<div class="section-label" style="margin-bottom:0.6rem;">Recent Feedback</div>', unsafe_allow_html=True)

    try:
        resp = requests.get("http://api:4000/feedback/", timeout=5)
        resp.raise_for_status()
        entries = resp.json()
        logger.info(f"Fetched {len(entries)} feedback entries")
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach the API server.")
        entries = []
    except Exception as e:
        logger.error(f"Error fetching feedback: {e}")
        st.error("Could not load feedback.")
        entries = []

    if not entries:
        st.markdown(
            '<div class="card" style="color:#555; font-size:0.85rem;">No feedback yet</div>',
            unsafe_allow_html=True,
        )
    else:
        for entry in entries[:10]:
            content    = entry.get("content", "")
            user_id    = entry.get("user_id", "?")
            created_at = entry.get("created_at", "")

            try:
                dt_label = datetime.fromisoformat(str(created_at)).strftime("%b %d, %Y · %H:%M")
            except Exception:
                dt_label = str(created_at)

            is_mine = entry.get("user_id") == st.session_state.get("user_id")
            accent  = "border-left: 3px solid #cc2222; padding-left: 0.8rem;" if is_mine else ""

            st.markdown(f"""
            <div class="card" style="margin-bottom:0.6rem; {accent}">
                <div style="color:#f5f5f5; font-size:0.88rem; margin-bottom:0.45rem;">{content}</div>
                <div style="color:#555; font-size:0.72rem;">
                    User #{user_id} &nbsp;·&nbsp; {dt_label}
                    {"&nbsp;· <span style='color:#d4621a;'>You</span>" if is_mine else ""}
                </div>
            </div>
            """, unsafe_allow_html=True)
