import duckdb
import os

DB_FILE = "credit_risk.db"
DATA_DIR = "data"

def stage_data_and_aggregate():
    con = duckdb.connect(DB_FILE)
    print("Connected to DuckDB for Credit Risk Pipeline...\n")
    
    # 1. Load CSVs into local DuckDB tables
    tables = ["application_train", "bureau", "POS_CASH_balance", "installments_payments"]
    for t in tables:
        csv_path = os.path.join(DATA_DIR, f"{t}.csv")
        if os.path.exists(csv_path):
            print(f"Loading '{t}.csv' into DuckDB...")
            con.execute(f"CREATE OR REPLACE TABLE {t} AS SELECT * FROM read_csv_auto('{csv_path}', ignore_errors=true);")
            count = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"Loaded '{t}': {count:,} records.")
    
    # 2. Extract aggregated client features via SQL CTEs
    feature_extraction_query = """
    WITH installment_features AS (
        SELECT 
            SK_ID_CURR,
            COUNT(SK_ID_PREV) AS total_installment_records,
            AVG(DAYS_ENTRY_PAYMENT - DAYS_INSTALMENT) AS avg_payment_delay_days,
            MAX(DAYS_ENTRY_PAYMENT - DAYS_INSTALMENT) AS max_payment_delay_days,
            SUM(CASE WHEN (DAYS_ENTRY_PAYMENT - DAYS_INSTALMENT) > 0 THEN 1 ELSE 0 END) AS count_late_payments,
            AVG(AMT_PAYMENT / NULLIF(AMT_INSTALMENT, 0)) AS avg_payment_ratio
        FROM installments_payments
        GROUP BY SK_ID_CURR
    ),
    pos_features AS (
        SELECT 
            SK_ID_CURR,
            AVG(SK_DPD) AS avg_pos_dpd,
            MAX(SK_DPD) AS max_pos_dpd
        FROM POS_CASH_balance
        GROUP BY SK_ID_CURR
    ),
    bureau_features AS (
        SELECT 
            SK_ID_CURR,
            COUNT(SK_ID_BUREAU) AS total_bureau_credits,
            SUM(CASE WHEN CREDIT_DAY_OVERDUE > 0 THEN 1 ELSE 0 END) AS bureau_overdue_counts,
            AVG(AMT_CREDIT_SUM_DEBT / NULLIF(AMT_CREDIT_SUM, 0)) AS avg_bureau_utilization
        FROM bureau
        GROUP BY SK_ID_CURR
    )
    SELECT 
        app.SK_ID_CURR,
        app.TARGET,
        app.NAME_CONTRACT_TYPE,
        app.CODE_GENDER,
        app.AMT_INCOME_TOTAL,
        app.AMT_CREDIT,
        app.AMT_ANNUITY,
        app.DAYS_BIRTH,
        app.DAYS_EMPLOYED,
        
        -- Joined behavioral aggregations
        COALESCE(inst.total_installment_records, 0) AS total_installment_records,
        COALESCE(inst.avg_payment_delay_days, 0) AS avg_payment_delay_days,
        COALESCE(inst.max_payment_delay_days, 0) AS max_payment_delay_days,
        COALESCE(inst.count_late_payments, 0) AS count_late_payments,
        COALESCE(inst.avg_payment_ratio, 1.0) AS avg_payment_ratio,
        
        COALESCE(pos.avg_pos_dpd, 0) AS avg_pos_dpd,
        COALESCE(pos.max_pos_dpd, 0) AS max_pos_dpd,
        
        COALESCE(bur.total_bureau_credits, 0) AS total_bureau_credits,
        COALESCE(bur.bureau_overdue_counts, 0) AS bureau_overdue_counts,
        COALESCE(bur.avg_bureau_utilization, 0) AS avg_bureau_utilization
    FROM application_train app
    LEFT JOIN installment_features inst ON app.SK_ID_CURR = inst.SK_ID_CURR
    LEFT JOIN pos_features pos ON app.SK_ID_CURR = pos.SK_ID_CURR
    LEFT JOIN bureau_features bur ON app.SK_ID_CURR = bur.SK_ID_CURR;
    """
    
    print("\nExecuting Feature Aggregation Query...")
    df_features = con.execute(feature_extraction_query).df()
    df_features.to_csv("data/credit_risk_features.csv", index=False)
    print(f"Feature Extraction Complete! Saved {len(df_features):,} rows to 'data/credit_risk_features.csv'.")
    con.close()

if __name__ == "__main__":
    stage_data_and_aggregate()