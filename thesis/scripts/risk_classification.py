import os
import sys
import pandas as pd
import numpy as np
import warnings
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

warnings.filterwarnings('ignore')

# Add project root and script directory to path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(current_dir))

# Import shared Data Prep engine from Step 4.1
from predictive_modeling import ImmunizationDataPrep

def evaluate_classification(y_true, y_pred, y_prob):
    """
    Computes classification evaluation metrics, handling single-class cases safely.
    """
    acc = accuracy_score(y_true, y_pred)
    
    # Use zero_division=0 to prevent warnings and set to 0.0 if undefined
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    # ROC-AUC is only defined if both classes (0 and 1) are present in y_true
    if len(np.unique(y_true)) > 1 and y_prob is not None:
        try:
            auc = roc_auc_score(y_true, y_prob)
        except Exception:
            auc = np.nan
    else:
        auc = np.nan
        
    return acc, prec, rec, f1, auc

def run_classification_pipeline(prep, dataset_type, output_dir):
    """
    Runs the early-warning risk classification pipeline (Logistic Regression,
    Random Forest, and Gradient Boosting Classifiers) on all 24 indicators.
    """
    print(f"\n--- Running early-warning risk classification pipeline on {dataset_type.upper()} Dataset ---")
    
    # Identify indicators dynamically
    indicators = [col for col in prep.df_cleaned.columns if col.endswith('_Coverage') or col.endswith('_Dropout')]
    
    metrics_records = []
    predictions_records = []
    
    # Hyperparameter grids
    lr_param_grid = {
        'C': [0.1, 1.0, 10.0],
        'solver': ['liblinear']
    }
    
    rf_param_grid = {
        'n_estimators': [50, 100],
        'max_depth': [3, 5, None],
        'class_weight': ['balanced', None]
    }
    
    gb_param_grid = {
        'n_estimators': [50, 100],
        'learning_rate': [0.05, 0.1],
        'max_depth': [3, 4]
    }
    
    for idx, col in enumerate(indicators):
        # Fetch ML feature splits
        X_train, X_test, y_train, y_test = prep.prepare_ml_features(dataset_type, col)
        
        if len(X_train) < 10:
            continue
            
        # Map target values to binary risk labels:
        # Coverage Shortfall = 1 if Coverage < 90% else 0
        # High Dropout = 1 if Dropout > 10% else 0
        if col.endswith('_Coverage'):
            y_train_bin = (y_train < 90.0).astype(int)
            y_test_bin = (y_test < 90.0).astype(int)
            risk_type = "Coverage_Shortfall (<90%)"
        else:
            y_train_bin = (y_train > 10.0).astype(int)
            y_test_bin = (y_test > 10.0).astype(int)
            risk_type = "High_Dropout (>10%)"
            
        # Check if the training set contains both classes.
        # If it only contains 0s (no historical risk violations), the classifier cannot learn.
        unique_classes = np.unique(y_train_bin)
        if len(unique_classes) < 2:
            print(f"[{idx+1}/{len(indicators)}] Skipping {col:<20} | Reason: No historical risk state variance (all {unique_classes[0]}s)")
            continue
            
        print(f"[{idx+1}/{len(indicators)}] Modeling early-warning risk for {col:<20} | Type: {risk_type}")
        
        # Determine CV splits dynamically to prevent crashes
        n_splits = min(3, len(X_train) // 5)
        n_splits = max(2, n_splits)
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        # 1. Logistic Regression Classifier
        lr_model = LogisticRegression(random_state=42)
        lr_grid = GridSearchCV(lr_model, lr_param_grid, cv=tscv, scoring='accuracy', n_jobs=-1)
        try:
            lr_grid.fit(X_train, y_train_bin)
            best_lr = lr_grid.best_estimator_
        except Exception:
            # Fallback to direct fit if CV folds lack binary class representation
            best_lr = LogisticRegression(random_state=42, solver='liblinear')
            best_lr.fit(X_train, y_train_bin)
            
        try:
            lr_pred = best_lr.predict(X_test)
            lr_prob = best_lr.predict_proba(X_test)[:, 1]
            lr_acc, lr_prec, lr_rec, lr_f1, lr_auc = evaluate_classification(y_test_bin, lr_pred, lr_prob)
        except Exception as e:
            print(f"  ❌ LR evaluation failed on {col}: {e}")
            lr_pred = np.zeros(len(y_test_bin))
            lr_prob = np.zeros(len(y_test_bin))
            lr_acc, lr_prec, lr_rec, lr_f1, lr_auc = np.nan, np.nan, np.nan, np.nan, np.nan
            
        # 2. Random Forest Classifier
        rf_model = RandomForestClassifier(random_state=42)
        rf_grid = GridSearchCV(rf_model, rf_param_grid, cv=tscv, scoring='accuracy', n_jobs=-1)
        try:
            rf_grid.fit(X_train, y_train_bin)
            best_rf = rf_grid.best_estimator_
        except Exception:
            best_rf = RandomForestClassifier(random_state=42)
            best_rf.fit(X_train, y_train_bin)
            
        try:
            rf_pred = best_rf.predict(X_test)
            rf_prob = best_rf.predict_proba(X_test)[:, 1]
            rf_acc, rf_prec, rf_rec, rf_f1, rf_auc = evaluate_classification(y_test_bin, rf_pred, rf_prob)
        except Exception as e:
            print(f"  ❌ RF evaluation failed on {col}: {e}")
            rf_pred = np.zeros(len(y_test_bin))
            rf_prob = np.zeros(len(y_test_bin))
            rf_acc, rf_prec, rf_rec, rf_f1, rf_auc = np.nan, np.nan, np.nan, np.nan, np.nan
            
        # 3. Gradient Boosting Classifier
        gb_model = GradientBoostingClassifier(random_state=42)
        gb_grid = GridSearchCV(gb_model, gb_param_grid, cv=tscv, scoring='accuracy', n_jobs=-1)
        try:
            gb_grid.fit(X_train, y_train_bin)
            best_gb = gb_grid.best_estimator_
        except Exception:
            best_gb = GradientBoostingClassifier(random_state=42)
            best_gb.fit(X_train, y_train_bin)
            
        try:
            gb_pred = best_gb.predict(X_test)
            gb_prob = best_gb.predict_proba(X_test)[:, 1]
            gb_acc, gb_prec, gb_rec, gb_f1, gb_auc = evaluate_classification(y_test_bin, gb_pred, gb_prob)
        except Exception as e:
            print(f"  ❌ GB evaluation failed on {col}: {e}")
            gb_pred = np.zeros(len(y_test_bin))
            gb_prob = np.zeros(len(y_test_bin))
            gb_acc, gb_prec, gb_rec, gb_f1, gb_auc = np.nan, np.nan, np.nan, np.nan, np.nan
            
        # Append metrics
        metrics_records.append({
            'Indicator': col,
            'Risk_Type': risk_type,
            'LR_Accuracy': lr_acc, 'LR_Precision': lr_prec, 'LR_Recall': lr_rec, 'LR_F1': lr_f1, 'LR_AUC': lr_auc,
            'RF_Accuracy': rf_acc, 'RF_Precision': rf_prec, 'RF_Recall': rf_rec, 'RF_F1': rf_f1, 'RF_AUC': rf_auc,
            'GB_Accuracy': gb_acc, 'GB_Precision': gb_prec, 'GB_Recall': gb_rec, 'GB_F1': gb_f1, 'GB_AUC': gb_auc
        })
        
        # Append forecasts for each month in y_test, mapping back to original Nepali calendar fields
        df_meta = prep.df_cleaned if dataset_type == 'cleaned' else prep.df_raw
        for idx_t, date in enumerate(y_test.index):
            row_meta = df_meta.loc[date]
            fiscal_year = row_meta['Fiscal Year']
            month_no = row_meta['Month No.']
            month_en = row_meta['Month (EN)']
            month_np = row_meta['Month (NP)']
            
            predictions_records.append({
                'Indicator': col,
                'Fiscal Year': fiscal_year,
                'Month No.': month_no,
                'Month (EN)': month_en,
                'Month (NP)': month_np,
                'Actual_Risk': y_test_bin.iloc[idx_t],
                'LR_Risk_Prob': lr_prob[idx_t],
                'RF_Risk_Prob': rf_prob[idx_t],
                'GB_Risk_Prob': gb_prob[idx_t]
            })
            
    # Save files to workspace
    metrics_df = pd.DataFrame(metrics_records)
    predictions_df = pd.DataFrame(predictions_records)
    
    metrics_path = output_dir / f"metrics_classification_{dataset_type}.csv"
    predictions_path = output_dir / f"predictions_classification_{dataset_type}.csv"
    
    metrics_df.to_csv(metrics_path, index=False)
    predictions_df.to_csv(predictions_path, index=False)
    
    print(f"✅ Saved metrics to: {metrics_path}")
    print(f"✅ Saved forecasts to: {predictions_path}")
    
    # Print summary averages for classifiers
    print(f"Average RF Early-Warning Accuracy: {metrics_df['RF_Accuracy'].mean():.4f}")
    print(f"Average RF Early-Warning F1-Score: {metrics_df['RF_F1'].mean():.4f}")

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 4 - STEP 4.5: EARLY-WARNING RISK CLASSIFICATION PIPELINE")
    print("=" * 60)
    
    # Paths
    raw_csv = project_root / "thesis" / "outputs" / "tables" / "Indicators_Raw.csv"
    cleaned_csv = project_root / "thesis" / "outputs" / "tables" / "Indicators_Cleaned.csv"
    tables_dir = project_root / "thesis" / "outputs" / "tables"
    
    prep = ImmunizationDataPrep(raw_csv, cleaned_csv)
    
    # Run pipeline for both Raw and Cleaned
    run_classification_pipeline(prep, 'raw', tables_dir)
    run_classification_pipeline(prep, 'cleaned', tables_dir)
    
    print("\n✅ STEP 4.5 COMPLETE")
    print("=" * 60)
