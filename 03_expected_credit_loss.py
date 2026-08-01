import pandas as pd

def calculate_ecl_and_export():
    df = pd.read_csv("data/credit_underwriting_scored.csv")
    
    # Baseline Assumption: 45% Loss Given Default for unsecured loans
    LGD = 0.45  
    
    # 1. Compute Financial Risk Metrics
    df['EAD'] = df['AMT_CREDIT']
    df['PD'] = df['PROBABILITY_OF_DEFAULT']
    df['EXPECTED_LOSS'] = df['PD'] * df['EAD'] * LGD
    
    # 2. Overwrite CSV so Tableau has access to EAD, PD, and EXPECTED_LOSS
    df.to_csv("data/credit_underwriting_scored.csv", index=False)
    print("Updated 'data/credit_underwriting_scored.csv' with EAD, PD, and EXPECTED_LOSS columns.")
    
    # 3. Aggregate portfolio loss metrics across Risk Tiers
    portfolio_summary = df.groupby('RISK_TIER', observed=False).agg(
        Total_Applicants=('SK_ID_CURR', 'count'),
        Average_PD=('PD', 'mean'),
        Total_Exposure_EAD=('EAD', 'sum'),
        Total_Expected_Loss=('EXPECTED_LOSS', 'sum')
    ).reset_index()
    
    portfolio_summary['ECL_Provision_Ratio_%'] = (
        portfolio_summary['Total_Expected_Loss'] / portfolio_summary['Total_Exposure_EAD']
    ) * 100
    
    print("="*70)
    print("CREDIT PORTFOLIO EXPECTED CREDIT LOSS (ECL) SUMMARY")
    print("="*70)
    print(portfolio_summary.to_string(index=False))
    
    # 4. Export to Excel for Portfolio Provisioning with all required columns
    export_cols = [
        'SK_ID_CURR', 
        'AMT_INCOME_TOTAL', 
        'AMT_CREDIT', 
        'PAYMENT_BURDEN_RATIO', 
        'PD', 
        'EAD', 
        'EXPECTED_LOSS', 
        'RISK_TIER'
    ]
    
    with pd.ExcelWriter("excel/portfolio_credit_loss_model.xlsx", engine='openpyxl') as writer:
        portfolio_summary.to_excel(writer, sheet_name="Portfolio Risk Summary", index=False)
        df[export_cols].head(1000).to_excel(writer, sheet_name="Sample Underwriting Decisions", index=False)
        
    print("\nSaved financial loss model to 'excel/portfolio_credit_loss_model.xlsx'")

if __name__ == "__main__":
    calculate_ecl_and_export()