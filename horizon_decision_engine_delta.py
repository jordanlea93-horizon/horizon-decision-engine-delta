import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="Horizon Decision Engine — Delta Model", layout="wide")

# =========================
# Asset -> Anchors mapping
# =========================
ASSET_ANCHORS = {
    "Cocoa": {"Macro Anchor": "Commercials", "Val Anchor": "Macro"},
    "Coffee": {"Macro Anchor": "Commercials", "Val Anchor": "Dollar & Gold"},
    "Cotton": {"Macro Anchor": "Commercials", "Val Anchor": "Dollar & Gold"},
    "Corn": {"Macro Anchor": "Commercials", "Val Anchor": "Dollar"},
    "Soybean": {"Macro Anchor": "Commercials", "Val Anchor": "Dollar & Gold"},
    "Sugar": {"Macro Anchor": "Commercials", "Val Anchor": "Dollar"},
    "Wheat": {"Macro Anchor": "Commercials", "Val Anchor": "Dollar"},
    "Bitcoin": {"Macro Anchor": "Retail", "Val Anchor": "Dollar"},
    "Eth": {"Macro Anchor": "Retail", "Val Anchor": "Macro"},
    "Natural Gas": {"Macro Anchor": "Commercial , Seasonals", "Val Anchor": "Macro"},
    "Crude Oil": {"Macro Anchor": "Commercial , Seasonals", "Val Anchor": "Dollar & Gold"},
    "Euro": {"Macro Anchor": "Commercials & Retail", "Val Anchor": "Dollar"},
    "British Pound": {"Macro Anchor": "Commercials & Retail", "Val Anchor": "Dollar & Gold"},
    "Japanese Yen": {"Macro Anchor": "Commercials & Retail", "Val Anchor": "Delta Only"},
    "Swiss Franc": {"Macro Anchor": "Commercials & Retail", "Val Anchor": "Delta Only"},
    "Canadian Dollar": {"Macro Anchor": "Commercials & Retail", "Val Anchor": "Dollar"},
    "Australian Dollar": {"Macro Anchor": "Commercials & Retail", "Val Anchor": "Dollar"},
    "New Zealand Dollar": {"Macro Anchor": "Commercials & Retail", "Val Anchor": "Dollar"},
    "US Dollar Index": {"Macro Anchor": "Commercials & Retail", "Val Anchor": "Delta Only"},
    "Platinum": {"Macro Anchor": "Commercials", "Val Anchor": "Dollar & Gold"},
    "Palladium": {"Macro Anchor": "Commercials", "Val Anchor": "Dollar & Gold"},
    "Copper": {"Macro Anchor": "Commercials & Retail", "Val Anchor": "Dollar"},
    "Gold": {"Macro Anchor": "Commercials", "Val Anchor": "Dollar"},
    "Silver": {"Macro Anchor": "Commercials", "Val Anchor": "Dollar"},
    "Nasdaq": {"Macro Anchor": "Seasonality", "Val Anchor": "Bonds"},
    "Dow Jones": {"Macro Anchor": "Seasonality", "Val Anchor": "Bonds"},
    "S&P 500": {"Macro Anchor": "Seasonality", "Val Anchor": "Bonds"},
    "Russel 2000": {"Macro Anchor": "Seasonality", "Val Anchor": "Bonds"},
    "Dax": {"Macro Anchor": "Seasonality", "Val Anchor": "Bonds"},
    "Google": {"Macro Anchor": "Seasonal & Catalyst", "Val Anchor": "Bonds"},
    "Apple": {"Macro Anchor": "Seasonal & Catalyst", "Val Anchor": "Bonds"},
    "Microsoft": {"Macro Anchor": "Seasonal & Catalyst", "Val Anchor": "Bonds"},
    "Amazon": {"Macro Anchor": "Seasonal & Catalyst", "Val Anchor": "Bonds"},
    "Meta": {"Macro Anchor": "Seasonal & Catalyst", "Val Anchor": "Bonds"},
    "Nvidia": {"Macro Anchor": "Seasonal & Catalyst", "Val Anchor": "Bonds"},
    "Tesla": {"Macro Anchor": "Seasonal & Catalyst", "Val Anchor": "Macro"},
    "Ferrari": {"Macro Anchor": "Seasonal & Catalyst", "Val Anchor": "Bonds"},
    "GBP / JPY": {"Macro Anchor": "Delta Only", "Val Anchor": "Gold & GBP"},
    "EUR / AUD": {"Macro Anchor": "Delta Only", "Val Anchor": "Gold & GBP"},
    "USD / JPY": {"Macro Anchor": "Delta Only", "Val Anchor": "Gold & GBP"},
    "USD / CHF": {"Macro Anchor": "Delta Only", "Val Anchor": "Bonds"},
    "USD / CAD": {"Macro Anchor": "Delta Only", "Val Anchor": "Dollar"},
}
ASSET_LIST = sorted(ASSET_ANCHORS.keys())

# =========================
# Helpers
# =========================
def log_row(path: Path, row: dict):
    if path.exists():
        df = pd.read_csv(path)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])
    df.to_csv(path, index=False)

def color_box(label: str, text: str, bg: str, fg: str = "#1f2937"):
    return f"""
    <div style="background:{bg};color:{fg};padding:6px 10px;border-radius:6px;
    font-weight:600;margin-bottom:6px;">
    <b>{label}</b><br>{text}
    </div>
    """

def val_anchor_box(val_anchor: str):
    colors = {
        "Dollar": "#e0f2ff",        # light blue
        "Bonds": "#ede9fe",         # light purple
        "Dollar & Gold": "#e2e8f0", # grey/blue
        "Gold & GBP": "#fef3c7",    # light gold
        "Macro": "#fee2e2",         # light red
    }
    return color_box("Val Anchor (Valuation driver):", val_anchor, colors.get(val_anchor, "#f1f5f9"))

# =========================
# UI Layout
# =========================
st.title("Horizon Decision Engine — Delta Model")
st.markdown("### IS THIS TRADE WORTH YOUR TIME AND CAPITAL?")

colA, colB = st.columns([2, 1])
with colA:
    date_input = st.date_input("Date", value=datetime.today())
    asset = st.selectbox("1) What is the asset?", ASSET_LIST, index=ASSET_LIST.index("Gold") if "Gold" in ASSET_LIST else 0)

with colB:
    st.markdown("### Asset Driven Fundamentals")
    anchors = ASSET_ANCHORS.get(asset, {})
    macro_anchor = anchors.get("Macro Anchor", "—")
    val_anchor = anchors.get("Val Anchor", "—")
    # Macro Anchor: light blue for all
    st.markdown(color_box("Macro Anchor (COT / Macro):", macro_anchor, "#e0f2ff", "#1e3a8a"), unsafe_allow_html=True)
    # Val Anchor: colored by type (incl. red for 'Macro')
    st.markdown(val_anchor_box(val_anchor), unsafe_allow_html=True)

st.divider()

# Phase selection (added Ranging Market)
flow_phase = st.radio(
    "2) Flow phase",
    ["Pro Flow", "Counter Flow", "Ranging Market"],
    help="Pro Flow = with trend, internal intact. Counter Flow = internal broken with intention. Ranging = clear range within internal structure."
)

reasons = []
final_decision = None  # "Proximal Entry" / "Inducement Entry" / "Liquidity Entry" / "Trade Not Valid"

# =========================
# PRO FLOW
# =========================
if flow_phase == "Pro Flow":
    st.subheader("Pro Flow Questions")
    q1 = st.radio("Is the market trending internally (protections, mitigations, MS breaks, weekly onside)?", ["Yes", "No"])
    if q1 == "No":
        final_decision = "Trade Not Valid"
        reasons.append("Market not trending internally / weekly not onside.")

    q2 = st.radio("Does the zone have direct intention OR decisional break with intent? (Decisional can be mid-leg)", ["Yes", "No"])
    if final_decision is None and q2 == "No":
        final_decision = "Trade Not Valid"
        reasons.append("Zone lacks direct intention / no structural break with intent.")

    if final_decision is None:
        clean_choice = st.radio("Is the zone formation clean?", [
            "Yes — Clean (no large wicks)",
            "Yes — Clean, but with a large wick",
            "No — but clear swing point"
        ])
        traps = st.radio("Any liquidity traps/inducements nearby?", ["No / not obvious", "Yes — obvious nearby"])

        if clean_choice.startswith("Yes — Clean (no large wicks)"):
            provisional = "Proximal Entry"
            reasons.append("Zone clean → proximal/body entry allowed.")
        elif clean_choice.startswith("Yes — Clean, but with a large wick"):
            provisional = "Inducement Entry"
            reasons.append("Zone clean but with wick → inducement entry.")
        else:
            provisional = "Liquidity Entry"
            reasons.append("Zone not clean but clear swing point → liquidity sweep entry.")

        if traps == "Yes — obvious nearby":
            final_decision = "Liquidity Entry"
            reasons.append("Obvious nearby liquidity → liquidity entry only.")
        else:
            final_decision = provisional

# =========================
# COUNTER FLOW
# =========================
elif flow_phase == "Counter Flow":
    st.subheader("Counter Flow Questions")
    q1 = st.radio("Is the Daily zone at a clean WEEKLY OB or swing point?", ["Yes", "No"])
    if q1 == "No":
        final_decision = "Trade Not Valid"
        reasons.append("Daily zone not at clean weekly OB/swing.")

    q2 = st.radio("Any liquidity traps/HTF zones nearby?", ["No — not close", "Yes — could act as draw"])
    if final_decision is None and q2 == "Yes — could act as draw":
        final_decision = "Trade Not Valid"
        reasons.append("Nearby HTF zone could act as draw → skip this zone.")
        reasons.append("If the delta signal is still valid, the next HQ zone is valid.")

    q3 = st.radio("Is the weekly reacting/sweeping against trade?", ["No", "Yes"])
    prefer_liquidity = (q3 == "Yes")
    if prefer_liquidity:
        reasons.append("Weekly sweep against trade → liquidity entry preferred.")

    q4 = st.radio("Is the Primary Valuation Benchmark OR TDI active?", ["Yes", "No"])
    if final_decision is None and q4 == "No":
        final_decision = "Trade Not Valid"
        reasons.append("Primary benchmark/TDI not active → trade not valid.")

    if final_decision is None:
        clean_choice = st.radio("Is the zone formation clean?", [
            "Yes — Clean (no large wicks)",
            "Yes — Clean, but with a large wick",
            "No — but clear swing point"
        ])
        if clean_choice.startswith("Yes — Clean (no large wicks)"):
            provisional = "Proximal Entry"
            reasons.append("Zone clean → proximal entry allowed.")
        elif clean_choice.startswith("Yes — Clean, but with a large wick"):
            provisional = "Inducement Entry"
            reasons.append("Zone clean but with wick → inducement entry.")
        else:
            provisional = "Liquidity Entry"
            reasons.append("Zone not clean but swing point → liquidity sweep entry.")

        q5 = st.radio("Does the zone have clear intent away from it (true supply/demand at extremity)?", ["Yes", "No"])
        if q5 == "No":
            final_decision = "Trade Not Valid"
            reasons.append("Zone lacks clear intent → not valid.")
        else:
            if prefer_liquidity:
                final_decision = "Liquidity Entry"
                reasons.append("Weekly counter-sweep → liquidity entry.")
            else:
                final_decision = provisional

# =========================
# RANGING MARKET
# =========================
else:
    st.subheader("Ranging Market Questions")
    # Q1: clear range within internal structure
    r1 = st.radio("Has the market formed a clear range, contained within internal structure?", ["Yes", "No"])
    if r1 == "No":
        final_decision = "Trade Not Valid"
        reasons.append("No clear, contained range → trade invalid.")

    # Q2: primary Val Signal or TDI active?
    r2 = st.radio("Is the Primary Val Signal or TDI active?", ["Yes", "No"])
    if final_decision is None and r2 == "No":
        final_decision = "Trade Not Valid"
        reasons.append("Primary Val Signal / TDI not active → trade invalid.")

    # Q3: zone at extremity of range?
    r3 = st.radio("Is the Zone at the extremity of the range?", ["Yes", "No"])
    if final_decision is None and r3 == "No":
        final_decision = "Trade Not Valid"
        reasons.append("Zone not at range extremity (no value).")

    # Q4: inducement present into entry (liquidity entry counts)
    r4 = st.radio("Is there inducement present coming into the entry? (Liquidity entry counts as inducement)", ["Yes", "No"])
    if final_decision is None and r4 == "No":
        final_decision = "Trade Not Valid"
        reasons.append("No inducement present → prone to traps (trade invalid).")

    # Q5: liquidity traps around zone?
    r5 = st.radio("Are there any liquidity traps around the Zone?", ["No", "Yes"])
    ranging_prefer_liquidity = (r5 == "Yes")
    if ranging_prefer_liquidity:
        reasons.append("Liquidity traps around zone → must be Liquidity Entry or the next HQ zone if close (within range).")

    # Q6: cleanliness → entry mapping
    if final_decision is None:
        clean_choice = st.radio("Is the zone formation clean?", [
            "Yes — Clean (no large wicks)",
            "Yes — Clean, but with a large wick",
            "No — but clear swing point of the range"
        ])
        if clean_choice.startswith("Yes — Clean (no large wicks)"):
            provisional = "Proximal Entry"
            reasons.append("Zone clean → proximal/body entry allowed.")
        elif clean_choice.startswith("Yes — Clean, but with a large wick"):
            provisional = "Inducement Entry"
            reasons.append("Zone clean but with large wick → inducement entry.")
        else:
            provisional = "Liquidity Entry"
            reasons.append("Zone not clean but clear swing point of the range → liquidity sweep entry.")

        # Q7: clear intent within the range?
        r7 = st.radio("Did the Zone cause clear intent within the range?", ["Yes", "No"])
        if r7 == "No":
            final_decision = "Trade Not Valid"
            reasons.append("Zone did not cause clear intent (no true S/D) → trade invalid.")
        else:
            if ranging_prefer_liquidity:
                final_decision = "Liquidity Entry"
            else:
                final_decision = provisional

        # Note for all valid ranging trades
        if final_decision != "Trade Not Valid":
            reasons.append("Target range liquidity.")

# =========================
# Verdict
# =========================
st.divider()
st.header("Final Verdict")
badge_color = {
    "Proximal Entry": "#16a34a",
    "Inducement Entry": "#7c3aed",
    "Liquidity Entry": "#ea580c",
    "Trade Not Valid": "#dc2626",
}.get(final_decision, "#334155")

st.markdown(
    f"#### <span style='color:{badge_color}'><b>{final_decision or '—'}</b></span>",
    unsafe_allow_html=True
)

st.markdown("**Reasons:**")
for r in reasons:
    st.write("- " + r)

# Global note for all phases
st.caption("Note: Use HTF for final refinement if the zone is large.")

# Notes & Risk + Logger
st.markdown("### Notes & Risk")
risk_r = st.number_input("Risk size (R)", min_value=0.0, max_value=10.0, value=1.0, step=0.25)
notes = st.text_area("Notes (optional)")

LOG_PATH = Path.home() / "HorizonDecisionLogs.csv"
if st.button("📥 Log decision to CSV"):
    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": date_input.strftime("%Y-%m-%d"),
        "asset": asset,
        "macro_anchor": macro_anchor,
        "val_anchor": val_anchor,
        "flow_phase": flow_phase,
        "final_decision": final_decision or "",
        "reasons": " | ".join(reasons),
        "risk_R": risk_r,
        "notes": notes,
    }
    try:
        log_row(LOG_PATH, row)
        st.success(f"Logged to: {LOG_PATH}")
    except Exception as e:
        st.error(f"Failed to log: {e}")
