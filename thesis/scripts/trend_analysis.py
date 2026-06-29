import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from statsmodels.tsa.seasonal import seasonal_decompose
from prophet import Prophet
import logging

# Disable Prophet diagnostic logging messages unless warnings/errors
logging.getLogger('prophet').setLevel(logging.WARNING)
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)

from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

# Add project root to path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

def run_classical_decomposition(df, indicator, output_dir):
    """
    Step 3.1: Applies classical seasonal decomposition (Additive)
    using statsmodels and saves the component subplots.
    """
    print(f"Running Classical Seasonal Decomposition (Additive) on: {indicator}")
    
    # Run seasonal decomposition with period=12 (yearly cycles)
    result = seasonal_decompose(df[indicator], model='additive', period=12)
    
    # Plot components manually for better styling
    fig, axes = plt.subplots(4, 1, figsize=(10, 8), sharex=True)
    
    # 1. Observed
    axes[0].plot(df.index, result.observed, color='#1f77b4', linewidth=2)
    axes[0].set_ylabel('Observed', fontsize=10, fontweight='bold')
    axes[0].set_title(f'Classical Seasonal Decomposition (Additive) - {indicator}', fontsize=12, fontweight='bold', pad=10)
    axes[0].grid(True, linestyle='--', alpha=0.5)
    
    # 2. Trend
    axes[1].plot(df.index, result.trend, color='#ff7f0e', linewidth=2)
    axes[1].set_ylabel('Trend', fontsize=10, fontweight='bold')
    axes[1].grid(True, linestyle='--', alpha=0.5)
    
    # 3. Seasonal
    axes[2].plot(df.index, result.seasonal, color='#2ca02c', linewidth=2)
    axes[2].set_ylabel('Seasonal', fontsize=10, fontweight='bold')
    axes[2].grid(True, linestyle='--', alpha=0.5)
    
    # 4. Residual (Noise)
    axes[3].scatter(df.index, result.resid, color='#d62728', alpha=0.7, edgecolors='none')
    axes[3].axhline(0, color='black', linestyle='-', linewidth=1)
    axes[3].set_ylabel('Residual', fontsize=10, fontweight='bold')
    axes[3].grid(True, linestyle='--', alpha=0.5)
    
    plt.xlabel('Date (Chronological Timeline)', fontsize=10, fontweight='bold')
    plt.tight_layout()
    
    # Save plot
    clean_name = indicator.lower().replace(' ', '_')
    plot_path = output_dir / f"classical_decomp_{clean_name}.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Saved classical decomposition plot to: {plot_path}")
    return result

def run_prophet_decomposition(df_input, indicator, output_dir):
    """
    Step 3.2: Performs robust seasonal decomposition using Prophet
    to isolate trend and yearly seasonality without losing edge data.
    """
    print(f"Running Prophet Decomposition on: {indicator}")
    
    # Prepare DataFrame for Prophet (columns must be 'ds' and 'y')
    prophet_df = pd.DataFrame({
        'ds': df_input.index,
        'y': df_input[indicator]
    }).reset_index(drop=True)
    
    # Initialize and fit Prophet model
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False
    )
    model.fit(prophet_df)
    
    # Predict in-sample to extract components
    forecast = model.predict(prophet_df)
    
    # Save the components plot using Prophet's built-in plotting utility
    fig = model.plot_components(forecast)
    fig.suptitle(f"Prophet Components Decomposition - {indicator}", y=1.02, fontsize=12, fontweight='bold')
    
    # Save plot
    clean_name = indicator.lower().replace(' ', '_')
    plot_path = output_dir / f"prophet_decomp_{clean_name}.png"
    fig.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    print(f"✅ Saved Prophet decomposition plot to: {plot_path}")
    return forecast

def run_acf_pacf_analysis(df, indicator, output_dir):
    """
    Step 3.4: Plots ACF and PACF side-by-side up to 24 lags
    to theoretically identify AR(p) and MA(q) terms.
    """
    print(f"Generating ACF/PACF plots for: {indicator}")
    
    # Extract series and drop NaNs
    series = df[indicator].dropna()
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot ACF (lags=24)
    plot_acf(series, lags=24, ax=axes[0], color='#1f77b4', vlines_kwargs={"colors": "#1f77b4"})
    axes[0].set_title(f'Autocorrelation (ACF) - {indicator}', fontsize=10, fontweight='bold')
    axes[0].grid(True, linestyle='--', alpha=0.5)
    
    # Plot PACF (lags=24)
    plot_pacf(series, lags=24, ax=axes[1], color='#d62728', vlines_kwargs={"colors": "#d62728"}, method='ywm')
    axes[1].set_title(f'Partial Autocorrelation (PACF) - {indicator}', fontsize=10, fontweight='bold')
    axes[1].grid(True, linestyle='--', alpha=0.5)
    
    fig.suptitle(f"ACF / PACF Diagnostic Profiling - {indicator}", fontsize=12, fontweight='bold', y=1.05)
    plt.tight_layout()
    
    # Save plot
    clean_name = indicator.lower().replace(' ', '_')
    plot_path = output_dir / f"acf_pacf_{clean_name}.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Saved ACF/PACF plot to: {plot_path}")

def run_adf_tests(raw_df, cleaned_df, output_table_dir):
    """
    Step 3.3: Performs Augmented Dickey-Fuller (ADF) tests to check if the
    series are stationary and determines the required order of differencing.
    Runs on all 18 coverage and 6 dropout series for both Raw and Cleaned datasets.
    """
    print("Running Augmented Dickey-Fuller (ADF) Stationarity Tests...")
    
    # Identify indicators dynamically (columns ending with _Coverage or _Dropout)
    indicators = [col for col in cleaned_df.columns if col.endswith('_Coverage') or col.endswith('_Dropout')]
    
    results = []
    
    for col in indicators:
        # Check if the column is present in both raw and cleaned dataframes
        if col not in raw_df.columns:
            print(f"⚠️ Skipping {col} (not found in Raw dataset)")
            continue
            
        # Get raw and cleaned series (dropping NaNs which represent pre-introduction months or missing values)
        raw_series = raw_df[col].dropna()
        cleaned_series = cleaned_df[col].dropna()
        
        # --- 1. Raw Series ADF ---
        raw_stat, raw_p, raw_d = np.nan, np.nan, "N/A"
        raw_stationary = "Unknown"
        if len(raw_series) >= 10:
            try:
                raw_res = adfuller(raw_series)
                raw_stat = raw_res[0]
                raw_p = raw_res[1]
                raw_stationary = "Yes" if raw_p < 0.05 else "No"
                
                # Check order of differencing
                if raw_p < 0.05:
                    raw_d = "0"
                else:
                    raw_diff = raw_series.diff().dropna()
                    raw_diff_res = adfuller(raw_diff)
                    raw_d = "1" if raw_diff_res[1] < 0.05 else ">=2"
            except Exception as e:
                print(f"⚠️ Error running ADF on Raw {col}: {e}")
        
        # --- 2. Cleaned Series ADF ---
        cleaned_stat, cleaned_p, cleaned_d = np.nan, np.nan, "N/A"
        cleaned_stationary = "Unknown"
        if len(cleaned_series) >= 10:
            try:
                cleaned_res = adfuller(cleaned_series)
                cleaned_stat = cleaned_res[0]
                cleaned_p = cleaned_res[1]
                cleaned_stationary = "Yes" if cleaned_p < 0.05 else "No"
                
                # Check order of differencing
                if cleaned_p < 0.05:
                    cleaned_d = "0"
                else:
                    cleaned_diff = cleaned_series.diff().dropna()
                    cleaned_diff_res = adfuller(cleaned_diff)
                    cleaned_d = "1" if cleaned_diff_res[1] < 0.05 else ">=2"
            except Exception as e:
                print(f"⚠️ Error running ADF on Cleaned {col}: {e}")
                
        results.append({
            'Indicator': col,
            'Raw_ADF_Stat': raw_stat,
            'Raw_P_Value': raw_p,
            'Raw_Stationary': raw_stationary,
            'Raw_Required_d': raw_d,
            'Cleaned_ADF_Stat': cleaned_stat,
            'Cleaned_P_Value': cleaned_p,
            'Cleaned_Stationary': cleaned_stationary,
            'Cleaned_Required_d': cleaned_d
        })
        
    # Compile and save
    results_df = pd.DataFrame(results)
    output_path = output_table_dir / "adf_stationarity_comparison.csv"
    results_df.to_csv(output_path, index=False)
    
    print(f"✅ Saved ADF stationarity comparison report to: {output_path}")
    
    # Print a small summary of stationary indicators
    raw_stat_count = (results_df['Raw_Stationary'] == 'Yes').sum()
    cleaned_stat_count = (results_df['Cleaned_Stationary'] == 'Yes').sum()
    print(f"Summary: Stationary Series (p < 0.05): Raw: {raw_stat_count}/24 | Cleaned: {cleaned_stat_count}/24")
    
    return results_df

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 3 - STEPS 3.1, 3.2 & 3.3: TREND AND STATIONARITY ANALYSIS")
    print("=" * 60)
    
    # Define paths
    raw_data_path = project_root / "thesis" / "outputs" / "tables" / "Indicators_Raw.csv"
    cleaned_data_path = project_root / "thesis" / "outputs" / "tables" / "Indicators_Cleaned.csv"
    figures_dir = project_root / "thesis" / "outputs" / "figures"
    tables_dir = project_root / "thesis" / "outputs" / "tables"
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    
    if cleaned_data_path.exists() and raw_data_path.exists():
        print(f"Loading datasets:\n - Raw: {raw_data_path}\n - Cleaned: {cleaned_data_path}")
        df_raw = pd.read_csv(raw_data_path)
        df_cleaned = pd.read_csv(cleaned_data_path)
        
        # Generate dummy datetime index starting 2020-07-01 (Shrawan 2077/78)
        # to ensure chronological monthly spacing for decomposition.
        df_cleaned['Date'] = pd.date_range(start='2020-07-01', periods=len(df_cleaned), freq='MS')
        df_cleaned.set_index('Date', inplace=True)
        
        df_raw['Date'] = pd.date_range(start='2020-07-01', periods=len(df_raw), freq='MS')
        df_raw.set_index('Date', inplace=True)
        
        # Selected key indicators
        target_indicators = ['BCG_Coverage', 'Penta_1_Coverage', 'Penta_Dropout']
        
        # Step 3.1: Classical Decomposition
        print("\n--- Running Classical Decomposition (Step 3.1) ---")
        for indicator in target_indicators:
            if indicator in df_cleaned.columns:
                run_classical_decomposition(df_cleaned, indicator, figures_dir)
                
        # Step 3.2: Prophet Decomposition
        print("\n--- Running Prophet Decomposition (Step 3.2) ---")
        for indicator in target_indicators:
            if indicator in df_cleaned.columns:
                run_prophet_decomposition(df_cleaned, indicator, figures_dir)
                
        # Step 3.3: Augmented Dickey-Fuller Tests
        print("\n--- Running ADF Stationarity Tests (Step 3.3) ---")
        run_adf_tests(df_raw, df_cleaned, tables_dir)
        
        # Step 3.4: Autocorrelation & Partial Autocorrelation Profiling
        print("\n--- Running ACF/PACF Diagnostic Profiling (Step 3.4) ---")
        for indicator in target_indicators:
            if indicator in df_cleaned.columns:
                run_acf_pacf_analysis(df_cleaned, indicator, figures_dir)
    else:
        print("❌ Dataset files not found. Make sure Phase 2 has been completed.")
        
    print("\n✅ STEP 3.4 COMPLETE")
    print("=" * 60)
