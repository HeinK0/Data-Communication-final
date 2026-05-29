from pathlib import Path
from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st


# --------------------------------------------------
# Page setup
# --------------------------------------------------
st.set_page_config(
    page_title="Hein Ko's Learning Journey Reflection Dashboard",
    layout="wide",
)


# --------------------------------------------------
# Styling
# --------------------------------------------------
st.markdown(
    """
<style>
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
}

.small-intro {
    color: #4b5563;
    font-size: 1rem;
    line-height: 1.55;
    max-width: 980px;
}

.kpi-card {
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 18px 18px;
    background: #ffffff;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    min-height: 112px;
}

.kpi-label {
    color: #6b7280;
    font-size: 0.9rem;
    font-weight: 600;
    margin-bottom: 8px;
}

.kpi-value {
    color: #111827;
    font-size: clamp(1.55rem, 2.2vw, 2.35rem);
    font-weight: 750;
    line-height: 1.15;
    overflow-wrap: anywhere;
}

.kpi-small {
    color: #6b7280;
    font-size: 0.78rem;
    margin-top: 6px;
}

.chart-summary {
    color: #4b5563;
    font-size: 0.95rem;
    line-height: 1.45;
    margin-top: -0.3rem;
    margin-bottom: 0.7rem;
}

.finding-card {
    border-left: 5px solid #ef4444;
    background: #fff7f7;
    border-radius: 14px;
    padding: 15px 16px;
    min-height: 116px;
}

.finding-title {
    font-weight: 750;
    color: #111827;
    margin-bottom: 6px;
}

.finding-text {
    color: #374151;
    font-size: 0.95rem;
    line-height: 1.45;
}

.definition-box {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 14px 16px;
    color: #374151;
}

.moment-box {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 14px 16px;
    color: #374151;
    line-height: 1.5;
}

hr {
    margin-top: 1.5rem;
    margin-bottom: 1.5rem;
}
</style>
""",
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Anonymization helpers
# --------------------------------------------------
def anonymize_text(value: object) -> str:
    """Remove or soften direct role/sector wording for public dashboard display."""
    text = "" if pd.isna(value) else str(value)

    replacements = {
        "Humanitarian data officer": "Data and research practitioner",
        "humanitarian data officer": "data and research practitioner",
        "Humanitarian data": "Data and research practice",
        "humanitarian data": "data and research practice",
        "MEAL and education technology": "Program monitoring and learning support",
        "MEAL and learning-program support": "Program support role",
        "MEAL": "Program monitoring",
        "Postgraduate learner": "Diploma learner",
        "postgraduate learner": "diploma learner",
        "Postgraduate": "Diploma",
        "postgraduate": "diploma",
        "Final project": "Dashboard project",
        "final project": "dashboard project",
        "Research firm": "Research organization",
        "research firm": "research organization",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def map_life_phase(value: object) -> str:
    """Create safer life-phase labels for charts and filters."""
    text = anonymize_text(value)

    mapping = {
        "Economics foundation and early direction": "Economics foundation and early direction",
        "Self-directed learning and resilience building": "Self-directed learning and resilience building",
        "Service and community growth": "Service and community growth",
        "Community development and field research exposure": "Community development and field research",
        "Research methods and community-development grounding": "Diploma and research-methods grounding",
        "Research firm and digital survey specialization": "Research and digital survey specialization",
        "Data Management Work": "Data and research practice",
        "University, Data Management Work": "University and data practice",
        "Youth empowerment and digital learning": "Youth learning and digital skills",
        "Youth empowerment and career support": "Youth learning and career support",
    }

    return mapping.get(text, text)


def map_journey_theme(value: object) -> str:
    """Create broader public-facing journey themes."""
    text = anonymize_text(value)

    mapping = {
        "Education": "Education",
        "Self-learning": "Self-learning",
        "Volunteering": "Volunteering",
        "Field research": "Field research",
        "Education and field research": "Education and research",
        "Data management Work": "Data and research practice",
        "Data Management Work": "Data and research practice",
        "Work-study growth": "Work-study development",
        "Program monitoring and learning support": "Program support",
        "Project": "Community project",
    }

    return mapping.get(text, text)


def map_role_context(value: object) -> str:
    """Create broader public-facing role labels."""
    text = anonymize_text(value)

    mapping = {
        "Undergraduate learner": "Undergraduate learner",
        "Independent learner": "Independent learner",
        "Volunteer caregiver/support role": "Volunteer support role",
        "Field and community data worker": "Community research role",
        "Diploma learner": "Diploma learner",
        "Research mentor": "Research mentor",
        "Research data assistant": "Research support role",
        "Data and research practitioner": "Data and research practitioner",
        "Public-interest enumeration": "Public-interest data collection",
        "Digital literacy project contributor": "Digital learning project contributor",
        "Career-growth platform contributor": "Career-support project contributor",
        "Program support role": "Program support role",
    }

    return mapping.get(text, text)


def map_decision_area(value: object) -> str:
    """Create safer decision-area labels."""
    text = anonymize_text(value)

    mapping = {
        "MEAL": "Program monitoring",
        "Program monitoring": "Program monitoring",
        "Education technology": "Learning support",
        "Dashboarding": "Dashboard development",
        "Data visualization": "Data visualization",
        "Data analysis": "Data analysis",
        "Survey design": "Survey design",
        "Quality monitoring": "Quality monitoring",
        "Program improvement": "Program improvement",
        "Learning transfer": "Learning transfer",
        "Human-centered work": "Human-centered work",
    }

    return mapping.get(text, text)


def create_activity_area(row: pd.Series) -> str:
    """Use a broad area instead of exact activity or position."""
    decision = row.get("decision_area_display", "")
    theme = row.get("journey_theme_display", "")

    if decision:
        return decision

    return theme


# --------------------------------------------------
# Data loading and preparation
# --------------------------------------------------
@st.cache_data
def load_data() -> pd.DataFrame:
    possible_paths = [
        Path("data/hein_personalized_growth_journey_dataset.csv"),
        Path("hein_personalized_growth_journey_dataset.csv"),
    ]

    data_path = None
    for path in possible_paths:
        if path.exists():
            data_path = path
            break

    if data_path is None:
        st.error(
            "Dataset not found. Please place `hein_personalized_growth_journey_dataset.csv` "
            "inside the `data` folder."
        )
        st.stop()

    df = pd.read_csv(data_path)

    required_columns = [
        "record_id",
        "date",
        "life_phase",
        "journey_theme",
        "role_context",
        "activity_focus",
        "time_invested_hours",
        "practice_sessions",
        "estimated_outputs_count",
        "difficulty_score_1_5",
        "confidence_score_1_5",
        "stress_score_1_5",
        "motivation_score_1_5",
        "skill_growth_score_1_5",
        "outcome_score_1_5",
        "decision_area",
        "moment_type",
        "short_reflection",
    ]

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        st.error("The dataset is missing these required columns:")
        st.code(", ".join(missing))
        st.stop()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    # Remove rows connected to this current dashboard/final project if they exist.
    exclude_terms = "final project|dashboard project"
    exclude_mask = (
        df["life_phase"].astype(str).str.contains(exclude_terms, case=False, na=False)
        | df["journey_theme"].astype(str).str.contains(exclude_terms, case=False, na=False)
        | df["role_context"].astype(str).str.contains(exclude_terms, case=False, na=False)
        | df["activity_focus"].astype(str).str.contains(exclude_terms, case=False, na=False)
    )
    df = df[~exclude_mask].copy()

    numeric_cols = [
        "time_invested_hours",
        "practice_sessions",
        "estimated_outputs_count",
        "difficulty_score_1_5",
        "confidence_score_1_5",
        "stress_score_1_5",
        "motivation_score_1_5",
        "skill_growth_score_1_5",
        "outcome_score_1_5",
    ]

    optional_numeric_cols = [
        "energy_score_1_5",
        "support_score_1_5",
        "ethics_awareness_score_1_5",
        "impact_scope_score_1_5",
    ]

    for col in numeric_cols + optional_numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["year"] = df["date"].dt.year
    df["period_label"] = df["date"].dt.strftime("%Y-%m")
    df["year_label"] = df["year"].astype(str)
    df["quarter_label"] = df["date"].dt.to_period("Q").astype(str)

    # Public-facing anonymized display columns.
    df["life_phase_display"] = df["life_phase"].apply(map_life_phase)
    df["journey_theme_display"] = df["journey_theme"].apply(map_journey_theme)
    df["role_context_display"] = df["role_context"].apply(map_role_context)
    df["decision_area_display"] = df["decision_area"].apply(map_decision_area)
    df["activity_area_display"] = df.apply(create_activity_area, axis=1)
    df["short_reflection_display"] = df["short_reflection"].apply(anonymize_text)

    # A simple composite reflection score.
    df["growth_index"] = df[
        [
            "confidence_score_1_5",
            "skill_growth_score_1_5",
            "outcome_score_1_5",
            "motivation_score_1_5",
        ]
    ].mean(axis=1)

    return df


# --------------------------------------------------
# Utility functions
# --------------------------------------------------
def safe_options(series):
    return sorted(series.dropna().astype(str).unique().tolist())


def all_default_multiselect(label, values):
    options = safe_options(values)
    return st.sidebar.multiselect(label, options=options, default=options)


def kpi_card(label, value, note=""):
    st.markdown(
        f"""
<div class="kpi-card">
    <div class="kpi-label">{escape(str(label))}</div>
    <div class="kpi-value">{escape(str(value))}</div>
    <div class="kpi-small">{escape(str(note))}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def finding_card(title, text):
    st.markdown(
        f"""
<div class="finding-card">
    <div class="finding-title">{escape(str(title))}</div>
    <div class="finding-text">{escape(str(text))}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def correlation_text(corr_value):
    if pd.isna(corr_value):
        return "Not enough data to estimate the relationship."

    strength = abs(corr_value)
    direction = "positive" if corr_value >= 0 else "negative"

    if strength < 0.20:
        level = "very weak"
    elif strength < 0.40:
        level = "weak"
    elif strength < 0.60:
        level = "moderate"
    else:
        level = "strong"

    return f"The relationship is {level} and {direction}. This is an association, not proof of causation."


def build_trend_data(data: pd.DataFrame, view: str, score_columns: list[str]) -> pd.DataFrame:
    temp = data.copy()

    if view == "Yearly average":
        group_cols = ["year_label"]
        temp["trend_label"] = temp["year_label"]
        temp["trend_order"] = temp["year"]
    else:
        group_cols = ["quarter_label"]
        temp["trend_label"] = temp["quarter_label"]
        temp["trend_order"] = temp["date"].dt.to_period("Q").astype(str)

    label_map = temp[group_cols + ["trend_label", "trend_order"]].drop_duplicates()

    trend = (
        temp.groupby(group_cols, as_index=False)[score_columns]
        .mean()
        .merge(label_map, on=group_cols, how="left")
        .sort_values("trend_order")
    )

    long_trend = trend.melt(
        id_vars=["trend_label", "trend_order"],
        value_vars=score_columns,
        var_name="metric",
        value_name="average_score",
    )

    return long_trend


# --------------------------------------------------
# Load data
# --------------------------------------------------
df = load_data()


# --------------------------------------------------
# Sidebar filters
# --------------------------------------------------
st.sidebar.title("🎛️ Filters")

selected_years = st.sidebar.multiselect(
    "Year",
    options=sorted(df["year"].dropna().unique().tolist()),
    default=sorted(df["year"].dropna().unique().tolist()),
)

selected_phases = all_default_multiselect("Life phase", df["life_phase_display"])
selected_themes = all_default_multiselect("Journey theme", df["journey_theme_display"])
selected_moments = all_default_multiselect("Moment type", df["moment_type"])
selected_decisions = all_default_multiselect("Decision area", df["decision_area_display"])

filtered_df = df.copy()

if selected_years:
    filtered_df = filtered_df[filtered_df["year"].isin(selected_years)]

if selected_phases:
    filtered_df = filtered_df[filtered_df["life_phase_display"].isin(selected_phases)]

if selected_themes:
    filtered_df = filtered_df[filtered_df["journey_theme_display"].isin(selected_themes)]

if selected_moments:
    filtered_df = filtered_df[filtered_df["moment_type"].isin(selected_moments)]

if selected_decisions:
    filtered_df = filtered_df[filtered_df["decision_area_display"].isin(selected_decisions)]

st.sidebar.markdown("---")
st.sidebar.caption("Public-facing labels are anonymized for safer sharing.")


# --------------------------------------------------
# Header
# --------------------------------------------------
st.title("Hein Ko's Learning Journey Reflection Dashboard")
st.markdown("### Data and Communication Final Assignment Dashboard")

st.markdown(
    """
<div class="small-intro">
This dashboard uses an anonymized personal-growth dataset to explore learning, effort,
confidence, stress, outcomes, and key turning points over time.
</div>
""",
    unsafe_allow_html=True,
)

if filtered_df.empty:
    st.warning("No data matches the selected filters. Please adjust the sidebar filters.")
    st.stop()


# --------------------------------------------------
# 1. Dataset overview
# --------------------------------------------------
st.markdown("## 1. Dataset Overview")

start_period = filtered_df["date"].min().strftime("%Y-%m")
end_period = filtered_df["date"].max().strftime("%Y-%m")
period_text = f"{start_period} → {end_period}"

kpi1, kpi2 = st.columns([1, 2])

with kpi1:
    kpi_card("Records", f"{len(filtered_df):,}", "Filtered observations")

with kpi2:
    kpi_card("Period", period_text, "Start to end of selected data")

st.markdown("### Chart-relevant columns")

column_summary = pd.DataFrame(
    [
        {
            "Column": "date / period_label",
            "Definition": "Time period used for the trend and yearly charts.",
        },
        {
            "Column": "life_phase_display",
            "Definition": "Anonymized stage of the personal growth journey.",
        },
        {
            "Column": "journey_theme_display",
            "Definition": "Broad learning/work theme used for filters and chart categories.",
        },
        {
            "Column": "time_invested_hours",
            "Definition": "Estimated hours invested during the period.",
        },
        {
            "Column": "confidence_score_1_5",
            "Definition": "Self-rated confidence score from 1 = low to 5 = high.",
        },
        {
            "Column": "stress_score_1_5",
            "Definition": "Self-rated stress score from 1 = low to 5 = high.",
        },
        {
            "Column": "skill_growth_score_1_5",
            "Definition": "Self-rated skill-growth score from 1 = low to 5 = high.",
        },
        {
            "Column": "outcome_score_1_5",
            "Definition": "Self-rated outcome score from 1 = low to 5 = high.",
        },
        {
            "Column": "estimated_outputs_count",
            "Definition": "Estimated number of outputs or deliverables in that period.",
        },
        {
            "Column": "moment_type",
            "Definition": "Short category describing the type of experience.",
        },
    ]
)

st.dataframe(column_summary, use_container_width=True, hide_index=True)

with st.expander("View anonymized filtered dataset"):
    display_cols = [
        "record_id",
        "period_label",
        "life_phase_display",
        "journey_theme_display",
        "role_context_display",
        "activity_area_display",
        "time_invested_hours",
        "confidence_score_1_5",
        "stress_score_1_5",
        "skill_growth_score_1_5",
        "outcome_score_1_5",
        "moment_type",
        "short_reflection_display",
    ]

    st.dataframe(
        filtered_df[display_cols],
        use_container_width=True,
        hide_index=True,
    )


# --------------------------------------------------
# 2. Data visualizations
# --------------------------------------------------
st.markdown("## 2. Data Visualizations")

# Chart 1
st.markdown("### Chart 1: Growth, Confidence, Stress, and Outcome Over Time")
st.markdown(
    """
<div class="chart-summary">
This chart shows the average score trend over time. Use yearly view for the cleanest summary,
or quarterly view to see more detailed changes.
</div>
""",
    unsafe_allow_html=True,
)

chart1_left, chart1_right = st.columns([1, 2])

with chart1_left:
    trend_view = st.radio(
        "Trend view",
        options=["Yearly average", "Quarterly average"],
        index=0,
        horizontal=False,
    )

with chart1_right:
    metric_options = {
        "Confidence": "confidence_score_1_5",
        "Stress": "stress_score_1_5",
        "Skill growth": "skill_growth_score_1_5",
        "Outcome": "outcome_score_1_5",
    }

    selected_metric_names = st.multiselect(
        "Score lines",
        options=list(metric_options.keys()),
        default=["Confidence", "Stress", "Skill growth", "Outcome"],
    )

selected_score_cols = [metric_options[name] for name in selected_metric_names]

if selected_score_cols:
    trend_long = build_trend_data(filtered_df, trend_view, selected_score_cols)

    clean_metric_names = {
        "confidence_score_1_5": "Confidence",
        "stress_score_1_5": "Stress",
        "skill_growth_score_1_5": "Skill growth",
        "outcome_score_1_5": "Outcome",
    }

    trend_long["metric"] = trend_long["metric"].map(clean_metric_names)

    trend_order = (
        trend_long[["trend_label", "trend_order"]]
        .drop_duplicates()
        .sort_values("trend_order")["trend_label"]
        .tolist()
    )

    fig_trend = px.line(
        trend_long,
        x="trend_label",
        y="average_score",
        color="metric",
        markers=True,
        title=f"{trend_view} score trends",
        labels={
            "trend_label": "Period",
            "average_score": "Average score (1–5)",
            "metric": "Metric",
        },
    )
    fig_trend.update_yaxes(range=[0, 5.2], dtick=1)
    fig_trend.update_xaxes(categoryorder="array", categoryarray=trend_order)
    fig_trend.update_layout(
        legend_title_text="Metric",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("---")

# Chart 2
st.markdown("### Chart 2: Time Investment by Growth Area")
st.markdown(
    """
<div class="chart-summary">
This chart compares where the most estimated time was invested across anonymized growth areas.
</div>
""",
    unsafe_allow_html=True,
)

group_options = {
    "Life phase": "life_phase_display",
    "Journey theme": "journey_theme_display",
    "Role context": "role_context_display",
    "Decision area": "decision_area_display",
}

group_label = st.selectbox(
    "Group time investment by",
    options=list(group_options.keys()),
    index=0,
)

group_choice = group_options[group_label]

hours_df = (
    filtered_df.groupby(group_choice, as_index=False)
    .agg(
        total_hours=("time_invested_hours", "sum"),
        records=("record_id", "count"),
        avg_confidence=("confidence_score_1_5", "mean"),
        avg_stress=("stress_score_1_5", "mean"),
    )
    .sort_values("total_hours", ascending=False)
)

fig_hours = px.bar(
    hours_df,
    x="total_hours",
    y=group_choice,
    orientation="h",
    hover_data={
        "total_hours": ":,.0f",
        "records": True,
        "avg_confidence": ":.2f",
        "avg_stress": ":.2f",
    },
    title=f"Total estimated hours by {group_label.lower()}",
    labels={
        "total_hours": "Total estimated hours",
        group_choice: group_label,
    },
)
fig_hours.update_layout(
    yaxis={"categoryorder": "total ascending"},
    margin=dict(l=20, r=20, t=60, b=20),
    height=max(420, 36 * len(hours_df)),
)
st.plotly_chart(fig_hours, use_container_width=True)

st.markdown("---")

# Chart 3
st.markdown("### Chart 3: Time Investment and Outcome")
st.markdown(
    """
<div class="chart-summary">
This chart explores whether periods with higher time investment also had stronger outcome scores.
</div>
""",
    unsafe_allow_html=True,
)

fig_scatter = px.scatter(
    filtered_df,
    x="time_invested_hours",
    y="outcome_score_1_5",
    size="estimated_outputs_count",
    color="journey_theme_display",
    hover_data=[
        "period_label",
        "life_phase_display",
        "activity_area_display",
        "difficulty_score_1_5",
        "confidence_score_1_5",
        "stress_score_1_5",
        "skill_growth_score_1_5",
    ],
    title="Time invested compared with outcome score",
    labels={
        "time_invested_hours": "Estimated hours invested",
        "outcome_score_1_5": "Outcome score (1–5)",
        "journey_theme_display": "Journey theme",
        "estimated_outputs_count": "Outputs",
        "period_label": "Period",
        "life_phase_display": "Life phase",
        "activity_area_display": "Activity area",
        "difficulty_score_1_5": "Difficulty",
        "confidence_score_1_5": "Confidence",
        "stress_score_1_5": "Stress",
        "skill_growth_score_1_5": "Skill growth",
    },
)
fig_scatter.update_yaxes(range=[0, 5.2], dtick=1)
fig_scatter.update_layout(
    legend_title_text="Journey theme",
    margin=dict(l=20, r=20, t=60, b=20),
)
st.plotly_chart(fig_scatter, use_container_width=True)

corr = filtered_df["time_invested_hours"].corr(filtered_df["outcome_score_1_5"])
corr_display = "N/A" if pd.isna(corr) else f"{corr:.2f}"
st.markdown(f"**Correlation:** {corr_display}. {correlation_text(corr)}")

st.markdown("---")

# Chart 4
st.markdown("### Chart 4: Moment Types by Year")
st.markdown(
    """
<div class="chart-summary">
This chart shows what kind of experience appeared most often in each year.
</div>
""",
    unsafe_allow_html=True,
)

with st.expander("Moment type meanings"):
    st.markdown(
        """
<div class="moment-box">
<b>Steady:</b> normal progress without a major turning point.<br>
<b>Challenge:</b> a difficult period that required extra effort or adjustment.<br>
<b>Breakthrough:</b> a period where learning, confidence, or output improved clearly.<br>
<b>Setback:</b> a period affected by stress, low energy, delay, or difficulty.<br>
<b>Reflection:</b> a period focused on reviewing direction, values, or future decisions.
</div>
""",
        unsafe_allow_html=True,
    )

moment_df = (
    filtered_df.groupby(["year", "moment_type"], as_index=False)
    .agg(records=("record_id", "count"))
)

fig_moment = px.bar(
    moment_df,
    x="year",
    y="records",
    color="moment_type",
    title="Distribution of journey moment types by year",
    labels={
        "year": "Year",
        "records": "Number of records",
        "moment_type": "Moment type",
    },
)
fig_moment.update_layout(
    legend_title_text="Moment type",
    margin=dict(l=20, r=20, t=60, b=20),
)
st.plotly_chart(fig_moment, use_container_width=True)


# --------------------------------------------------
# 3. Key findings
# --------------------------------------------------
st.markdown("## 3. Key Findings")

top_hours_row = hours_df.iloc[0]
highest_stress_row = filtered_df.sort_values("stress_score_1_5", ascending=False).iloc[0]
highest_growth_row = filtered_df.sort_values("skill_growth_score_1_5", ascending=False).iloc[0]

breakthrough_count = int((filtered_df["moment_type"] == "breakthrough").sum())
setback_count = int((filtered_df["moment_type"] == "setback").sum())

finding1, finding2 = st.columns(2)
finding3, finding4 = st.columns(2)

with finding1:
    finding_card(
        "Most time invested",
        f"The largest time investment is in {top_hours_row[group_choice]} "
        f"with about {top_hours_row['total_hours']:.0f} estimated hours."
    )

with finding2:
    finding_card(
        "Highest stress period",
        f"The highest stress appears around {highest_stress_row['period_label']} "
        f"within the area of {highest_stress_row['activity_area_display']}."
    )

with finding3:
    finding_card(
        "Strongest growth period",
        f"The strongest skill-growth score appears around {highest_growth_row['period_label']} "
        f"within the area of {highest_growth_row['activity_area_display']}."
    )

with finding4:
    finding_card(
        "Journey pattern",
        f"The selected data includes {breakthrough_count} breakthrough moments and "
        f"{setback_count} setback moments."
    )


# --------------------------------------------------
# 4. Decision-making section
# --------------------------------------------------
st.markdown("## 4. Decision-Making Section")

decision_summary = (
    filtered_df.groupby("decision_area_display", as_index=False)
    .agg(
        avg_stress=("stress_score_1_5", "mean"),
        avg_growth=("skill_growth_score_1_5", "mean"),
        avg_outcome=("outcome_score_1_5", "mean"),
        total_hours=("time_invested_hours", "sum"),
        records=("record_id", "count"),
    )
    .sort_values(["avg_stress", "total_hours"], ascending=False)
)

high_stress_area = decision_summary.iloc[0]["decision_area_display"]
high_growth_area = decision_summary.sort_values("avg_growth", ascending=False).iloc[0][
    "decision_area_display"
]

st.markdown(
    f"""
**Decision question:** Based on my data, what should I do differently in the future?

Looking at my data, I was able to better understand my personal growth and track how my priorities have evolved over time.
It encouraged me to focus more on volunteering and on maintaining high-quality outputs in my work. 
I also recognized that I have continued to grow along my chosen career path through my studies and work experiences. 
At the same time, I noticed that I have not gained many entirely new skills compared to previous years, instead, most of my growth has come from deepening and improving the skills I already possess.
"""
)
