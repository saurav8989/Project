import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# --- API Config ---
API_URL = "http://127.0.0.1:8000/fhir/MeasureReport"

# --- Page Config ---
st.set_page_config(page_title="Dashboard", page_icon="🏥", layout="wide")

# --- Title and Description ---
st.markdown("<h1 style='font-size: 2.2rem;'>🏥 National Childhood Immunization Analytics & DQA</h1>", unsafe_allow_html=True)
st.markdown("""
This dashboard consumes HL7 FHIR `MeasureReport` resources directly from the custom FastAPI Reference Server. 
It combines **Epidemiological Analytics** (Coverage & Dropout) with rigorous **Data Quality Assessment (DQA)** 
to prove that interoperability via FHIR preserves all necessary metadata for auditing.
""")

@st.cache_data(ttl=600)
def fetch_fhir_data():
    """Fetches and parses FHIR JSON from the FastAPI server."""
    try:
        response = requests.get(API_URL)
        if response.status_code != 200:
            st.error("Error: Could not reach the FHIR API. Is the server running on port 8000?")
            return pd.DataFrame()
        
        bundle = response.json()
        entries = bundle.get("entry", [])
        
        data = []
        for entry in entries:
            resource = entry.get("resource", {})
            if resource.get("resourceType") != "MeasureReport":
                continue
                
            # Parse Date (Gregorian proxy from period)
            date_str = resource.get("period", {}).get("end")
            date_obj = pd.to_datetime(date_str) if date_str else None
            
            # Parse Vaccine ID
            measure_ref = resource.get("measure", "")
            vaccine_id = measure_ref.split("Measure/measure-")[-1]
            
            # Parse Custom Extensions (Fiscal Year, Month)
            fiscal_year = "Unknown"
            month_nepali = "Unknown"
            extensions = resource.get("extension", [])
            for ext in extensions:
                if ext.get("url") == "http://example.org/fhir/StructureDefinition/nepali-fiscal-period":
                    sub_exts = ext.get("extension", [])
                    for sub in sub_exts:
                        if sub.get("url") == "fiscalYear":
                            fiscal_year = sub.get("valueString", "Unknown")
                        elif sub.get("url") == "monthEnglish":
                            month_nepali = sub.get("valueString", "Unknown")
            
            # Extract Metrics
            numerator = 0
            denominator = 0
            percentage = 0.0
            is_absent = False
            
            groups = resource.get("group", [])
            if groups:
                group = groups[0]
                populations = group.get("population", [])
                for pop in populations:
                    code_list = pop.get("code", {}).get("coding", [])
                    code = code_list[0].get("code") if code_list else None
                    
                    if code == "numerator":
                        numerator = pop.get("count", 0)
                        # Check for missing data explicitly via FHIR extension
                        for ext in pop.get("extension", []):
                            if ext.get("url") == "http://hl7.org/fhir/StructureDefinition/data-absent-reason":
                                is_absent = True
                    elif code == "denominator":
                        denominator = pop.get("count", 0)
                
                # Get percentage from measureScoreQuantity
                msq = group.get("measureScoreQuantity", {})
                percentage = msq.get("value", 0.0)
            
            data.append({
                "Date": date_obj,
                "Fiscal_Year": fiscal_year,
                "Month": month_nepali,
                "Vaccine_ID": vaccine_id,
                "Doses_Administered": numerator,
                "Target_Population": denominator,
                "Coverage_Percentage": percentage,
                "Is_Absent": is_absent
            })
            
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def fetch_facility_data():
    """Fetches facility reporting data from the raw CSV."""
    try:
        df_csv = pd.read_csv("data/processed/Cleaned_Data.csv")
        df_csv["Facilities Expected"] = pd.to_numeric(df_csv["Facilities Expected"], errors="coerce")
        df_csv["Facilities Reported"] = pd.to_numeric(df_csv["Facilities Reported"], errors="coerce")
        return df_csv
    except Exception:
        return pd.DataFrame()

# --- Load Data ---
with st.spinner("Fetching standard FHIR resources from API..."):
    df = fetch_fhir_data()
    df_facility = fetch_facility_data()

if df.empty:
    st.warning("No data available. Please ensure the FastAPI server is running on http://127.0.0.1:8000.")
    st.stop()

# --- Vaccine Family Mapping ---
VACCINE_FAMILIES = {
    "BCG": ["bcg"],
    "Penta": ["penta1", "penta2", "penta3"],
    "OPV": ["opv1", "opv2", "opv3"],
    "PCV": ["pcv1", "pcv2", "pcv3"],
    "Rota": ["rota1", "rota2"],
    "MR": ["mr1", "mr2"],
    "fIPV": ["fipv1", "fipv2"],
    "TCV": ["tcv"],
    "JE": ["je"],
}

# --- Sidebar Filters ---
st.sidebar.header("Dashboard Controls")
vaccine_options = ["-- Select Vaccine --"] + list(VACCINE_FAMILIES.keys())
selected_family = st.sidebar.selectbox("Select Vaccine Family", vaccine_options)

fiscal_years = ["-- Select Fiscal Year --", "All Years"] + sorted(list(df["Fiscal_Year"].unique()))
selected_fy = st.sidebar.selectbox("Select Fiscal Year", fiscal_years)

# --- Landing Page State (Global Overview) ---
if selected_family == "-- Select Vaccine --" or selected_fy == "-- Select Fiscal Year --":
    st.info("👈 Please select a Vaccine Family and Fiscal Year from the sidebar to view specific analytics.")
    
    st.markdown("###  National Childhood Immunization Overview")
    st.markdown("This page aggregates the entire 5-year childhodd immunization dataset to provide macro-level insights before drilling down.")
    
    # 1. Global KPIs
    total_fhir_records = len(df)
    total_outliers = len(df[df["Coverage_Percentage"] > 100])
    
    # Calculate global consistency violations
    global_violations = 0
    pivot = df.pivot_table(index=["Fiscal_Year", "Month"], columns="Vaccine_ID", values="Doses_Administered")
    for family in VACCINE_FAMILIES.values():
        if len(family) > 1:
            for i in range(len(family)-1):
                curr, nxt = family[i], family[i+1]
                if curr in pivot.columns and nxt in pivot.columns:
                    global_violations += (pivot[nxt] > pivot[curr]).sum()
                    
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Records", f"{total_fhir_records:,}")
    kpi2.metric("Total Coverage Outliers (>100%)", f"{total_outliers:,}")
    kpi3.metric("Total Logical Violations", f"{global_violations:,}")
    
    st.divider()
    
    # 2. Charts
    col_macro1, col_macro2 = st.columns(2)
    
    with col_macro1:
        # Macro Line Chart
        avg_cov_df = df.groupby("Date")["Coverage_Percentage"].mean().reset_index()
        fig_macro = px.line(
            avg_cov_df, x="Date", y="Coverage_Percentage", 
            title="Average Coverage Trend (All Vaccines)", 
            markers=True, labels={"Coverage_Percentage": "Avg Coverage (%)"}
        )
        fig_macro.update_layout(yaxis=dict(range=[0, max(120, avg_cov_df["Coverage_Percentage"].max() + 10)]))
        st.plotly_chart(fig_macro, use_container_width=True)
        
        # Donut Chart for DQA
        absent_count = df["Is_Absent"].sum()
        valid_clean = total_fhir_records - total_outliers - absent_count
        dqa_pie = pd.DataFrame({
            "Category": ["Clean Data", "Coverage Outliers", "Missing Data (TCV)"],
            "Count": [valid_clean, total_outliers, absent_count]
        })
        fig_pie = px.pie(
            dqa_pie, names="Category", values="Count", hole=0.5, 
            title="Data Quality Distribution",
            color="Category",
            color_discrete_map={"Clean Data": "#2ca02c", "Coverage Outliers": "#d62728", "Missing Data (TCV)": "#ff7f0e"}
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_macro2:
        # Total Volume Bar Chart
        vol_data = []
        for family_name, indicators in VACCINE_FAMILIES.items():
            total_doses = df[df["Vaccine_ID"].isin(indicators)]["Doses_Administered"].sum()
            vol_data.append({"Vaccine Family": family_name, "Total Doses": total_doses})
        
        vol_df = pd.DataFrame(vol_data).sort_values("Total Doses", ascending=True)
        fig_vol = px.bar(
            vol_df, x="Total Doses", y="Vaccine Family", orientation='h', 
            title="Total Doses Administered by Vaccine Family (5 Years)",
            text="Total Doses",
            color="Vaccine Family"
        )
        fig_vol.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig_vol.update_layout(showlegend=False, xaxis=dict(range=[0, vol_df["Total Doses"].max() * 1.2]))
        st.plotly_chart(fig_vol, use_container_width=True)

    st.stop()

# Filter Data for Selected Family & FY
family_indicators = VACCINE_FAMILIES[selected_family]

filtered_df = df[df["Vaccine_ID"].isin(family_indicators)].copy()
if selected_fy != "All Years":
    filtered_df = filtered_df[filtered_df["Fiscal_Year"] == selected_fy]

if filtered_df.empty:
    st.info("No data found for this selection.")
    st.stop()

# Sort chronologically
filtered_df = filtered_df.sort_values(by="Date")

# --- 1. Top Metrics & Completeness ---
st.subheader("1. Executive Metrics & Completeness")
total_records = len(filtered_df)

# True FHIR Completeness via DataAbsentReason
absent_records = filtered_df["Is_Absent"].sum()
valid_records = total_records - absent_records
completeness_pct = (valid_records / total_records) * 100 if total_records > 0 else 0

avg_coverage = filtered_df["Coverage_Percentage"].mean()

# Calculate Facility Reporting Rate
facility_rate = 0.0
if not df_facility.empty:
    if selected_fy != "All Years":
        fac_df = df_facility[df_facility["Fiscal Year"] == selected_fy]
    else:
        fac_df = df_facility
    
    total_expected = fac_df["Facilities Expected"].sum()
    total_reported = fac_df["Facilities Reported"].sum()
    if total_expected > 0:
        facility_rate = (total_reported / total_expected) * 100

col1, col2, col3 = st.columns(3)
# col1.metric("FHIR Records Found", f"{total_records} / {expected_records} Expected")
col1.metric("Data Completeness", f"{completeness_pct:.1f}%", help="Missing records (like TCV) lower this score.")
col2.metric(f"Avg {selected_family} Coverage", f"{avg_coverage:.1f}%")
col3.metric("Facility Reporting Rate", f"{facility_rate:.1f}%", help="Derived from raw DHIS2 datasets.")

st.divider()

# --- 2. Coverage and Dropout ---
st.subheader("2. Epidemiological Analytics")
if len(family_indicators) > 1:
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("**Longitudinal Coverage Trend**")
        fig_line = px.line(
            filtered_df, 
            x="Date" if selected_fy == "All Years" else "Month", 
            y="Coverage_Percentage", 
            color="Vaccine_ID",
            markers=True,
            labels={"Coverage_Percentage": "Coverage (%)"}
        )
        fig_line.update_layout(yaxis=dict(range=[0, max(120, filtered_df["Coverage_Percentage"].max() + 10)]))
        st.plotly_chart(fig_line, use_container_width=True)

    with col_chart2:
        st.markdown("**Clinical Drop-out (Total Doses)**")
        dropout_df = filtered_df.groupby("Vaccine_ID")["Doses_Administered"].sum().reset_index()
        dropout_df["Vaccine_ID"] = pd.Categorical(dropout_df["Vaccine_ID"], categories=family_indicators, ordered=True)
        dropout_df = dropout_df.sort_values("Vaccine_ID")

        fig_bar = px.bar(
            dropout_df,
            x="Vaccine_ID",
            y="Doses_Administered",
            text="Doses_Administered",
            color="Vaccine_ID"
        )
        fig_bar.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig_bar.update_layout(showlegend=False, yaxis=dict(range=[0, dropout_df["Doses_Administered"].max() * 1.2]))
        st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.markdown("**Longitudinal Coverage Trend**")
    fig_line = px.line(
        filtered_df, 
        x="Date" if selected_fy == "All Years" else "Month", 
        y="Coverage_Percentage", 
        color="Vaccine_ID",
        markers=True,
        labels={"Coverage_Percentage": "Coverage (%)"}
    )
    fig_line.update_layout(yaxis=dict(range=[0, max(120, filtered_df["Coverage_Percentage"].max() + 10)]))
    st.plotly_chart(fig_line, use_container_width=True)

st.divider()

# --- 3. Consistency & Outliers ---
st.subheader("3. Data Quality Assessment (DQA)")
if len(family_indicators) > 1:
    dqa_col1, dqa_col2 = st.columns(2)

    with dqa_col1:
        st.markdown("🚨 **Consistency Violations (Drop-out Logic)**")
        st.caption("Detects logical errors: Subsequent doses exceeding initial doses (e.g., Dose 2 > Dose 1) in the same month.")
        
        # Pivot table to compare doses per month
        pivot_df = filtered_df.pivot_table(index=["Fiscal_Year", "Month"], columns="Vaccine_ID", values="Doses_Administered").reset_index()
        
        violations = []
        for _, row in pivot_df.iterrows():
            # Check pairwise logic: dose 1 >= dose 2, dose 2 >= dose 3
            for i in range(len(family_indicators) - 1):
                dose_current = family_indicators[i]
                dose_next = family_indicators[i+1]
                if pd.notna(row.get(dose_current)) and pd.notna(row.get(dose_next)):
                    if row[dose_next] > row[dose_current]:
                        violations.append({
                            "Fiscal_Year": row["Fiscal_Year"],
                            "Month": row["Month"],
                            "Violation": f"{dose_next} ({row[dose_next]:.0f}) > {dose_current} ({row[dose_current]:.0f})"
                        })
        if violations:
            st.error(f"Found {len(violations)} consistency violations.")
            st.dataframe(pd.DataFrame(violations), use_container_width=True)
        else:
            st.success("No consistency violations detected for this selection!")

    with dqa_col2:
        st.markdown("🔴 **Coverage Outliers (>100%)**")
        st.caption("Flags impossible coverage rates (>100%) indicating population denominator issues.")
        
        outliers = filtered_df[filtered_df["Coverage_Percentage"] > 100][["Fiscal_Year", "Month", "Vaccine_ID", "Coverage_Percentage"]]
        if not outliers.empty:
            st.error(f"Found {len(outliers)} coverage outliers.")
            st.dataframe(outliers.sort_values(by="Coverage_Percentage", ascending=False), use_container_width=True)
        else:
            st.success("No coverage outliers detected for this selection!")
else:
    st.markdown("🔴 **Coverage Outliers (>100%)**")
    st.caption("Flags impossible coverage rates (>100%) indicating population denominator issues.")
    
    outliers = filtered_df[filtered_df["Coverage_Percentage"] > 100][["Fiscal_Year", "Month", "Vaccine_ID", "Coverage_Percentage"]]
    if not outliers.empty:
        st.error(f"Found {len(outliers)} coverage outliers.")
        st.dataframe(outliers.sort_values(by="Coverage_Percentage", ascending=False), use_container_width=True)
    else:
        st.success("No coverage outliers detected for this selection!")

st.divider()
with st.expander("🔍 View Raw Parsed FHIR Data"):
    st.dataframe(filtered_df, use_container_width=True)
