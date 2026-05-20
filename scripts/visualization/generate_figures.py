import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Configure style for publication quality
sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'

# Output directory
output_dir = "outputs/figures"
os.makedirs(output_dir, exist_ok=True)

print("Loading data and generating academic figures...")
# Load Data
df = pd.read_csv("data/processed/Cleaned_Data.csv")
df["Facilities Expected"] = pd.to_numeric(df["Facilities Expected"], errors='coerce')
df["Facilities Reported"] = pd.to_numeric(df["Facilities Reported"], errors='coerce')
df["Surviving Infants (Monthly)"] = pd.to_numeric(df["Surviving Infants (Monthly)"], errors='coerce')

vaccine_cols = [col for col in df.columns if "(Col" in col]

# ------------------------------------------------------------------------------
# 1. Time Series Charts: Coverage Trend
# ------------------------------------------------------------------------------
# We will calculate total doses administered across all vaccines and total expected population.
df['Total_Doses'] = df[vaccine_cols].sum(axis=1)
df['Total_Expected'] = df['Surviving Infants (Monthly)'] * len(vaccine_cols)
df['Avg_Coverage_Percentage'] = (df['Total_Doses'] / df['Total_Expected']) * 100

df['Month_Index'] = range(1, len(df) + 1)

plt.figure(figsize=(10, 5))
sns.lineplot(data=df, x='Month_Index', y='Avg_Coverage_Percentage', marker='o', linewidth=2, color="#2c7fb8")
plt.axhline(100, color='red', linestyle='--', alpha=0.5, label='100% Target')
plt.title("Longitudinal Average Coverage Trend (All Vaccines)", pad=15)
plt.xlabel("Months (Month 1 = Shrawan 2077/78, Month 60 = Asar 2081/82)")
plt.ylabel("Average Coverage (%)")
plt.legend()
plt.tight_layout()
plt.savefig(f"{output_dir}/fig_coverage_trend.png")
plt.close()
print(f"Generated: {output_dir}/fig_coverage_trend.png")

# ------------------------------------------------------------------------------
# 2. Heatmaps: Facility Completeness
# ------------------------------------------------------------------------------
df['Facility_Reporting_Rate'] = (df['Facilities Reported'] / df['Facilities Expected']) * 100
heatmap_data = df.pivot(index="Fiscal Year", columns="Month No.", values="Facility_Reporting_Rate")

plt.figure(figsize=(10, 5))
sns.heatmap(heatmap_data, annot=True, fmt=".1f", cmap="RdYlGn", vmin=70, vmax=100, linewidths=.5)
plt.title("Facility Reporting Completeness Heatmap (%)", pad=15)
plt.ylabel("Fiscal Year")
plt.xlabel("Month Number (1 = Shrawan, 12 = Asar)")
plt.tight_layout()
plt.savefig(f"{output_dir}/fig_facility_completeness_heatmap.png")
plt.close()
print(f"Generated: {output_dir}/fig_facility_completeness_heatmap.png")

# ------------------------------------------------------------------------------
# 3. Boxplots: Outlier Detection
# ------------------------------------------------------------------------------
melted_df = df.melt(id_vars=['Fiscal Year', 'Month (EN)', 'Surviving Infants (Monthly)'], 
                    value_vars=vaccine_cols, 
                    var_name='Vaccine', 
                    value_name='Doses')
melted_df['Doses'] = pd.to_numeric(melted_df['Doses'], errors='coerce')
melted_df['Coverage'] = (melted_df['Doses'] / melted_df['Surviving Infants (Monthly)']) * 100

plt.figure(figsize=(12, 6))
# Only label Vaccine names cleanly
melted_df['Vaccine_Clean'] = melted_df['Vaccine'].apply(lambda x: x.split(" (")[0])
sns.boxplot(data=melted_df, x='Vaccine_Clean', y='Coverage', palette="Set2")
plt.axhline(100, color='red', linestyle='--', alpha=0.5)
plt.title("Coverage Outlier Detection by Vaccine (Boxplots)", pad=15)
plt.xlabel("Vaccine Indicator")
plt.ylabel("Coverage Percentage (%)")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(f"{output_dir}/fig_outlier_boxplots.png")
plt.close()
print(f"Generated: {output_dir}/fig_outlier_boxplots.png")

# ------------------------------------------------------------------------------
# 4. Bar Charts: Violation Frequencies (Consistency checks)
# ------------------------------------------------------------------------------
violations = {
    'Rota (1st < 2nd)': 0,
    'OPV (1st < 2nd < 3rd)': 0,
    'fIPV (1st < 2nd)': 0,
    'PCV (1st < 2nd < 3rd)': 0,
    'Penta (1st < 2nd < 3rd)': 0,
    'MR (1st < 2nd)': 0
}

for idx, row in df.iterrows():
    if pd.notna(row['Rota 1st (Col 3)']) and pd.notna(row['Rota 2nd (Col 4)']):
        if row['Rota 2nd (Col 4)'] > row['Rota 1st (Col 3)']: violations['Rota (1st < 2nd)'] += 1
    
    if pd.notna(row['OPV 1st (Col 5)']) and pd.notna(row['OPV 2nd (Col 6)']):
        if row['OPV 2nd (Col 6)'] > row['OPV 1st (Col 5)']: violations['OPV (1st < 2nd < 3rd)'] += 1
    if pd.notna(row['OPV 2nd (Col 6)']) and pd.notna(row['OPV 3rd (Col 7)']):
        if row['OPV 3rd (Col 7)'] > row['OPV 2nd (Col 6)']: violations['OPV (1st < 2nd < 3rd)'] += 1
    
    if pd.notna(row['fIPV 1st (Col 8)']) and pd.notna(row['fIPV 2nd (Col 9)']):
        if row['fIPV 2nd (Col 9)'] > row['fIPV 1st (Col 8)']: violations['fIPV (1st < 2nd)'] += 1
    
    if pd.notna(row['PCV 1st (Col 10)']) and pd.notna(row['PCV 2nd (Col 11)']):
        if row['PCV 2nd (Col 11)'] > row['PCV 1st (Col 10)']: violations['PCV (1st < 2nd < 3rd)'] += 1
    if pd.notna(row['PCV 2nd (Col 11)']) and pd.notna(row['PCV 3rd (Col 12)']):
        if row['PCV 3rd (Col 12)'] > row['PCV 2nd (Col 11)']: violations['PCV (1st < 2nd < 3rd)'] += 1
    
    if pd.notna(row['Penta 1st (Col 13)']) and pd.notna(row['Penta 2nd (Col 14)']):
        if row['Penta 2nd (Col 14)'] > row['Penta 1st (Col 13)']: violations['Penta (1st < 2nd < 3rd)'] += 1
    if pd.notna(row['Penta 2nd (Col 14)']) and pd.notna(row['Penta 3rd (Col 15)']):
        if row['Penta 3rd (Col 15)'] > row['Penta 2nd (Col 14)']: violations['Penta (1st < 2nd < 3rd)'] += 1
    
    if pd.notna(row['MR 1st (Col 16)']) and pd.notna(row['MR 2nd (Col 17)']):
        if row['MR 2nd (Col 17)'] > row['MR 1st (Col 16)']: violations['MR (1st < 2nd)'] += 1

viol_df = pd.DataFrame(list(violations.items()), columns=['Vaccine Family', 'Violations'])
viol_df = viol_df.sort_values(by='Violations', ascending=False)

plt.figure(figsize=(10, 5))
sns.barplot(data=viol_df, x='Violations', y='Vaccine Family', palette="Reds_r")
plt.title("Logical Drop-out Violations by Vaccine Family", pad=15)
plt.xlabel("Total Logical Violations Found")
plt.ylabel("Vaccine Family")
plt.tight_layout()
plt.savefig(f"{output_dir}/fig_violation_frequencies.png")
plt.close()
print(f"Generated: {output_dir}/fig_violation_frequencies.png")

print(f"\nAll publication-quality figures successfully saved to {output_dir}/")
