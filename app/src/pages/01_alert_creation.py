import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import logging
logging.basicConfig(format='%(filename)s:%(lineno)s:%(levelname)s -- %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

import streamlit as st
import requests
from modules.nav import SideBarLinks, LOGO_PATH

API_BASE = os.getenv("API_BASE", "http://api:4000")

st.set_page_config(page_title="Add Alert | BargainHunters", page_icon="🔔", layout="wide")

st.markdown("""
<style>
[data-testid="stForm"] button[kind="primaryFormSubmit"] {
    font-size: 0.72rem;
    padding-left: 0.25rem;
    padding-right: 0.25rem;
}
</style>
""", unsafe_allow_html=True)

SideBarLinks()

# ── Auth guard ─────────────────────────────────────────────────────────────
if not st.session_state.get('authenticated'):
    st.switch_page('Home.py')
if st.session_state.get('role') != 'user':
    st.switch_page('Home.py')
if not st.session_state.get('user_id'):
    st.switch_page('pages/00_user_select.py')

# ── Logo + title ───────────────────────────────────────────────────────────
logo_col, title_col = st.columns([1, 6])
with logo_col:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=110)
with title_col:
    st.markdown('<div class="page-title" style="margin-top:0.6rem;">Create Alert</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-sub">Search eBay for an item and we\'ll notify you when the price drops.</div>',
        unsafe_allow_html=True,
    )

st.markdown("---")

# ── Success state ──────────────────────────────────────────────────────────
if st.session_state.get("alert_created"):
    result = st.session_state.pop("alert_created")
    st.success(
        f"Alert created for **{result.get('target_name', 'item')}** — "
        f"baseline price **${result.get('original_price', 0):.2f}**"
    )
    col1, col2 = st.columns([2, 5])
    with col1:
        if st.button("Back to Watchlist →", type="primary", use_container_width=True):
            st.switch_page("pages/04_watchlist.py")
    with col2:
        if st.button("Create another alert", use_container_width=True):
            for key in ("search_results", "selected_listing"):
                st.session_state.pop(key, None)
            st.rerun()
    st.stop()

# ── Step 1: Search ─────────────────────────────────────────────────────────
search_col, _ = st.columns([4, 3])
with search_col:
    with st.form("search_form", clear_on_submit=False):
        q_col, btn_col = st.columns([5, 1])
        with q_col:
            query = st.text_input(
                "Search eBay",
                label_visibility="collapsed",
                value=st.session_state.get("last_query", ""),
            )
        with btn_col:
            searched = st.form_submit_button("Search", type="primary", use_container_width=True)

    if searched:
        if not query.strip():
            st.warning("Enter a search term first.")
        else:
            st.session_state["last_query"] = query
            st.session_state.pop("selected_listing", None)
            with st.spinner("Searching eBay…"):
                try:
                    resp = requests.get(
                        f"{API_BASE}/ebay/search",
                        params={"q": query.strip()},
                        timeout=15,
                    )
                    if resp.status_code == 200:
                        results = resp.json()
                        st.session_state["search_results"] = results
                        logger.info(f"Search '{query}' returned {len(results)} results")
                    elif resp.status_code == 502:
                        st.error("Could not reach the eBay API. Please try again later.")
                        st.session_state.pop("search_results", None)
                    else:
                        st.error(f"Search failed ({resp.status_code}).")
                        st.session_state.pop("search_results", None)
                except requests.exceptions.ConnectionError:
                    st.error("Cannot reach the API server. Is the backend running?")
                except requests.exceptions.Timeout:
                    st.error("Search timed out. Please try again.")

# ── Step 2: Results grid ───────────────────────────────────────────────────
results = st.session_state.get("search_results", [])

if results and not st.session_state.get("selected_listing"):
    st.markdown(
        f'<div class="section-label" style="margin:1rem 0 0.6rem;">Results for "{st.session_state.get("last_query", "")}"</div>',
        unsafe_allow_html=True,
    )

    cols_per_row = 3
    for row_start in range(0, len(results), cols_per_row):
        row_items = results[row_start: row_start + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, listing in zip(cols, row_items):
            with col:
                price_str = f"${listing['current_price']:.2f}" if listing['current_price'] else "—"
                thumb = listing.get("thumbnail", "")

                st.markdown(f"""
                <div class="card" style="min-height:200px; display:flex; flex-direction:column; gap:0.5rem;">
                    {"<img src='" + thumb + "' style='width:100%;border-radius:6px;object-fit:contain;max-height:130px;'>" if thumb else ""}
                    <div style="color:#f5f5f5; font-size:0.83rem; font-weight:600; line-height:1.4; flex:1;">
                        {listing['name'][:80]}{"…" if len(listing['name']) > 80 else ""}
                    </div>
                    <div style="color:#d4621a; font-size:1rem; font-weight:800;">{price_str}</div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("Set Alert", key=f"pick_{row_start}_{listing['url']}", use_container_width=True):
                    st.session_state["selected_listing"] = listing
                    st.rerun()

# ── Step 3: Configure alert for selected listing ───────────────────────────
selected = st.session_state.get("selected_listing")

if selected:
    st.markdown("---")
    st.markdown('<div class="section-label" style="margin-bottom:0.6rem;">Configure Alert</div>', unsafe_allow_html=True)

    left, _, right = st.columns([3, 1, 3])

    with left:
        # Show selected listing summary
        price_str = f"${selected['current_price']:.2f}" if selected['current_price'] else "—"
        st.markdown(f"""
        <div class="card card-accent" style="margin-bottom:1rem;">
            <div style="color:#888; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.4rem;">Selected listing</div>
            <div style="color:#f5f5f5; font-size:0.9rem; font-weight:600; margin-bottom:0.3rem;">
                {selected['name'][:100]}{"…" if len(selected['name']) > 100 else ""}
            </div>
            <div style="color:#d4621a; font-size:1.1rem; font-weight:800;">Current price: {price_str}</div>
        </div>
        """, unsafe_allow_html=True)

        alert_kind = st.radio(
            "Alert condition",
            options=["drop_amt", "drop_percent", "in_stock"],
            format_func=lambda x: {
                "drop_amt": "Price drop ($)",
                "drop_percent": "Price drop (%)",
                "in_stock": "Back in stock",
            }[x],
            horizontal=True,
        )

        drop_amt = None
        drop_percent = None

        if alert_kind == "drop_amt":
            drop_amt = st.number_input(
                "Notify me when price drops by at least ($)",
                min_value=0.01,
                step=1.0,
                value=5.0,
                format="%.2f",
            )
        elif alert_kind == "drop_percent":
            drop_percent = st.number_input(
                "Notify me when price drops by at least (%)",
                min_value=0.1,
                max_value=99.9,
                step=1.0,
                value=10.0,
                format="%.1f",
            )

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            create = st.button("Create Alert →", type="primary", use_container_width=True)
        with btn_col2:
            if st.button("← Back to results", use_container_width=True):
                st.session_state.pop("selected_listing", None)
                st.rerun()

        if create:
            payload = {
                "ebay_url": selected["url"],
                "watch_type": "listing",
                "user_id": st.session_state.get("user_id"),
                "drop_amt": drop_amt,
                "drop_percent": drop_percent,
            }
            try:
                resp = requests.post(
                    f"{API_BASE}/alerts/from-url",
                    json=payload,
                    timeout=15,
                )
                if resp.status_code == 201:
                    st.session_state["alert_created"] = resp.json()
                    st.session_state.pop("selected_listing", None)
                    st.session_state.pop("search_results", None)
                    logger.info(f"Alert created: {resp.json()}")
                    st.rerun()
                elif resp.status_code == 400:
                    st.error("Invalid request: " + resp.json().get("error", "check the listing URL."))
                elif resp.status_code == 404:
                    st.error("eBay returned no data for this listing. It may have ended.")
                elif resp.status_code == 502:
                    st.error("Could not reach the eBay API. Please try again later.")
                else:
                    st.error(f"Unexpected error ({resp.status_code}).")
            except requests.exceptions.ConnectionError:
                st.error("Cannot reach the API server. Is the backend running?")
            except requests.exceptions.Timeout:
                st.error("Request timed out. Please retry.")
            except Exception as e:
                logger.error(f"Unexpected error creating alert: {e}")
                st.error("Something went wrong. Please try again.")

    with right:
        st.markdown('<div class="section-label" style="margin-bottom:0.6rem;">How alerts work</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="card">
            <div style="color:#888; font-size:0.83rem; line-height:1.6;">
                <b style="color:#d4621a;">Price drop ($)</b><br>
                Get notified when the price falls by at least the dollar amount you set.<br><br>
                <b style="color:#d4621a;">Price drop (%)</b><br>
                Get notified when the price falls by at least the percentage you set.<br><br>
                <b style="color:#d4621a;">Back in stock</b><br>
                Get notified as soon as the item becomes available again.
            </div>
        </div>
        """, unsafe_allow_html=True)
