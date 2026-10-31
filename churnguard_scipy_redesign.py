import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re
import json
import html
import base64
from pathlib import Path
import streamlit.components.v1 as components

try:
    from streamlit_mic_recorder import speech_to_text
    MIC_RECORDER_AVAILABLE = True
except ImportError:
    speech_to_text = None
    MIC_RECORDER_AVAILABLE = False

# ============================================================
# ChurnGuard AI — customer retention prototype
# Palette: black, warm cream, charcoal, burnt orange, coral
# ============================================================

st.set_page_config(
    page_title="ChurnGuard AI | Customer Retention",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# PowerPoint-inspired palette
C = {
    "black": "#000000",
    "cream": "#FFFDEE",
    "charcoal": "#1A1A1A",
    "cream2": "#F4EFD9",
    "orange": "#F53A07",
    "coral": "#FF8A5C",
    "beige": "#D9D4BE",
    "taupe": "#8C8777",
    "grey": "#3A3A3A",
    "pale_coral": "#FFB199",
    "white": "#FFFFFF",
    "lime": "#A8D83E",
    "lime_soft": "#C8EF72",
    "panel": "#151515",
    "line": "#303030",
}
RISK_COLORS = {"Low": C["lime"], "Medium": C["coral"], "High": C["orange"]}
SEGMENT_COLORS = {
    "Champions": C["coral"],
    "Loyal Customers": C["pale_coral"],
    "Recent Customers": C["beige"],
    "Needs Nurturing": C["taupe"],
    "At Risk": C["orange"],
    "New Customers": "#E8CFA0",
}

st.markdown(
    f"""
    <style>
      :root {{ color-scheme: dark; }}
      .stApp {{ background: {C['black']}; color: {C['cream']}; }}
      [data-testid="stMainBlockContainer"] {{ max-width: 1600px; padding-top: 1.25rem; padding-bottom: 2rem; }}
      [data-testid="stSidebar"] {{ background: #101010; border-right: 1px solid {C['line']}; }}
      [data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}
      h1, h2, h3, h4, p, label {{ color: {C['cream']}; }}
      h1 {{ letter-spacing: -.045em; font-weight: 650; }}
      h2, h3 {{ letter-spacing: -.025em; }}
      .hero {{ padding: 1rem 1.3rem 1.15rem; border-radius: 20px; margin-bottom: .9rem;
        background: radial-gradient(circle at 92% 20%, #25291b 0, #151515 32%, #101010 75%);
        border: 1px solid {C['line']}; position: relative; overflow: hidden; }}
      .hero:after {{ content: '✳'; position: absolute; right: 3%; top: -35px; font-size: 130px; color: {C['lime']}; opacity: .12; pointer-events: none; }}
      .hero p {{ color: {C['cream2']}; margin-bottom: .1rem; max-width: 700px; }}
      .eyebrow {{ color: {C['lime']}; font-size: .70rem; letter-spacing: .17em; font-weight: 800; }}
      div[data-testid="stMetric"] {{ background: {C['panel']}; border: 1px solid {C['line']}; padding: 13px 16px; border-radius: 17px; min-height: 100px; }}
      div[data-testid="stMetricLabel"] {{ color: {C['beige']}; font-size: .78rem; }}
      div[data-testid="stMetricValue"] {{ color: {C['cream']}; font-weight: 650; }}
      div[data-testid="stMetricDelta"] svg {{ color: {C['lime']}; }}
      .panel {{ background: {C['panel']}; border: 1px solid {C['line']}; border-radius: 18px; padding: 1rem 1.1rem; margin: .3rem 0 .8rem; }}
      .note {{ background: {C['panel']}; border: 1px solid {C['line']}; padding: 14px 16px; border-radius: 14px; color: {C['cream2']}; }}
      .tag {{ display: inline-block; padding: .22rem .55rem; border-radius: 999px; font-size: .78rem; font-weight: 750; border: 1px solid {C['line']}; background: #202020; color: {C['cream']}; }}
      .stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] button {{ border-radius: 999px; border: 1px solid {C['lime']}; color: #101010; background: {C['lime']}; font-weight: 750; transition: all .18s ease; }}
      .stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] button:hover {{ border-color: {C['lime_soft']}; color: #101010; background: {C['lime_soft']}; transform: translateY(-1px); }}
      [data-testid="stDataFrame"], [data-testid="stTable"] {{ border: 1px solid {C['line']}; border-radius: 14px; overflow: hidden; }}
      .stSelectbox label, .stMultiSelect label, .stSlider label, .stFileUploader label, .stTextInput label {{ color: {C['cream2']}; }}
      [data-testid="stForm"] {{ border: 0; padding: 0; }}
      [data-testid="stTextInput"] input {{ background: #151515; border: 1px solid {C['line']}; border-radius: 999px; min-height: 42px; }}
      [data-testid="stTextInput"] input:focus {{ box-shadow: none !important; outline: 1px solid {C['lime']} !important; border-color: {C['lime']} !important; }}
      [data-testid="stForm"] [data-testid="stTextInput"] {{ box-shadow: none !important; }}
      [data-testid="stPopover"] button {{ border-radius: 999px; }}
      [data-testid="stSidebar"] [data-testid="stRadio"] label {{ padding: .28rem .35rem; border-radius: 10px; }}
      [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{ background: #242424; }}
      [data-testid="stExpander"] {{ background: #111111; border: 1px solid {C['line']}; border-radius: 15px; }}
      [data-testid="stExpander"] summary p {{ font-weight: 600; }}
      [data-baseweb="tab-list"] {{ gap: .35rem; }}
      [data-baseweb="tab"] {{ background: #151515; border-radius: 999px; padding: .45rem .9rem; }}
      [aria-selected="true"][data-baseweb="tab"] {{ background: {C['lime']}; color: #101010; }}
      a {{ color: {C['lime']} !important; }}
      footer {{ visibility: hidden; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# Local-only profile persistence for this single-user prototype.
PROFILE_PATH = Path(__file__).with_name("churnguard_profile.json")
DEFAULT_PROFILE = {
    "name": "Akshay", "email": "", "phone": "", "tagline": "Customer intelligence and scientific computing",
    "biography": "", "education": "", "skills": "Python, pandas, SciPy, Streamlit",
    "workspace": "ChurnGuard AI", "website": "", "github": "", "avatar_b64": ""
}

def load_local_profile():
    try:
        if PROFILE_PATH.exists():
            loaded = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                return {**DEFAULT_PROFILE, **loaded}
    except (OSError, json.JSONDecodeError):
        pass
    return DEFAULT_PROFILE.copy()

def save_local_profile(profile):
    # This file stays beside the app and is not a cloud account or authentication system.
    PROFILE_PATH.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")

if "local_profile" not in st.session_state:
    st.session_state["local_profile"] = load_local_profile()


@st.cache_data
def make_demo_data(n=240):
    """Create synthetic example data; not real customers."""
    rng = np.random.default_rng(17)
    today = pd.Timestamp.today().normalize()
    archetypes = rng.choice(
        ["Champion", "Regular", "At Risk", "New"],
        size=n,
        p=[0.24, 0.38, 0.23, 0.15],
    )
    recency, orders, spend = [], [], []
    for group in archetypes:
        if group == "Champion":
            recency.append(int(rng.integers(1, 31)))
            orders.append(int(rng.integers(7, 26)))
            spend.append(round(float(rng.lognormal(5.0, 0.65)), 2))
        elif group == "Regular":
            recency.append(int(rng.integers(15, 80)))
            orders.append(int(rng.integers(2, 13)))
            spend.append(round(float(rng.lognormal(4.5, 0.7)), 2))
        elif group == "At Risk":
            recency.append(int(rng.integers(75, 190)))
            orders.append(int(rng.integers(1, 8)))
            spend.append(round(float(rng.lognormal(4.2, 0.8)), 2))
        else:
            recency.append(int(rng.integers(1, 26)))
            orders.append(int(rng.integers(1, 4)))
            spend.append(round(float(rng.lognormal(3.9, 0.65)), 2))
    return pd.DataFrame(
        {
            "customer_id": [f"CUST-{i:04d}" for i in range(1, n + 1)],
            "last_purchase_date": [
                (today - pd.Timedelta(days=int(x))).date() for x in recency
            ],
            "total_spend": spend,
            "order_count": orders,
            "region": rng.choice(["North", "South", "East", "West"], n),
            "acquisition_channel": rng.choice(["Web", "Mobile", "Referral", "Store"], n),
        }
    )


def score_customers(raw, id_col, date_col, spend_col, freq_col, inactive_days):
    """Calculate transparent RFM-style features and heuristic risk score."""
    df = raw.copy()
    df = df.rename(
        columns={
            id_col: "customer_id",
            date_col: "last_purchase_date",
            spend_col: "total_spend",
            freq_col: "order_count",
        }
    )
    required = ["customer_id", "last_purchase_date", "total_spend", "order_count"]
    if any(col not in df.columns for col in required):
        return pd.DataFrame()

    df["last_purchase_date"] = pd.to_datetime(df["last_purchase_date"], errors="coerce")
    df["total_spend"] = pd.to_numeric(df["total_spend"], errors="coerce")
    df["order_count"] = pd.to_numeric(df["order_count"], errors="coerce")
    df = df.dropna(subset=["customer_id", "last_purchase_date"])
    df["total_spend"] = df["total_spend"].fillna(0).clip(lower=0)
    df["order_count"] = df["order_count"].fillna(0).clip(lower=0)
    if df.empty:
        return df

    # Reference date avoids negative recency for future-dated records.
    reference_date = max(
        pd.Timestamp.today().normalize(),
        df["last_purchase_date"].max().normalize() + pd.Timedelta(days=1),
    )
    df["recency_days"] = (
        reference_date - df["last_purchase_date"].dt.normalize()
    ).dt.days.clip(lower=0)

    order_90 = max(float(df["order_count"].quantile(0.90)), 1.0)
    spend_90 = max(float(df["total_spend"].quantile(0.90)), 1.0)
    recency_component = (df["recency_days"] / max(inactive_days * 2, 1)).clip(0, 1)
    frequency_component = 1 - (df["order_count"] / order_90).clip(0, 1)
    monetary_component = 1 - (df["total_spend"] / spend_90).clip(0, 1)

    df["risk_recency_component"] = (recency_component * 65).round(1)
    df["risk_frequency_component"] = (frequency_component * 20).round(1)
    df["risk_monetary_component"] = (monetary_component * 15).round(1)
    df["churn_risk_score"] = (
        df["risk_recency_component"]
        + df["risk_frequency_component"]
        + df["risk_monetary_component"]
    ).clip(0, 100).round(1)

    df["risk_level"] = np.select(
        [
            df["recency_days"] >= inactive_days,
            df["churn_risk_score"] >= 60,
            df["churn_risk_score"] >= 35,
        ],
        ["High", "High", "Medium"],
        default="Low",
    )

    median_orders = max(float(df["order_count"].median()), 1.0)
    df["rfm_segment"] = np.select(
        [
            (df["recency_days"] <= 30)
            & (df["order_count"] >= median_orders * 1.5)
            & (df["total_spend"] >= df["total_spend"].median()),
            (df["recency_days"] <= 45)
            & (df["order_count"] >= median_orders),
            (df["recency_days"] <= 30)
            & (df["order_count"] < median_orders),
            (df["recency_days"] >= inactive_days)
            & (df["order_count"] <= median_orders),
            df["recency_days"] <= 60,
        ],
        [
            "Champions",
            "Loyal Customers",
            "New Customers",
            "At Risk",
            "Recent Customers",
        ],
        default="Needs Nurturing",
    )

    reasons = []
    actions = []
    for row in df.itertuples(index=False):
        why = []
        if row.recency_days >= inactive_days:
            why.append(f"No purchase for {int(row.recency_days)} days (threshold: {inactive_days})")
        elif row.recency_days >= inactive_days * 0.6:
            why.append(f"Purchase inactivity is approaching the {inactive_days}-day threshold")
        if row.order_count <= median_orders:
            why.append("Purchase frequency is at or below the dataset median")
        if row.total_spend <= df["total_spend"].median():
            why.append("Historical spend is at or below the dataset median")
        if not why:
            why.append("Recent activity and purchase frequency look comparatively healthy")
        reasons.append("; ".join(why))

        if row.risk_level == "High":
            if row.recency_days >= inactive_days:
                actions.append("Prioritise a personalised win-back message; test a limited offer if margin allows")
            else:
                actions.append("Contact the customer, ask for feedback, and recommend a relevant product")
        elif row.risk_level == "Medium":
            actions.append("Send a timely reminder or tailored recommendation; monitor the next purchase")
        elif row.rfm_segment in ["Champions", "Loyal Customers"]:
            actions.append("Reward loyalty, request feedback, and invite a referral without over-discounting")
        elif row.rfm_segment == "New Customers":
            actions.append("Share onboarding tips and a helpful next-purchase suggestion")
        else:
            actions.append("Use a relevant content or product message and review engagement")

    df["risk_explanation"] = reasons
    df["recommended_action"] = actions
    df["risk_level"] = pd.Categorical(
        df["risk_level"], categories=["High", "Medium", "Low"], ordered=True
    )
    return df.sort_values(["churn_risk_score", "total_spend"], ascending=[False, False])


def style_plot(fig, height=340):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=C["cream2"], family="Inter, ui-sans-serif, system-ui, sans-serif"),
        title_font=dict(color=C["cream"], size=16),
        margin=dict(l=12, r=12, t=58, b=12),
        height=height,
        legend_title_text="",
    )
    fig.update_xaxes(gridcolor=C["grey"], zerolinecolor=C["grey"])
    fig.update_yaxes(gridcolor=C["grey"], zerolinecolor=C["grey"])
    return fig


def money(value):
    return f"${value:,.2f}"


# ---------------- Voice assistant helpers ----------------
def normalise_command(text):
    """Normalise English/Hindi voice or typed commands for simple intent matching."""
    text = str(text or "").strip().lower()
    text = re.sub(r"[?!.,;:]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def detect_navigation_command(query):
    q = normalise_command(query)
    commands = {
        "Overview": ["open dashboard", "show dashboard", "go to dashboard", "dashboard", "overview", "डैशबोर्ड खोलो", "डैशबोर्ड दिखाओ", "ओवरव्यू खोलो"],
        "Customer Explorer": ["customer explorer", "open customer explorer", "show customers", "customer details", "explore customers", "ग्राहक दिखाओ", "कस्टमर दिखाओ", "कस्टमर एक्सप्लोरर खोलो", "ग्राहक एक्सप्लोरर खोलो", "जोखिम वाले ग्राहक दिखाओ", "रिस्की ग्राहक दिखाओ"],
        "Retention Playbook": ["retention plan", "retention playbook", "open retention plan", "show retention plan", "retention recommendations", "रिटेंशन प्लान खोलो", "रिटेंशन प्लान दिखाओ", "ग्राहकों को रोकने के उपाय", "रिटेंशन सुझाव दिखाओ"],
        "About": ["open about", "about page", "about churnguard", "ऐप के बारे में", "अबाउट पेज खोलो"]
    }
    for page_name, phrases in commands.items():
        if any(normalise_command(phrase) in q for phrase in phrases):
            return page_name
    return None


def answer_customer_question(query, data, inactive_days, language="English"):
    """Answer supported questions from the live scored dataframe; never invent metrics."""
    q = normalise_command(query)
    hindi = language == "हिन्दी"
    if data is None or data.empty:
        return "डेटा उपलब्ध नहीं है।" if hindi else "There is no usable customer data to answer from."

    risk = data["risk_level"].astype(str)
    high = data[risk == "High"]
    medium = data[risk == "Medium"]
    low = data[risk == "Low"]
    total = int(data["customer_id"].nunique())
    avg_spend = float(data["total_spend"].mean())
    high_spend = float(high["total_spend"].sum())
    avg_recency = float(data["recency_days"].mean())

    asks_why = any(x in q for x in ["why", "reason", "explain", "क्यों", "कारण", "समझाओ"])
    asks_action = any(x in q for x in ["retain", "retention", "recommend", "action", "contact", "prioriti", "रोकने", "बचाने", "सुझाव", "क्या करना", "संपर्क", "पहले"])
    asks_segment = any(x in q for x in ["segment", "सेगमेंट", "किस समूह", "किस श्रेणी"])
    asks_avg = any(x in q for x in ["average", "avg", "औसत"])
    asks_spend = any(x in q for x in ["spend", "spent", "spending", "खर्च", "राशि", "पैसा"])
    asks_medium = any(x in q for x in ["medium", "मध्यम", "मीडियम"])
    asks_low = any(x in q for x in ["low risk", "low-risk", "कम जोखिम", "लो रिस्क"])
    asks_high = any(x in q for x in ["high", "high risk", "high-risk", "at risk", "risk", "जोखिम", "खतरे", "हाई रिस्क", "हाई-रिस्क"])
    asks_count = any(x in q for x in ["how many", "count", "number of", "कितने", "कितनी", "संख्या", "कितना"])

    if asks_why and any(x in q for x in ["customer", "ग्राहक", "कस्टमर"]):
        # If a customer ID is included, use it; otherwise explain the score methodology.
        match = re.search(r"cust[-_ ]?\d+", str(query), flags=re.I)
        if match:
            customer_id = match.group(0).replace(" ", "-").upper()
            row = data[data["customer_id"].astype(str).str.upper() == customer_id]
            if not row.empty:
                r = row.iloc[0]
                prefix = f"ग्राहक {r['customer_id']} का जोखिम स्कोर {r['churn_risk_score']:.1f}/100 है। " if hindi else f"Customer {r['customer_id']} has a heuristic risk score of {r['churn_risk_score']:.1f}/100. "
                return prefix + str(r["risk_explanation"])
        return ("स्कोर एक नियम-आधारित संकेतक है: हाल की खरीदारी/recency का 65%, frequency का 20% और historical spend का 15% योगदान है। यह प्रशिक्षित churn probability नहीं है।" if hindi else "The score is a rule-based indicator: recency contributes 65%, purchase frequency 20%, and historical spend 15%. It is not a trained churn probability.")

    if asks_action:
        if not high.empty:
            top = high.sort_values(["churn_risk_score", "total_spend"], ascending=[False, False]).head(5)
            ids = ", ".join(top["customer_id"].astype(str).tolist())
            return (f"पहले {len(high)} high-risk ग्राहकों की समीक्षा करें। सबसे पहले इन ग्राहकों से संपर्क करें: {ids}। व्यक्तिगत win-back संदेश भेजें, समस्या/फीडबैक पूछें और छूट देने से पहले margin जाँचें।" if hindi else f"Review the {len(high)} high-risk customers first. Start with: {ids}. Send a personalised win-back message, ask for feedback, and check margin before offering a discount.")
        return "कोई high-risk ग्राहक नहीं मिला।" if hindi else "No high-risk customers were found in the current data."

    if asks_segment:
        counts = data["rfm_segment"].value_counts()
        if counts.empty:
            return "सेगमेंट डेटा उपलब्ध नहीं है।" if hindi else "Segment data is unavailable."
        top_segment, count = str(counts.index[0]), int(counts.iloc[0])
        return (f"सबसे बड़ा सेगमेंट {top_segment} है, जिसमें {count} ग्राहक हैं। यह संख्या है, अपने-आप में churn का प्रमाण नहीं।" if hindi else f"The largest segment is {top_segment}, with {count} customers. Segment size alone does not prove churn risk.")

    if asks_avg and asks_spend:
        return (f"औसत historical customer spend {avg_spend:,.2f} है।" if hindi else f"Average historical customer spend is {avg_spend:,.2f}.")
    if asks_spend and asks_high:
        return (f"High-risk ग्राहकों से जुड़ा historical spend {high_spend:,.2f} है। यह भविष्य में होने वाले नुकसान का अनुमान नहीं है।" if hindi else f"Historical spend associated with high-risk customers is {high_spend:,.2f}. This is not a forecast of future lost revenue.")

    if asks_count:
        if asks_medium:
            label, count = "Medium", int(medium.shape[0])
        elif asks_low:
            label, count = "Low", int(low.shape[0])
        else:
            label, count = "High", int(high.shape[0])
        if hindi:
            hindi_label = {"High": "high-risk", "Medium": "medium-risk", "Low": "low-risk"}[label]
            return f"मौजूदा डेटा में {count} {hindi_label} ग्राहक हैं। कुल {total} ग्राहक विश्लेषित किए गए। जोखिम स्तर नियम-आधारित हैं, वास्तविक churn probability नहीं।"
        return f"There are {count} {label.lower()}-risk customers in the current data, out of {total} customers analysed. Risk bands are heuristic indicators, not actual churn probabilities."

    if any(x in q for x in ["recency", "inactive", "days since", "निष्क्रिय", "खरीदारी के दिन"]):
        return (f"औसतन पिछली खरीदारी को {avg_recency:.1f} दिन हुए हैं। वर्तमान inactivity threshold {inactive_days} दिन है।" if hindi else f"Average time since last purchase is {avg_recency:.1f} days. The current inactivity threshold is {inactive_days} days.")

    return ("मैं ग्राहक संख्या, high/medium/low risk, historical spend, औसत खर्च, सेगमेंट और retention actions के बारे में जवाब दे सकता हूँ। अपना सवाल थोड़ा और स्पष्ट करें।" if hindi else "I can answer questions about customer counts by risk level, historical spend, average spend, segments, recency, and retention actions. Please rephrase your question with a little more detail.")


def render_speech_player(text, language):
    """Render an explicit click-to-speak control to avoid repeated autoplay on reruns."""
    safe_text = json.dumps(str(text), ensure_ascii=False)
    lang_code = "hi-IN" if language == "हिन्दी" else "en-IN"
    components.html(f"""
      <div style="font-family:Arial,sans-serif;background:#1A1A1A;border:1px solid #8C8777;border-radius:10px;padding:10px;color:#FFFDEE;">
        <button id="speakBtn" style="background:#A8D83E;color:#101010;border:0;border-radius:8px;padding:9px 14px;cursor:pointer;font-weight:700;">🔊 Speak answer / जवाब सुनें</button>
        <span id="speechStatus" style="margin-left:10px;font-size:12px;color:#F4EFD9;"></span>
      </div>
      <script>
        const answerText = {safe_text};
        const langCode = {json.dumps(lang_code)};
        const btn = document.getElementById('speakBtn');
        const status = document.getElementById('speechStatus');
        btn.addEventListener('click', () => {{
          if (!('speechSynthesis' in window)) {{ status.textContent = 'Speech output is not supported in this browser.'; return; }}
          window.speechSynthesis.cancel();
          const utterance = new SpeechSynthesisUtterance(answerText);
          utterance.lang = langCode;
          utterance.rate = 0.95;
          utterance.onstart = () => status.textContent = 'Speaking…';
          utterance.onend = () => status.textContent = 'Finished';
          utterance.onerror = () => status.textContent = 'Could not play speech. Check browser settings.';
          window.speechSynthesis.speak(utterance);
        }});
      </script>
    """, height=75)


# ---------------- Sidebar ----------------
st.sidebar.markdown(f"## 🛡️ ChurnGuard <span style='color:{C['coral']}'>AI</span>", unsafe_allow_html=True)
st.sidebar.caption("Customer intelligence • Retention workspace")
PAGE_OPTIONS = ["Overview", "Customer Explorer", "Retention Playbook", "Profile", "About"]
if "pending_nav_page" in st.session_state:
    pending = st.session_state.pop("pending_nav_page")
    if pending in PAGE_OPTIONS:
        st.session_state["nav_page"] = pending
if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = "Overview"
PAGE_ICONS = {
    "Overview": "⌂",
    "Customer Explorer": "◎",
    "Retention Playbook": "✦",
    "Profile": "♙",
    "About": "ⓘ",
}
page = st.sidebar.radio(
    "Navigate",
    PAGE_OPTIONS,
    format_func=lambda item: f"{PAGE_ICONS.get(item, '•')}   {item}",
    key="nav_page",
    help="Choose a section. Hover over a navigation item to read its label.",
)
st.sidebar.divider()
inactive_days = st.sidebar.slider("Inactive customer threshold (days)", 30, 180, 90, 15)
st.sidebar.caption("Prototype mode · Risk scores are heuristic indicators, not trained churn probabilities.")

with st.sidebar.expander("📂 Use your own customer CSV", expanded=False):
    uploaded = st.file_uploader(
        "Upload CSV",
        type=["csv"],
        help="The uploaded file is processed in this local app session.",
    )
    st.caption("Required fields: customer ID, last purchase date, total spend, and order count.")

if "source_data" not in st.session_state:
    st.session_state.source_data = make_demo_data()
    st.session_state.source_name = "Synthetic demo dataset"

if uploaded is not None:
    try:
        candidate = pd.read_csv(uploaded)
        if candidate.empty:
            st.sidebar.error("That CSV has no rows.")
        else:
            st.session_state.source_data = candidate
            st.session_state.source_name = uploaded.name
    except Exception as exc:
        st.sidebar.error(f"Could not read CSV: {exc}")

raw = st.session_state.source_data.copy()
columns = list(raw.columns)

with st.sidebar.expander("⚙️ Map your CSV columns", expanded=uploaded is not None):
    if len(columns) < 1:
        st.error("The selected dataset has no columns.")
        st.stop()

    def choose_column(label, preferred, key):
        default_index = columns.index(preferred) if preferred in columns else 0
        return st.selectbox(label, columns, index=default_index, key=key)

    id_col = choose_column("Customer ID", "customer_id", "map_id")
    date_col = choose_column("Last purchase date", "last_purchase_date", "map_date")
    spend_col = choose_column("Total spend", "total_spend", "map_spend")
    freq_col = choose_column("Order count", "order_count", "map_freq")

scored = score_customers(raw, id_col, date_col, spend_col, freq_col, inactive_days)

# ---------------- Header toolbar / analysis question ----------------
# A compact top toolbar inspired by the supplied dashboard reference.
toolbar_spacer, toolbar_search, toolbar_profile = st.columns([0.02, 0.76, 0.22], vertical_alignment="center")
with toolbar_spacer:
    st.write("")
with toolbar_search:
    with st.form("header_analysis_question", clear_on_submit=False, border=False):
        ask_col, ask_button_col = st.columns([0.86, 0.14], vertical_alignment="center")
        with ask_col:
            header_question = st.text_input(
                "Ask about your analysis",
                placeholder="Ask about customers, risk signals, spend, segments, or retention…",
                label_visibility="collapsed",
                key="header_question_input",
            )
        with ask_button_col:
            header_ask_submitted = st.form_submit_button("Ask ↗", use_container_width=True)
with toolbar_profile:
    profile_cols = st.columns([0.75, 1.05, 0.65], vertical_alignment="center")
    with profile_cols[0]:
        with st.popover("♧", help="Notifications"):
            st.markdown("**Notifications**")
            st.caption("You're all caught up. Analysis answers are generated from the current dataset.")
    with profile_cols[1]:
        with st.popover("Workspace", help="Workspace details"):
            st.markdown("**ChurnGuard AI workspace**")
            st.caption(f"Dataset: {st.session_state.get('source_name', 'Current dataset')}")
            st.caption("Mode: local prototype")
    with profile_cols[2]:
        profile = st.session_state["local_profile"]
        initials = "".join(part[0] for part in profile.get("name", "AK").split()[:2]).upper() or "AK"
        with st.popover(initials[:3], help="Open your profile settings"):
            avatar_b64 = profile.get("avatar_b64", "")
            if avatar_b64:
                try:
                    st.image(base64.b64decode(avatar_b64), width=76)
                except Exception:
                    st.caption("Profile avatar")
            st.markdown(f"**{profile.get('name') or 'Your profile'}**")
            st.caption(profile.get("workspace") or "Local workspace")
            st.caption("Profile details are saved locally on this computer.")
            if st.button("Edit profile ↗", key="open_profile_page", use_container_width=True):
                st.session_state["pending_nav_page"] = "Profile"
                st.rerun()

# ---------------- Header ----------------
st.markdown(
    f"""
    <div class="hero">
      <div class="eyebrow">CUSTOMER INTELLIGENCE · SCIENTIFIC EDITION</div>
      <h1 style="margin:.25rem 0 .3rem 0;color:{C['cream']};">
        ChurnGuard <span style="color:{C['lime']};">AI</span>
      </h1>
      <p>Understand customer behaviour. Surface retention signals. Make evidence-aware decisions.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if scored.empty:
    st.error("No usable rows found. Check the mapped customer ID and purchase date columns.")
    st.info("The CSV must contain valid customer IDs and parseable last-purchase dates.")
    st.stop()

if header_ask_submitted:
    if not str(header_question or "").strip():
        st.warning("Type a question about the current analysis first.")
    else:
        header_answer = answer_customer_question(header_question, scored, inactive_days, "English")
        st.session_state["header_analysis_answer"] = header_answer
        st.session_state["header_analysis_question_text"] = header_question

if st.session_state.get("header_analysis_answer"):
    with st.container(border=True):
        answer_head_left, answer_head_right = st.columns([0.85, 0.15], vertical_alignment="center")
        with answer_head_left:
            st.markdown("**✦ Analysis assistant**")
            st.caption(f"Question: {st.session_state.get('header_analysis_question_text', '')}")
        with answer_head_right:
            if st.button("Clear ×", key="clear_header_answer"):
                st.session_state.pop("header_analysis_answer", None)
                st.session_state.pop("header_analysis_question_text", None)
                st.rerun()
        st.write(st.session_state["header_analysis_answer"])
        st.caption("Answers are generated from the current dataset using built-in rules; no external AI API is connected.")

# ---------------- Voice assistant ----------------
with st.expander("🎙️ Voice Assistant | English + हिन्दी", expanded=False):
    st.markdown("Ask about your current customer data, or use a voice command to navigate the app.")
    voice_language = st.selectbox("Assistant language / सहायक की भाषा", ["English", "हिन्दी"], key="voice_language")
    language_code = "hi-IN" if voice_language == "हिन्दी" else "en-IN"
    st.caption("Microphone support depends on your browser and microphone permissions. Text input is always available.")

    spoken_query = ""
    if MIC_RECORDER_AVAILABLE:
        try:
            spoken_query = speech_to_text(
                language=language_code,
                start_prompt="🎤 Start speaking" if voice_language == "English" else "🎤 बोलना शुरू करें",
                stop_prompt="⏹️ Stop recording" if voice_language == "English" else "⏹️ रिकॉर्डिंग रोकें",
                just_once=True,
                key=f"voice_mic_{language_code}",
            ) or ""
        except Exception as exc:
            st.warning(f"Microphone input is unavailable right now. Use the text box below. Details: {exc}")
    else:
        st.info("Optional microphone package is not installed. Text questions still work. Install `streamlit-mic-recorder` to enable microphone input.")

    with st.form("voice_question_form", clear_on_submit=False):
        typed_query = st.text_input(
            "Your question or command" if voice_language == "English" else "अपना सवाल या कमांड लिखें",
            value="",
            placeholder="e.g. How many customers are at high risk?" if voice_language == "English" else "उदाहरण: कितने ग्राहक high risk में हैं?",
        )
        submitted = st.form_submit_button("Ask / पूछें")

    query_to_process = typed_query.strip() if submitted and typed_query.strip() else (str(spoken_query).strip() if spoken_query else "")
    if submitted or spoken_query:
        if not query_to_process:
            st.warning("Please enter a question or use the microphone.")
        else:
            target_page = detect_navigation_command(query_to_process)
            if target_page:
                st.session_state["pending_nav_page"] = target_page
                response = (f"पेज खोला जा रहा है: {target_page}" if voice_language == "हिन्दी" else f"Opening page: {target_page}")
                st.session_state["voice_answer"] = response
                st.session_state["voice_answer_language"] = voice_language
                st.rerun()
            else:
                response = answer_customer_question(query_to_process, scored, inactive_days, voice_language)
                st.session_state["voice_answer"] = response
                st.session_state["voice_answer_language"] = voice_language

    if st.session_state.get("voice_answer"):
        st.markdown("#### Assistant response / सहायक का जवाब")
        st.markdown(f"<div class='panel'>{html.escape(str(st.session_state['voice_answer']))}</div>", unsafe_allow_html=True)
        render_speech_player(st.session_state["voice_answer"], st.session_state.get("voice_answer_language", voice_language))

# ---------------- Pages ----------------
if page == "Overview":
    st.caption(f"Data source: **{st.session_state.source_name}** · {len(scored):,} usable rows")
    st.caption("Scientific note: the current 0–100 score is a transparent heuristic, not a churn probability. A probability model requires historical churn labels and out-of-sample validation.")
    total_customers = int(scored["customer_id"].nunique())
    high_risk = int((scored["risk_level"] == "High").sum())
    risk_rate = high_risk / max(len(scored), 1) * 100
    revenue_at_risk = float(scored.loc[scored["risk_level"] == "High", "total_spend"].sum())
    avg_spend = float(scored["total_spend"].mean())

    c1, c2, c3, c4 = st.columns([1, 1, 1.25, 1])
    c1.metric("CUSTOMERS ANALYSED", f"{total_customers:,}")
    c2.metric("HIGH-RISK SIGNALS", f"{high_risk:,}", f"{risk_rate:.1f}% of rows")
    c3.metric("HISTORICAL SPEND · HIGH RISK", money(revenue_at_risk))
    c4.metric("AVERAGE SPEND", money(avg_spend))

    st.markdown("### Activity overview")
    main_col, side_col = st.columns([1.55, 1], gap="medium")
    with main_col:
        st.markdown("<div class='panel'><span class='eyebrow'>01 / RISK DISTRIBUTION</span><br><b>Customer health signals</b></div>", unsafe_allow_html=True)
        risk_counts = (
            scored["risk_level"].astype(str).value_counts()
            .reindex(["Low", "Medium", "High"], fill_value=0)
            .rename_axis("Risk level").reset_index(name="Customers")
        )
        fig = px.bar(
            risk_counts, x="Risk level", y="Customers", color="Risk level",
            color_discrete_map=RISK_COLORS, text="Customers",
            category_orders={"Risk level": ["Low", "Medium", "High"]},
        )
        fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0, opacity=.95)
        fig.update_layout(showlegend=False, bargap=.42, margin=dict(l=8, r=8, t=15, b=8), xaxis_title=None, yaxis_title=None)
        style_plot(fig, height=275)
        fig.update_xaxes(showgrid=False, tickfont=dict(size=11))
        fig.update_yaxes(showgrid=True, gridcolor="#292929", zeroline=False)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        st.markdown("<div class='note'> <b>Reading the signal</b><br>Risk bands are transparent rule-based indicators, not calibrated churn probabilities.</div>", unsafe_allow_html=True)
    with side_col:
        st.markdown("<div class='panel'><span class='eyebrow'>02 / CUSTOMER MIX</span><br><b>RFM-style segments</b></div>", unsafe_allow_html=True)
        seg = scored["rfm_segment"].value_counts().rename_axis("Segment").reset_index(name="Customers")
        seg_colors = {**SEGMENT_COLORS, "Champions": C["lime"], "At Risk": C["orange"], "Loyal Customers": C["coral"]}
        fig2 = px.pie(seg, names="Segment", values="Customers", hole=0.68, color="Segment", color_discrete_map=seg_colors)
        fig2.update_traces(textposition="inside", textinfo="percent", marker=dict(line=dict(color=C["black"], width=2)), hole=.68)
        fig2.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="top", y=-.08, xanchor="left", x=0, font=dict(size=10)), margin=dict(l=5, r=5, t=10, b=48))
        style_plot(fig2, height=275)
        st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})
        segment_counts = scored["rfm_segment"].value_counts()
        top_segment = str(segment_counts.index[0]) if not segment_counts.empty else "—"
        top_count = int(segment_counts.iloc[0]) if not segment_counts.empty else 0
        st.markdown(f"<div class='note'><span class='eyebrow'>LARGEST SEGMENT</span><br><b style='font-size:1.35rem;color:{C['lime']};'>{html.escape(top_segment)}</b><br>{top_count:,} customers in this group</div>", unsafe_allow_html=True)

    st.markdown("### 🚨 Customers to review first")
    st.caption("Sorted by heuristic risk score. Use the explanation and action as decision support, not as certainty.")
    display_cols = [
        "customer_id", "recency_days", "order_count", "total_spend",
        "churn_risk_score", "risk_level", "rfm_segment", "recommended_action",
    ]
    st.dataframe(scored[display_cols].head(8), width="stretch", hide_index=True)
    st.caption(
        "Metric note: historical spend of high-risk customers is the sum of their recorded spend. "
        "It is not a forecast of future lost revenue. Demo records are synthetic."
    )

    # Compact risk-score distribution
    with st.expander("How is the risk score calculated?"):
        st.markdown(
            "- **65% recency component:** more days since the last purchase increases the score.\n"
            "- **20% frequency component:** lower order counts compared with the dataset's 90th percentile increase the score.\n"
            "- **15% monetary component:** lower historical spend compared with the dataset's 90th percentile increases the score.\n\n"
            "A customer is also marked High when their inactivity reaches the selected threshold. "
            "This is a transparent heuristic, not a trained or validated churn model."
        )

elif page == "Customer Explorer":
    st.markdown("### Customer Explorer")
    st.caption("Filter the dataset, select a customer, and inspect the drivers behind their heuristic risk score.")

    q1, q2, q3 = st.columns([1, 1.2, 1.2])
    with q1:
        risk_filter = st.multiselect(
            "Risk level", ["High", "Medium", "Low"],
            default=["High", "Medium", "Low"],
        )
    with q2:
        segment_options = sorted(scored["rfm_segment"].dropna().unique().tolist())
        segment_filter = st.multiselect(
            "RFM-style segment", segment_options, default=segment_options
        )
    with q3:
        min_spend = float(scored["total_spend"].min())
        max_spend = float(scored["total_spend"].max())
        if max_spend <= min_spend:
            spend_range = (min_spend, max_spend)
            st.caption(f"Spend: {money(min_spend)}")
        else:
            spend_range = st.slider(
                "Historical spend range",
                min_value=min_spend,
                max_value=max_spend,
                value=(min_spend, max_spend),
            )

    filtered = scored[
        scored["risk_level"].astype(str).isin(risk_filter)
        & scored["rfm_segment"].isin(segment_filter)
        & scored["total_spend"].between(spend_range[0], spend_range[1])
    ].copy()

    st.write(f"Showing **{len(filtered):,}** customers")
    if filtered.empty:
        st.warning("No customers match those filters. Try selecting more risk levels or segments.")
    else:
        st.dataframe(
            filtered[
                ["customer_id", "recency_days", "order_count", "total_spend",
                 "churn_risk_score", "risk_level", "rfm_segment"]
            ],
            width="stretch",
            hide_index=True,
        )

        customer_ids = filtered["customer_id"].astype(str).tolist()
        selected_id = st.selectbox("Inspect a customer", customer_ids, key="selected_customer")
        selected = filtered[filtered["customer_id"].astype(str) == selected_id].iloc[0]

        st.markdown("---")
        st.markdown(f"### Customer intelligence · `{selected_id}`")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Risk score", f"{selected['churn_risk_score']:.1f}/100")
        m2.metric("Risk band", str(selected["risk_level"]))
        m3.metric("Days since purchase", f"{int(selected['recency_days'])}")
        m4.metric("Historical spend", money(float(selected["total_spend"])))

        details_left, details_right = st.columns([1, 1.2])
        with details_left:
            st.markdown("#### Risk score components")
            component_df = pd.DataFrame({
                "Component": ["Recency (65%)", "Frequency (20%)", "Monetary (15%)"],
                "Score contribution": [
                    float(selected["risk_recency_component"]),
                    float(selected["risk_frequency_component"]),
                    float(selected["risk_monetary_component"]),
                ],
            })
            component_fig = px.bar(
                component_df, x="Score contribution", y="Component", orientation="h",
                text="Score contribution",
                color="Component",
                color_discrete_map={
                    "Recency (65%)": C["orange"],
                    "Frequency (20%)": C["coral"],
                    "Monetary (15%)": C["taupe"],
                },
                title="Contribution to 0–100 heuristic score",
            )
            component_fig.update_traces(texttemplate="%{text:.1f}", textposition="outside", cliponaxis=False)
            component_fig.update_layout(showlegend=False)
            style_plot(component_fig, height=260)
            st.plotly_chart(component_fig, width="stretch")
        with details_right:
            st.markdown("#### Why this customer was flagged")
            st.markdown(f"<div class='panel'>{selected['risk_explanation']}</div>", unsafe_allow_html=True)
            st.markdown("#### Recommended next action")
            st.markdown(
                f"<div class='panel'><span style='color:{C['coral']};font-weight:800;'>NEXT BEST ACTION</span><br><br>"
                f"{selected['recommended_action']}</div>",
                unsafe_allow_html=True,
            )
            st.caption("Recommendation is rule-based in this prototype. Validate offers with controlled experiments.")

        # Display optional extra fields from the uploaded dataset for this selected customer.
        extra_cols = [
            col for col in raw.columns
            if col not in {id_col, date_col, spend_col, freq_col}
        ]
        if extra_cols:
            st.markdown("#### Additional customer details")
            original_id = selected["customer_id"]
            matching = raw[raw[id_col].astype(str) == str(original_id)]
            if not matching.empty:
                st.dataframe(matching[extra_cols].head(1), width="stretch", hide_index=True)

    st.markdown("---")
    st.markdown("#### Export filtered customers")
    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download filtered customer analysis (CSV)",
        data=csv_bytes,
        file_name="churnguard_customer_analysis.csv",
        mime="text/csv",
    )

elif page == "Retention Playbook":
    st.markdown("### Retention Playbook")
    st.write("Practical actions based on the current heuristic segments. Test interventions and measure their incremental impact.")
    playbook = pd.DataFrame([
        {
            "Priority": "P1 · Urgent",
            "Who": f"High risk or inactive for {inactive_days}+ days",
            "Suggested action": "Personalised win-back message; ask for feedback before offering a discount.",
            "Measure": "Reactivation rate and incremental margin",
        },
        {
            "Priority": "P2 · Nurture",
            "Who": "Medium risk or weakening engagement",
            "Suggested action": "Send a relevant product recommendation or reminder; reduce purchase friction.",
            "Measure": "Repeat-purchase rate within 30 days",
        },
        {
            "Priority": "P3 · Grow",
            "Who": "Champions and loyal customers",
            "Suggested action": "Recognise loyalty, request feedback, and invite referrals without over-discounting.",
            "Measure": "Repeat orders, referral conversion, and margin",
        },
        {
            "Priority": "P4 · Onboard",
            "Who": "New customers with few purchases",
            "Suggested action": "Share useful onboarding content and a tailored next-purchase suggestion.",
            "Measure": "Second-purchase conversion",
        },
    ])
    st.dataframe(playbook, width="stretch", hide_index=True)

    high = scored[scored["risk_level"].astype(str) == "High"]
    if not high.empty:
        st.markdown("#### Suggested outreach queue")
        queue_cols = [
            "customer_id", "recency_days", "order_count", "total_spend",
            "churn_risk_score", "risk_explanation", "recommended_action",
        ]
        st.dataframe(high[queue_cols].head(15), width="stretch", hide_index=True)
        queue_csv = high[queue_cols].to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download high-risk outreach queue",
            data=queue_csv,
            file_name="churnguard_outreach_queue.csv",
            mime="text/csv",
        )

    st.info(
        "Model-generated explanations are not connected yet. This playbook and voice Q&A use transparent code-based rules; "
        "the optional Nebius Token Factory / NVIDIA model integration can be added after API access is available."
    )

elif page == "Profile":
    profile = st.session_state["local_profile"]
    st.markdown("### Your profile")
    st.caption("A local profile for this project workspace. It is not a public account and is not synced to the cloud.")
    avatar_col, avatar_info = st.columns([0.22, 0.78], vertical_alignment="center")
    with avatar_col:
        if profile.get("avatar_b64"):
            try:
                st.image(base64.b64decode(profile["avatar_b64"]), width=132)
            except Exception:
                st.markdown("<div class='panel'>👤</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='panel' style='text-align:center;font-size:2.5rem'>👤</div>", unsafe_allow_html=True)
    with avatar_info:
        st.markdown(f"#### {html.escape(profile.get('name') or 'Your name')}")
        st.write(profile.get("tagline") or "Add a tagline to introduce yourself.")
        st.caption("PNG or JPEG avatar · up to 2 MB")

    tab_profile, tab_bio, tab_qual, tab_settings = st.tabs(["Profile", "Biography", "Qualifications", "Settings"])
    with tab_profile:
        avatar_file = st.file_uploader("Upload an avatar", type=["png", "jpg", "jpeg"], key="profile_avatar_upload", help="Maximum size: 2 MB")
        if avatar_file is not None:
            if avatar_file.size > 2 * 1024 * 1024:
                st.error("Please choose an image smaller than 2 MB.")
            else:
                profile["avatar_b64"] = base64.b64encode(avatar_file.getvalue()).decode("ascii")
                st.session_state["local_profile"] = profile
                st.image(avatar_file, width=96, caption="New avatar preview")
        with st.form("profile_details_form"):
            name = st.text_input("Name", value=profile.get("name", ""), max_chars=80)
            tagline = st.text_input("Tagline", value=profile.get("tagline", ""), max_chars=160)
            email = st.text_input("Email", value=profile.get("email", ""), max_chars=160)
            phone = st.text_input("Phone number", value=profile.get("phone", ""), max_chars=40)
            website = st.text_input("Website", value=profile.get("website", ""), max_chars=200)
            github = st.text_input("GitHub username", value=profile.get("github", ""), max_chars=80)
            save_profile = st.form_submit_button("Save profile changes", use_container_width=True)
        if save_profile:
            if not name.strip():
                st.error("Please enter a name before saving.")
            else:
                profile.update({"name": name.strip(), "tagline": tagline.strip(), "email": email.strip(), "phone": phone.strip(), "website": website.strip(), "github": github.strip()})
                st.session_state["local_profile"] = profile
                try:
                    save_local_profile(profile)
                    st.success("Profile saved on this computer.")
                    st.rerun()
                except OSError as exc:
                    st.error(f"Could not save the local profile file: {exc}")
    with tab_bio:
        with st.form("profile_bio_form"):
            biography = st.text_area("Biography", value=profile.get("biography", ""), height=180, placeholder="Tell people what you are learning or building…")
            save_bio = st.form_submit_button("Save biography", use_container_width=True)
        if save_bio:
            profile["biography"] = biography.strip()
            st.session_state["local_profile"] = profile
            try:
                save_local_profile(profile)
                st.success("Biography saved.")
            except OSError as exc:
                st.error(f"Could not save: {exc}")
    with tab_qual:
        with st.form("profile_qual_form"):
            education = st.text_area("Education", value=profile.get("education", ""), height=100, placeholder="Course, institution, or relevant learning…")
            skills = st.text_area("Skills and interests", value=profile.get("skills", ""), height=100, placeholder="Python, data analysis, scientific computing…")
            save_qual = st.form_submit_button("Save qualifications", use_container_width=True)
        if save_qual:
            profile.update({"education": education.strip(), "skills": skills.strip()})
            st.session_state["local_profile"] = profile
            try:
                save_local_profile(profile)
                st.success("Qualifications saved.")
            except OSError as exc:
                st.error(f"Could not save: {exc}")
    with tab_settings:
        with st.form("profile_settings_form"):
            workspace = st.text_input("Workspace name", value=profile.get("workspace", "ChurnGuard AI"), max_chars=100)
            st.caption("Your details are stored in churnguard_profile.json beside the Python app. No password or login is created.")
            save_settings = st.form_submit_button("Save workspace settings", use_container_width=True)
        if save_settings:
            profile["workspace"] = workspace.strip() or "ChurnGuard AI"
            st.session_state["local_profile"] = profile
            try:
                save_local_profile(profile)
                st.success("Workspace settings saved.")
            except OSError as exc:
                st.error(f"Could not save: {exc}")

else:
    st.markdown("### About ChurnGuard AI")
    st.markdown(
        """
        **ChurnGuard AI** is a customer-retention prototype designed to help teams prioritise outreach,
        understand customer activity, and choose measurable retention actions.
        """
    )
    st.markdown("#### Current capabilities")
    st.markdown(
        "- Upload a customer CSV and map its columns.\n"
        "- Calculate recency, frequency, monetary value, and a transparent heuristic risk score.\n"
        "- Segment customers using RFM-style rules.\n"
        "- Inspect customer-level risk contributors, explanations, and suggested actions.\n"
        "- Filter and export customer analyses and high-risk outreach queues.\n"
        "- Ask basic customer-data questions in English or Hindi using the voice assistant.\n"
        "- Navigate supported pages with English/Hindi commands when recognised by the assistant."
    )
    st.markdown("#### Important limitations")
    st.markdown(
        "- The score is a heuristic, not a trained or validated churn-probability model.\n"
        "- Historical spend of high-risk customers is not a prediction of future lost revenue.\n"
        "- The built-in demo data is synthetic.\n"
        "- Voice recognition depends on browser support and microphone permissions; text input is the fallback.\n"
        "- Nebius Token Factory / NVIDIA model integration is not connected yet; answers currently use deterministic Python rules."
    )
    st.markdown(
        f"<div class='note'>Built for the Nebius × NVIDIA Global AI Hackathon 2026 · Prototype stage</div>",
        unsafe_allow_html=True,
    )

st.divider()
st.caption(
    "ChurnGuard AI · Prototype build · Use risk scores and recommendations as decision support, not certainty."
)
