import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from statsmodels.tsa.seasonal import seasonal_decompose

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

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 3 - STEP 3.1: CLASSICAL SEASONAL DECOMPOSITION")
    print("=" * 60)
    
    # Define paths
    cleaned_data_path = project_root / "thesis" / "outputs" / "tables" / "Indicators_Cleaned.csv"
    figures_dir = project_root / "thesis" / "outputs" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    if cleaned_data_path.exists():
        print(f"Loading cleaned indicators from: {cleaned_data_path}")
        df = pd.read_csv(cleaned_data_path)
        
        # Generate dummy datetime index starting 2020-07-01 (Shrawan 2077/78)
        # to ensure chronological monthly spacing.
        df['Date'] = pd.date_range(start='2020-07-01', periods=len(df), freq='MS')
        df.set_index('Date', inplace=True)
        
        # Selected key indicators for Step 3.1
        target_indicators = ['BCG_Coverage', 'Penta_1_Coverage', 'Penta_Dropout']
        
        for indicator in target_indicators:
            if indicator in df.columns:
                run_classical_decomposition(df, indicator, figures_dir)
            else:
                print(f"⚠️ Indicator not found in dataset columns: {indicator}")
    else:
        print(f"❌ Cleaned dataset not found at: {cleaned_data_path}")
        
    print("\n✅ STEP 3.1 COMPLETE")
    print("=" * 60)
