import pandas as pd
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# ---- Load your data ----
file_path = "/home/king/projects/BI010875_MCA/Data_files/BI010875 MCA Analysis DATA MASTER v0.1.xlsx"
df = pd.read_excel(file_path, sheet_name="Sheet1", header=3)

# ---- Drop non-analytic fields ----
df = df.drop(columns=[
    "careepisodeID", "IncidentDate", "IJD_IncidentNumber", 
    "ChiefComplaint", "MechanismDetail", 
    "ImpressionSuspectedDiagnosis"
], errors="ignore")

# Replace NaN with 'NotRecorded'
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
    "proposedCarePatientBestInterest",
    "Service Outcome"
]

# Ensure all blanks/empty strings in question columns are set to 'NotRecorded'
for q in questions:
    df[q] = df[q].replace(["", " "], "NotRecorded")
    
question_labels = {q: f"Q{i+1}" for i, q in enumerate(questions)}

answer_colors = {
    "Yes": "lightgreen",
    "No": "lightcoral",
    "Not recorded": "lightgray",
    "NaN": "lightgray"
}

st.title("Interactive Patient Flow Sankey")


# -----------------------
# Two-column layout
# -----------------------
col_filters, col_chart = st.columns([1, 3])

# -----------------------
# Filters
# -----------------------
filters = {}
with col_filters:
    st.header("Filters")
    for q in questions:
        options = df[q].dropna().unique().tolist()
        filters[q] = st.multiselect(f"{question_labels[q]}: {q}", options, default=options)

# -----------------------
# Filter dataframe
# -----------------------
df_filtered = df.copy()
for q, selected in filters.items():
    df_filtered = df_filtered[df_filtered[q].isin(selected)]

# -----------------------
# Compute totals per question
# -----------------------
totals = {q: df_filtered[q].value_counts().to_dict() for q in questions}

# -----------------------
# Sankey chart and table in right column
# -----------------------
with col_chart:
    st.header("Filtered Data Summary")

    # ---- Totals table transposed ----
    answers = sorted({ans for q in questions for ans in df[q].unique()})
    totals_table = []
    for ans in answers:
        row = {"Answer": ans}
        for q in questions:
            row[question_labels[q]] = int(totals[q].get(ans, 0) or 0)
        totals_table.append(row)

    totals_df = pd.DataFrame(totals_table)

    # ---- Show table ----
    st.subheader("Totals per Question (Filtered, Transposed)")
    st.table(totals_df)

    # ---- Sankey chart ----
    node_labels = []
    node_map = {}
    node_colors = []

    for q in questions:
        for ans in df_filtered[q].unique():
            label = f"<span style='font-family:Arial; color:white'>{question_labels[q]}<br>{ans}</span>"
            node_map[(q, ans)] = len(node_labels)
            node_labels.append(label)
            node_colors.append("lightgray")  # grey nodes

    sources, targets, values, link_colors = [], [], [], []

    for i in range(len(questions)-1):
        q_from = questions[i]
        q_to = questions[i+1]
        counts = df_filtered.groupby([q_from, q_to]).size().reset_index(name='count')
        for _, row in counts.iterrows():
            sources.append(node_map[(q_from, row[q_from])])
            targets.append(node_map[(q_to, row[q_to])])
            values.append(row['count'])
            link_colors.append(answer_colors.get(row[q_from], "lightblue"))

    fig = go.Figure(go.Sankey(
        node=dict(
            label=node_labels,
            color=node_colors,
            pad=10,
            thickness=40,
            line=dict(color='white', width=0)
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors,
            hovertemplate='%{value} records<extra></extra>'
        ),
        domain=dict(x=[0,1], y=[0.2,1.0])
    ))

    fig.update_layout(
        width=1200,
        height=800,
        margin=dict(l=20, r=20, t=100, b=20),
        font=dict(family="Arial", color="black", size=12),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5
        )
    )

    st.plotly_chart(fig, use_container_width=True)
