import pandas as pd
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# ---- Load data ----
file_path = "/home/king/projects/BI010875_MCA/Data_files/BI010875 MCA Analysis DATA MASTER v0.1.xlsx"
df = pd.read_excel(file_path, sheet_name="DATA", header=3)

# ---- Drop first unnamed column if exists ----
if df.columns[0].startswith("Unnamed"):
    df = df.drop(columns=[df.columns[0]])

# ---- Drop non-analytic fields ----
df = df.drop(columns=[
    "careepisodeID", "ChiefComplaint", "MechanismDetail",
    "ImpressionSuspectedDiagnosis"
], errors="ignore")

# ---- Parse IncidentDate fallback from incident number ----
def build_date_from_incident_number(incident_number):
    if pd.isna(incident_number):
        return pd.NaT
    if isinstance(incident_number, str) and incident_number.startswith("S") and len(incident_number) >= 7:
        yymmdd = incident_number[1:7]
        try:
            return pd.to_datetime(yymmdd, format="%y%m%d", errors="coerce")
        except:
            return pd.NaT
    return pd.NaT

if "IncidentDate" in df.columns and "IJD_IncidentNumber" in df.columns:
    mask_missing = df["IncidentDate"].isna()
    df.loc[mask_missing, "IncidentDate"] = df.loc[mask_missing, "IJD_IncidentNumber"].apply(build_date_from_incident_number)

# ---- Replace NaN with 'NotRecorded' ----
df = df.fillna("NotRecorded")

# ---- Questions & labels ----
questions = [
    "Mental Capacity Assessment Undertaken",
    "Patient Does Have Capacity",
    "Does the patient have an impairment or, a disturbance in the functioning of, their mind or brain at the moment?",
    "Is the impairment or disturbance suffcient that the person lacks the capaity to make the decision at this time?",
    "Does the patient understand the information relevant to the decision including the likely consequances...?",
    "Can the patient retain that information?",
    "Can the patient use or weigh that information as part of the process of making the decision?",
    "Can the patient communicate that decision by any means?",
    "Proposed Care Patient Best Interest",
    "Service Outcome"
]
for q in questions:
    df[q] = df[q].replace(["", " "], "NotRecorded")

question_labels = {q: f"Q{i+1}" for i, q in enumerate(questions)}

answer_colors = {"Yes": "lightgreen", "No": "lightcoral", "NotRecorded": "lightgray"}

# ---- Title & overall date range ----
st.title("Interactive Mental Capacity Assessment Analysis")
if "IncidentDate" in df.columns:
    valid_dates = pd.to_datetime(df["IncidentDate"], errors="coerce").dropna()
    if not valid_dates.empty:
        st.markdown(f"**Records between {valid_dates.min().date():%d %b %Y} and {valid_dates.max().date():%d %b %Y}**")

# ---- Sidebar Filters ----
st.sidebar.header("Filters")
filters = {}
for q in questions:
    options = df[q].dropna().unique().tolist()
    filters[q] = st.sidebar.multiselect(f"{question_labels[q]}: {q}", options, default=options)

if "Operational Node" in df.columns:
    op_nodes = df["Operational Node"].dropna().unique().tolist()
    selected_nodes = st.sidebar.multiselect("Operational Node", op_nodes, default=op_nodes)

# ---- Apply filters ----
df_filtered = df.copy()
for q, selected in filters.items():
    df_filtered = df_filtered[df_filtered[q].isin(selected)]
if "Operational Node" in df.columns:
    df_filtered = df_filtered[df_filtered["Operational Node"].isin(selected_nodes)]

# ---- Records per Month ----
if "IncidentDate" in df_filtered.columns:
    df_filtered["YearMonth"] = df_filtered["IncidentDate"].dt.to_period("M")
    records_per_month = df_filtered.groupby("YearMonth").size().reset_index(name="Records")
    records_per_month["YearMonth"] = records_per_month["YearMonth"].dt.strftime("%b %Y")
    st.subheader("Records per Month (Filtered)")
    st.table(records_per_month.reset_index(drop=True))

# ---- Totals per question (exclude Q10) ----
table_questions = [q for q in questions if q != "Service Outcome"]

totals = {q: df_filtered[q].value_counts().to_dict() for q in table_questions}
answers = sorted({ans for q in table_questions for ans in df_filtered[q].unique()})
totals_table = []
for ans in answers:
    row = {"Answer": ans}
    for q in table_questions:
        row[question_labels[q]] = int(totals[q].get(ans, 0))
    totals_table.append(row)
totals_df = pd.DataFrame(totals_table)

# ---- HTML table with line breaks and coloring ----
html = """
<style>
.table-container { overflow-x:auto; margin-bottom:20px; }
table.custom { border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size:12px; text-align:center; }
table.custom th, table.custom td { border: 1px solid #ccc; padding:5px; }
table.custom th { white-space: normal; word-wrap: break-word; }
</style>
<div class="table-container">
<table class="custom">
  <tr>
    <th>Answer</th>
"""
for q in table_questions:
    html += f"<th>{question_labels[q]}<br>{q}</th>"
html += "</tr>"

for _, row in totals_df.iterrows():
    ans = row["Answer"]
    html += f"<tr><td>{ans}</td>"
    for q in table_questions:
        val = row[question_labels[q]]
        color = answer_colors.get(ans, "white")
        html += f"<td style='background-color:{color}'>{val}</td>"
    html += "</tr>"

html += "</table></div>"

st.subheader("Totals per Question (Filtered)")
st.markdown(html, unsafe_allow_html=True)

# ---- Q10 Table ('Service Outcome') ----
q10 = "Service Outcome"
totals_q10 = df_filtered[q10].value_counts().to_dict()
answers_q10 = sorted(df_filtered[q10].unique())

totals_table_q10 = []
for ans in answers_q10:
    row = {"Answer": ans, question_labels[q10]: int(totals_q10.get(ans, 0))}
    totals_table_q10.append(row)
totals_df_q10 = pd.DataFrame(totals_table_q10)

# ---- Q10 Table ('Service Outcome') ----
q10 = "Service Outcome"
totals_q10 = df_filtered[q10].value_counts().to_dict()
answers_q10 = sorted(df_filtered[q10].unique())

totals_table_q10 = []
for ans in answers_q10:
    row = {"Answer": ans, question_labels[q10]: int(totals_q10.get(ans, 0))}
    totals_table_q10.append(row)
totals_df_q10 = pd.DataFrame(totals_table_q10)

# ---- Q10 Table Transposed ('Service Outcome') ----
q10 = "Service Outcome"
totals_q10 = df_filtered[q10].value_counts().to_dict()
answers_q10 = sorted(df_filtered[q10].unique())

# ---- HTML table for Q10 (transposed) ----
html_q10 = f"""
<style>
.table-container {{ overflow-x:auto; margin-bottom:20px; }}
table.custom {{ border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size:12px; text-align:center; }}
table.custom th, table.custom td {{ border: 1px solid #ccc; padding:5px; }}
table.custom th {{ white-space: normal; word-wrap: break-word; }}
</style>
<div class="table-container">
<table class="custom">
  <tr>
    <th>{question_labels[q10]}<br>{q10}</th>
"""
# Add headers for each answer
for ans in answers_q10:
    html_q10 += f"<th>{ans}</th>"
html_q10 += "</tr>"

# Add counts row
html_q10 += "<tr>"
html_q10 += "<td>Count</td>"
for ans in answers_q10:
    val = totals_q10.get(ans, 0)
    color = answer_colors.get(ans, "white")
    html_q10 += f"<td style='background-color:{color}'>{val}</td>"
html_q10 += "</tr>"

html_q10 += "</table></div>"

st.subheader("Q10 Service Outcome (Filtered)")
st.markdown(html_q10, unsafe_allow_html=True)

# ---- Sankey chart with counts in node labels, keeping formatting ----
node_labels, node_map, node_colors = [], {}, []

# Precompute counts per question/answer
# ---- Function to format counts like 1.2k ----
def human_format(num):
    """Format number like 1.2k, 3.4M, etc."""
    num = int(num)
    if num >= 1_000_000_000:
        return f"{num/1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}k"
    else:
        return str(num)

counts_per_q = {q: df_filtered[q].value_counts().to_dict() for q in questions}

for q in questions:
    for ans in df_filtered[q].unique():
        count = counts_per_q[q].get(ans, 0)
        label = f"<span style='font-family:Arial; color:white'>{question_labels[q]}<br>{ans} - {human_format(count)}</span>"
        node_map[(q, ans)] = len(node_labels)
        node_labels.append(label)
        node_colors.append("lightblue")  # light blue nodes (the questions)

sources, targets, values, link_colors = [], [], [], []
for i in range(len(questions)-1):
    q_from, q_to = questions[i], questions[i+1]
    counts = df_filtered.groupby([q_from, q_to]).size().reset_index(name='count')
    for _, row in counts.iterrows():
        sources.append(node_map[(q_from, row[q_from])])
        targets.append(node_map[(q_to, row[q_to])])
        values.append(row['count'])
        link_colors.append(answer_colors.get(row[q_from], "lightblue"))

fig = go.Figure(go.Sankey(
    node=dict(label=node_labels, color=node_colors, pad=10, thickness=40, line=dict(color='white', width=0)),
    link=dict(source=sources, target=targets, value=values, color=link_colors, hovertemplate='%{value} records<extra></extra>'),
    domain=dict(x=[0,1], y=[0,1])
))
fig.update_layout(  title_text="Patient Flow Sankey Chart", title_x=0.5,
                    width=1200, height=800, margin=dict(l=20,r=20,t=100,b=20),
                    font=dict(family="Arial", size=12, color="black"))
st.plotly_chart(fig, use_container_width=True)

