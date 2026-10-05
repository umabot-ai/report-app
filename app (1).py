"""
Report web app (Streamlit) - replaces the Discord entry bot.

ENTRY part  : Name dropdown (required) + Late Reason dropdown (optional)
              + one-click "Send Report" button.
REPORT part : every press posts a bill-style report with the chosen values and
              an automatic date/time (Sri Lanka time). Reports are shared by
              everyone who opens the app.

Run locally:   streamlit run app.py
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

# ---------- EDIT THESE ----------
COLUMN1_TITLE = "Name"
COLUMN1_OPTIONS = [
    "Gayan Sir", "Nishantha Sir", "Janith Sir", "Devaka Sir", "Shehan Sir",
    "Dilshan Sir", "Dinesh Sir", "Hemantha Sir", "Some Sir", "Pabasara Sir",
    "Rajitha Sir", "Lasindu Sir", "Shanaka Sir", "Namal Sir", "Madhawa Sir",
    "Suchira Sir", "Dinuka Sir", "Supun Sir", "Gimhan Sir", "Saman Sir",
    "Indika Sir", "Buddika Sir", "Miyuru Sir", "Chamika Sir", "Chirath Sir",
    "Charith Sir", "Ruwan Sir", "Danushka Sir", "Himanka Sir", "Ashoka Sir",
    "Bandara Sir", "Sanjaya Sir", "Aruni Miss", "Bodhini Miss", "Iresha Miss",
    "Harshani Miss", "Inoka Miss", "Thathya Miss", "Dileni Miss",
    "Pabasaraa Miss", "Ayesha Miss",
]

LATE_REASON_TITLE = "Late Reason"
LATE_REASON_OPTIONS = [
    "Requested",
    "Lecturer Late",
    "Technical Error",
    "Clz Queue",
]

TIMEZONE = ZoneInfo("Asia/Colombo")
# --------------------------------

st.set_page_config(page_title="Report Entry", page_icon="🧾")


@st.cache_resource
def shared_reports() -> list:
    """One list shared by every visitor (kept until the app restarts)."""
    return []


reports = shared_reports()


def now_text() -> str:
    return datetime.now(TIMEZONE).strftime("%d-%m-%Y %H:%M:%S")


def send_report():
    """Runs when the button is clicked."""
    name = st.session_state.get("name")
    if not name:
        st.session_state.flash = ("error", f"Please choose a {COLUMN1_TITLE} first.")
        return

    reports.append(
        {
            "Date": now_text(),
            COLUMN1_TITLE: name,
            LATE_REASON_TITLE: st.session_state.get("reason") or "",
            "Submitted by": (st.session_state.get("submitter") or "").strip(),
        }
    )

    # Reset the form after a successful submission.
    st.session_state.name = None
    st.session_state.reason = None
    st.session_state.flash = ("success", "Report sent ✅")


def bill(r: dict) -> str:
    line = "-" * 34
    return (
        f"{line}\n"
        f"{'REPORT':^34}\n"
        f"{line}\n"
        f"Date         : {r['Date']}\n"
        f"{COLUMN1_TITLE:<13}: {r[COLUMN1_TITLE]}\n"
        f"{LATE_REASON_TITLE:<13}: {r[LATE_REASON_TITLE] or '-'}\n"
        f"Submitted by : {r['Submitted by'] or '-'}\n"
        f"{line}"
    )


# ---------------- ENTRY ----------------
st.title("🧾 Data Entry")
st.caption(f"Now: {now_text()}")

st.selectbox(
    f"{COLUMN1_TITLE} (required)",
    COLUMN1_OPTIONS,
    index=None,
    placeholder=f"Select {COLUMN1_TITLE}",
    key="name",
)
st.selectbox(
    f"{LATE_REASON_TITLE} (optional)",
    LATE_REASON_OPTIONS,
    index=None,
    placeholder=f"Select {LATE_REASON_TITLE}",
    key="reason",
)
st.text_input("Submitted by (optional)", key="submitter")

st.button("Send Report", type="primary", on_click=send_report)

flash = st.session_state.pop("flash", None)
if flash:
    (st.success if flash[0] == "success" else st.error)(flash[1])

# ---------------- REPORTS ----------------
st.divider()
st.subheader("Reports")

if not reports:
    st.info("No reports yet.")
else:
    latest = reports[-1]
    st.code(bill(latest), language=None)

    df = pd.DataFrame(reports[::-1])
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button(
        "Download all reports (CSV)",
        df.to_csv(index=False).encode("utf-8"),
        file_name="reports.csv",
        mime="text/csv",
    )
