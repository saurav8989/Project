import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

class ImmunizationDataPrep:
    """
    Step 4.1: Feature Engineering & Train/Test Splitting Engine.
    Handles data loading, lag features (1, 2, 12), cyclical month encodings,
    and TCV pre-introduction exclusion rules.
    """
    def __init__(self, raw_path, cleaned_path):
        self.raw_path = Path(raw_path)
        self.cleaned_path = Path(cleaned_path)
        
        # Load datasets
        if not self.raw_path.exists() or not self.cleaned_path.exists():
            raise FileNotFoundError("Raw or Cleaned indicators dataset not found.")
            
        self.df_raw = pd.read_csv(self.raw_path)
        self.df_cleaned = pd.read_csv(self.cleaned_path)
        
        # Generate chronological datetime index starting 2020-07-01 (Shrawan 2077/78)
        self.df_raw['Date'] = pd.date_range(start='2020-07-01', periods=len(self.df_raw), freq='MS')
        self.df_raw.set_index('Date', inplace=True)
        
        self.df_cleaned['Date'] = pd.date_range(start='2020-07-01', periods=len(self.df_cleaned), freq='MS')
        self.df_cleaned.set_index('Date', inplace=True)

    def prepare_univariate_split(self, dataset_type, target_col):
        """
        Prepares raw target series for statistical forecasting (ARIMA, SARIMA, Prophet).
        Applies TCV pre-introduction exclusion rules.
        """
        df = self.df_cleaned if dataset_type == 'cleaned' else self.df_raw
        
        # Extract target series
        y = df[target_col].copy()
        
        # TCV Pre-introduction Exclusion Rule:
        # TCV was introduced in Month 21 (April 2022 / Baishak 2079).
        # We drop the first 20 months (rows 0 to 19) because the vaccine wasn't in schedule.
        if 'TCV' in target_col:
            y = y.iloc[20:]
            
        # Drop any remaining NaNs (relevant for Raw TCV or missing values)
        y = y.dropna()
        
        # Temporal Split:
        # Train: Months 1-48 (rows 0-47 in chronological alignment)
        # Test: Months 49-60 (rows 48-59 in chronological alignment)
        # Note: If TCV was sliced, the indices are shifted, but we still split temporally.
        # Since the total months is 60:
        # For non-TCV: train is first 48 rows, test is last 12 rows.
        # For TCV (40 months total): train is first 28 rows (representing months 21-48),
        # test is last 12 rows (representing months 49-60).
        if 'TCV' in target_col:
            train_y = y.iloc[:28]
            test_y = y.iloc[28:]
        else:
            train_y = y.iloc[:48]
            test_y = y.iloc[48:]
            
        return train_y, test_y

    def prepare_ml_features(self, dataset_type, target_col):
        """
        Prepares feature matrix (X) and target vector (y) for machine learning models (RF, GB).
        Engineers lag features (1, 2, 12) and cyclical month encodings.
        """
        df = self.df_cleaned if dataset_type == 'cleaned' else self.df_raw
        
        # Create a working copy
        work_df = df[[target_col, 'Month No.']].copy()
        
        # TCV Pre-introduction Exclusion Rule:
        if 'TCV' in target_col:
            work_df = work_df.iloc[20:]
            
        # 1. Cyclical Month Encodings
        work_df['Month_Sin'] = np.sin(2 * np.pi * work_df['Month No.'] / 12.0)
        work_df['Month_Cos'] = np.cos(2 * np.pi * work_df['Month No.'] / 12.0)
        
        # 2. Lag Features
        work_df['Lag_1'] = work_df[target_col].shift(1)
        work_df['Lag_2'] = work_df[target_col].shift(2)
        work_df['Lag_12'] = work_df[target_col].shift(12)
        
        # Drop rows with NaNs (which includes the 12 lag rows and any raw NaNs)
        ml_data = work_df.dropna()
        
        # Extract features (X) and target (y)
        X = ml_data[['Lag_1', 'Lag_2', 'Lag_12', 'Month_Sin', 'Month_Cos']]
        y = ml_data[target_col]
        
        # Temporal Split:
        # Since test set must be Year 5 (last 12 months, months 49-60):
        # We split based on the index position.
        # Total records for non-TCV after dropping 12 lags is 48.
        # Train: rows 0 to 35 (which correspond to months 13-48).
        # Test: rows 36 to 47 (which correspond to months 49-60).
        # For TCV (40 months total after slicing): after dropping 12 lags, total is 28.
        # Train: rows 0 to 15 (months 33-48).
        # Test: rows 16 to 27 (months 49-60).
        if 'TCV' in target_col:
            train_idx_end = 16
        else:
            train_idx_end = 36
            
        X_train, X_test = X.iloc[:train_idx_end], X.iloc[train_idx_end:]
        y_train, y_test = y.iloc[:train_idx_end], y.iloc[train_idx_end:]
        
        return X_train, X_test, y_train, y_test

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 4 - STEP 4.1: FEATURE ENGINEERING & SPLITTING VERIFICATION")
    print("=" * 60)
    
    # Define paths
    raw_csv = project_root / "thesis" / "outputs" / "tables" / "Input_Data" / "Indicators_Raw.csv"
    cleaned_csv = project_root / "thesis" / "outputs" / "tables" / "Input_Data" / "Indicators_Cleaned.csv"
    
    try:
        prep = ImmunizationDataPrep(raw_csv, cleaned_csv)
        print("✅ Successfully initialized Data Prep Engine.")
        
        # Verify splits on key target indicators: BCG, Penta 1, Penta Dropout, and TCV
        test_indicators = ['BCG_Coverage', 'Penta_1_Coverage', 'Penta_Dropout', 'TCV_Coverage']
        
        for dataset in ['raw', 'cleaned']:
            print(f"\n--- Dataset: {dataset.upper()} ---")
            for indicator in test_indicators:
                if indicator in prep.df_cleaned.columns:
                    # Univariate verification
                    train_y, test_y = prep.prepare_univariate_split(dataset, indicator)
                    print(f"Univariate {indicator:<20} | Train: {len(train_y)} months | Test: {len(test_y)} months")
                    
                    # ML verification
                    X_tr, X_te, y_tr, y_te = prep.prepare_ml_features(dataset, indicator)
                    print(f"ML Feature  {indicator:<20} | Train X: {X_tr.shape} y: {len(y_tr)} | Test X: {X_te.shape} y: {len(y_te)}")
                else:
                    print(f"⚠️ {indicator} not found in columns.")
                    
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        
    print("\n✅ STEP 4.1 COMPLETE")
    print("=" * 60)
