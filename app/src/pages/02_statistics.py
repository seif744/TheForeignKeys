import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import logging
logging.basicConfig(format='%(filename)s:%(lineno)s:%(levelname)s -- %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

import streamlit as st
import requests
import pandas as pd
from modules.nav import SideBarLinks, LOGO_PATH

API = os.getenv("API_BASE", "http://api:4000")

st.set_page_config(page_title="Statistics | BargainHunters", page_icon="📊", layout="wide")

SideBarLinks()

if not st.session_state.get('authenticated'):
    st.switch_page('Home.py')
if st.session_state.get('role') != 'user':
    st.switch_page('Home.py')

user_id = st.session_state.get('user_id')

# ── Logo + title ───────────────────────────────────────────────────────────
logo_col, title_col = st.columns([1, 6])
with logo_col:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=110)
with title_col:
    st.markdown('<div class="page-title" style="margin-top:0.6rem;">Statistics</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Platform overview and your personal tracking stats.</div>', unsafe_allow_html=True)

st.markdown("---")


def fetch(path):
    try:
        r = requests.get(f"{API}{path}", timeout=5)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach the API server. Is the backend running?")
        return None
    except Exception as e:
        logger.error(f"Failed to fetch {path}: {e}")
        return None


users      = fetch("/u/")      or []
listings   = fetch("/listings/")   or []
items      = fetch("/items/")      or []
categories = fetch("/categories/") or []
alerts     = (fetch(f"/alerts/watchlist/{user_id}") or []) if user_id else []
notifs     = (fetch(f"/notifications/{user_id}")    or []) if user_id else []

# ── Platform Overview ──────────────────────────────────────────────────────
st.markdown('<div class="section-label">Platform Overview</div>', unsafe_allow_html=True)

active_users    = sum(1 for u in users      if u.get('is_active'))
active_listings = sum(1 for l in listings   if l.get('is_active'))
active_items    = sum(1 for i in items      if i.get('is_active'))
active_cats     = sum(1 for c in categories if c.get('is_active'))

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Users",      len(users),      f"{active_users} active")
col2.metric("Total Listings",   len(listings),   f"{active_listings} active")
col3.metric("Total Items",      len(items),      f"{active_items} active")
col4.metric("Total Categories", len(categories), f"{active_cats} active")

st.markdown("<br>", unsafe_allow_html=True)

# ── Average Prices ─────────────────────────────────────────────────────────
listing_prices  = [l['current_price'] for l in listings   if l.get('current_price') is not None]
item_prices     = [i['current_price'] for i in items      if i.get('current_price') is not None]
cat_prices      = [c['current_price'] for c in categories if c.get('current_price') is not None]

if listing_prices or item_prices or cat_prices:
    st.markdown('<div class="section-label">Average Tracked Prices</div>', unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3)
    p1.metric("Avg Listing Price",  f"${sum(listing_prices)/len(listing_prices):.2f}"  if listing_prices  else "—")
    p2.metric("Avg Item Price",     f"${sum(item_prices)/len(item_prices):.2f}"        if item_prices     else "—")
    p3.metric("Avg Category Price", f"${sum(cat_prices)/len(cat_prices):.2f}"          if cat_prices      else "—")
    st.markdown("<br>", unsafe_allow_html=True)

# ── Listing price distribution chart ──────────────────────────────────────
all_prices = (
    [("Listing", p) for p in listing_prices] +
    [("Item",    p) for p in item_prices]    +
    [("Category",p) for p in cat_prices]
)
if all_prices:
    st.markdown('<div class="section-label">Price Distribution by Entity Type</div>', unsafe_allow_html=True)
    price_df = pd.DataFrame(all_prices, columns=["Type", "Price ($)"])
    avg_by_type = price_df.groupby("Type")["Price ($)"].mean().reset_index()
    avg_by_type = avg_by_type.set_index("Type")
    st.bar_chart(avg_by_type, color="#cc2222")
    st.markdown("<br>", unsafe_allow_html=True)

st.markdown("---")

# ── Your Stats ─────────────────────────────────────────────────────────────
if user_id:
    st.markdown('<div class="section-label">Your Stats</div>', unsafe_allow_html=True)

    active_alerts = sum(1 for a in alerts if a.get('is_active'))

    u1, u2, u3 = st.columns(3)
    u1.metric("My Alerts",             len(alerts), f"{active_alerts} active")
    u2.metric("Notifications Received", len(notifs))
    inactive = len(alerts) - active_alerts
    u3.metric("Inactive Alerts", inactive)

    if alerts:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-label">My Alerts by Watch Type</div>', unsafe_allow_html=True)

        type_counts: dict[str, int] = {}
        for a in alerts:
            wt = a.get('watch_type', 'unknown')
            type_counts[wt] = type_counts.get(wt, 0) + 1

        type_df = pd.DataFrame(
            {"Count": type_counts.values()},
            index=list(type_counts.keys()),
        )
        type_df.index.name = "Watch Type"
        st.bar_chart(type_df, color="#d4621a")

        # Alert threshold type breakdown
        has_dollar  = sum(1 for a in alerts if a.get('drop_amt') is not None)
        has_percent = sum(1 for a in alerts if a.get('drop_percent') is not None)
        has_stock   = sum(1 for a in alerts if a.get('drop_amt') is None and a.get('drop_percent') is None)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-label">My Alerts by Threshold Type</div>', unsafe_allow_html=True)
        t1, t2, t3 = st.columns(3)
        t1.metric("Dollar Drop ($)",   has_dollar)
        t2.metric("Percent Drop (%)",  has_percent)
        t3.metric("Back-in-Stock",     has_stock)

else:
    st.markdown(
        '<div class="card" style="color:#888;">Select an account on the home screen to see your personal stats.</div>',
        unsafe_allow_html=True,
    )

# ── Feedback footer ──────────────────────────────────────────────
with st._bottom:
    st.page_link("pages/05_feedback.py", label="Feedback", icon='💬')
