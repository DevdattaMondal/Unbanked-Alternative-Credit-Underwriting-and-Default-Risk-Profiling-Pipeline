import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler


def run_feature_engineering_and_scoring():
    df = pd.read_csv("data/credit_risk_features.csv")
    
    # 1. Feature Engineering
    df['PAYMENT_BURDEN_RATIO'] = df['AMT_ANNUITY'] / (df['AMT_INCOME_TOTAL'] + 1)
    df['CREDIT_TO_INCOME_RATIO'] = df['AMT_CREDIT'] / (df['AMT_INCOME_TOTAL'] + 1)
    df['AGE_YEARS'] = np.abs(df['DAYS_BIRTH']) / 365.25
    df['EMPLOYMENT_YEARS'] = np.where(df['DAYS_EMPLOYED'] > 0, 0, np.abs(df['DAYS_EMPLOYED']) / 365.25)
    
    # Alternative Behavioral Index
    df['BEHAVIORAL_RISK_INDEX'] = (
        (df['count_late_payments'] * 1.5) + 
        (df['avg_payment_delay_days'].clip(lower=0) * 0.8) + 
        (df['bureau_overdue_counts'] * 2.0)
    )
    
    # 2. Seaborn Diagnostic Visualizations
    plt.figure(figsize=(10, 5))
    sns.kdeplot(data=df, x='PAYMENT_BURDEN_RATIO', hue='TARGET', common_norm=False, palette='Set1', clip=(0, 1))
    plt.title('Payment Burden Ratio Density Distribution by Default Status (TARGET)')
    plt.xlabel('Payment Burden Ratio (Annuity / Total Income)')
    plt.ylabel('Density')
    plt.tight_layout()
    plt.savefig("data/payment_burden_density.png", dpi=300)
    print("Saved risk diagnostic plot to 'data/payment_burden_density.png'")
    
    # 3. Probability of Default (PD) Modeling
    feature_cols = [
        'PAYMENT_BURDEN_RATIO', 'CREDIT_TO_INCOME_RATIO', 'AGE_YEARS', 'EMPLOYMENT_YEARS',
        'avg_payment_delay_days', 'count_late_payments', 'avg_payment_ratio',
        'max_pos_dpd', 'total_bureau_credits', 'avg_bureau_utilization', 'BEHAVIORAL_RISK_INDEX'
    ]
    
    X = df[feature_cols]
    y = df['TARGET']
    
    imputer = SimpleImputer(strategy='median')
    scaler = StandardScaler()
    
    X_imp = imputer.fit_transform(X)
    X_scaled = scaler.fit_transform(X_imp)
    
    model = LogisticRegression(max_iter=1000, class_weight='balanced')
    model.fit(X_scaled, y)
    
    # Predict Probability of Default (PD)
    df['PROBABILITY_OF_DEFAULT'] = model.predict_proba(X_scaled)[:, 1]
    
    # Assign Credit Risk Tiers
    df['RISK_TIER'] = pd.qcut(df['PROBABILITY_OF_DEFAULT'], q=5, labels=['Very Low', 'Low', 'Medium', 'High', 'Very High'])
    
    df.to_csv("data/credit_underwriting_scored.csv", index=False)
    print("Saved scored underwriting pipeline to 'data/credit_underwriting_scored.csv'")

if __name__ == "__main__":
    run_feature_engineering_and_scoring()