"""
Report web app (Streamlit) - replaces the Discord entry bot.

ENTRY part  : Name dropdown (required), Late Reason dropdown (optional),
              Submitted by dropdown (optional) + one-click "Send Report" button.
REPORT part : every press saves a row permanently to a Google Sheet (which you
              can open or download as Excel) and shows a bill-style report with
              an automatic date/time (Sri Lanka time).

If the Google Sheet is not connected yet, the app still works but keeps the
reports only in temporary memory (a warning is shown on the page).

Run locally:   streamlit run app.py
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import gspread
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

SUBMITTER_TITLE = "Submitted by"
SUBMITTER_OPTIONS = [  # <-- put the real names of the people who submit here
    "Person 1",
    "Person 2",
    "Person 3",
]

TIMEZONE = ZoneInfo("Asia/Colombo")
# --------------------------------

HEADERS = ["Date", COLUMN1_TITLE, LATE_REASON_TITLE, SUBMITTER_TITLE]

st.set_page_config(page_title="Report Entry", page_icon="🧾")


# ---------- storage ----------
@st.cache_resource
def get_sheet():
    """Connect to the Google Sheet. Returns None if it is not set up yet."""
    try:
        creds = dict(st.secrets["gcp_service_account"])
        sheet_id = st.secrets["sheet_id"]
    except Exception:
        return None
    ws = gspread.service_account_from_dict(creds).open_by_key(sheet_id).sheet1
    if not ws.get_all_values():
        ws.append_row(HEADERS, value_input_option="RAW")
    return ws


@st.cache_resource
def memory_reports() -> list:
    """Temporary fallback, lost when the app restarts."""
    return []


@st.cache_data(ttl=20)
def read_sheet_rows():
    return get_sheet().get_all_records()


def save_row(row: dict):
    ws = get_sheet()
    if ws is None:
        memory_reports().append(row)
    else:
        ws.append_row([row[h] for h in HEADERS], value_input_option="RAW")
        read_sheet_rows.clear()


def load_rows() -> list:
    if get_sheet() is None:
        return memory_reports()
    return read_sheet_rows()


# ---------- helpers ----------
def now_text() -> str:
    return datetime.now(TIMEZONE).strftime("%d-%m-%Y %H:%M:%S")


def send_report():
    """Runs when the button is clicked."""
    name = st.session_state.get("name")
    if not name:
        st.session_state.flash = ("error", f"Please choose a {COLUMN1_TITLE} first.")
        return

    row = {
        "Date": now_text(),
        COLUMN1_TITLE: name,
        LATE_REASON_TITLE: st.session_state.get("reason") or "",
        SUBMITTER_TITLE: st.session_state.get("submitter") or "",
    }

    try:
        save_row(row)
    except Exception as e:  # keep the form filled so nothing is lost
        st.session_state.flash = ("error", f"Could not save the report: {e}")
        return

    # Reset the form after a successful submission.
    st.session_state.name = None
    st.session_state.reason = None
    st.session_state.submitter = None
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
        f"{SUBMITTER_TITLE:<13}: {r[SUBMITTER_TITLE] or '-'}\n"
        f"{line}"
    )


# ---------------- ENTRY ----------------
st.title("🧾 Data Entry")
st.caption(f"Now: {now_text()}")

if get_sheet() is None:
    st.warning(
        "Google Sheet is not connected yet - reports are only kept temporarily "
        "and will be lost when the app restarts."
    )

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
st.selectbox(
    f"{SUBMITTER_TITLE} (optional)",
    SUBMITTER_OPTIONS,
    index=None,
    placeholder=f"Select {SUBMITTER_TITLE}",
    key="submitter",
)

st.button("Send Report", type="primary", on_click=send_report)

flash = st.session_state.pop("flash", None)
if flash:
    (st.success if flash[0] == "success" else st.error)(flash[1])

# ---------------- REPORTS ----------------
st.divider()
st.subheader("Reports")

try:
    reports = load_rows()
except Exception as e:
    reports = []
    st.error(f"Could not read the Google Sheet: {e}")

if not reports:
    st.info("No reports yet.")
else:
    st.code(bill(reports[-1]), language=None)

    df = pd.DataFrame(reports[::-1])
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button(
        "Download all reports (CSV)",
        df.to_csv(index=False).encode("utf-8"),
        file_name="reports.csv",
        mime="text/csv",
    )
