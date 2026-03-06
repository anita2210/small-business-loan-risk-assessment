import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, classification_report
import pickle

# Load data
loans = pd.read_csv('../data/loans_sample.csv')
print(f"loaded {len(loans)} rows")

# Create target
# DEFAULT DEFINITION (consistent across all files):
# is_default = 1 if chgoffdate has an actual date value
# is_default = 0 if chgoffdate is NULL, empty string, or 'N' (not charged off)
# This matches the SQL definition in analysis_queries.sql
loans['is_default'] = loans['chgoffdate'].apply(
    lambda x: 0 if (pd.isna(x) or str(x).strip() in ['N', '']) else 1
)
defaults = loans['is_default'].sum()
print(f"defaults: {defaults} ({defaults/len(loans)*100:.1f}%)")

# ENHANCED FEATURE ENGINEERING
# Sector features
loans['sector'] = loans['naics'].astype(str).str[:2]
loans['sector_num'] = pd.to_numeric(loans['sector'], errors='coerce').fillna(0)

# High-risk sectors (from our analysis)
high_risk_sectors = ['52', '53', '48', '51', '56']  # Finance, RE, Transport, Info, Admin
medium_risk_sectors = ['49', '23', '45', '61']
loans['sector_high_risk'] = loans['sector'].apply(lambda x: 1 if x in high_risk_sectors else 0)
loans['sector_medium_risk'] = loans['sector'].apply(lambda x: 1 if x in medium_risk_sectors else 0)

# Business maturity
loans['is_new'] = loans['newexist'].apply(lambda x: 1 if x == 2 else 0)
loans['is_established'] = loans['newexist'].apply(lambda x: 1 if x == 0 else 0)
loans['is_recent'] = loans['newexist'].apply(lambda x: 1 if x == 1 else 0)

# Loan characteristics
loans['term_val'] = pd.to_numeric(loans['term'], errors='coerce').fillna(0)
loans['employees'] = pd.to_numeric(loans['noemp'], errors='coerce').fillna(0)
loans['jobs_created'] = pd.to_numeric(loans['createjob'], errors='coerce').fillna(0)
loans['jobs_retained'] = pd.to_numeric(loans['retainedjob'], errors='coerce').fillna(0)

# Location
loans['urban'] = loans['urbanrural'].apply(lambda x: 1 if x == 1 else 0)
loans['rural'] = loans['urbanrural'].apply(lambda x: 1 if x == 2 else 0)

# Loan type flags
loans['has_revline'] = loans['revlinecr'].apply(lambda x: 1 if x == 'Y' else 0)
loans['is_lowdoc'] = loans['lowdoc'].apply(lambda x: 1 if x == 'Y' else 0)

# Franchise
loans['is_franchise'] = loans['franchisecode'].apply(lambda x: 0 if (pd.isna(x) or x == 0 or x == '0') else 1)

# Loan amount
def clean_amt(val):
    if pd.isna(val):
        return 0
    s = str(val).replace('$', '').replace(',', '').replace('"', '').strip()
    try:
        return float(s)
    except:
        return 0

loans['amount'] = loans['disbursementgross'].apply(clean_amt)

# NEW: Derived features
loans['amount_per_employee'] = loans.apply(
    lambda r: r['amount'] / r['employees'] if r['employees'] > 0 else r['amount'], axis=1
)

loans['amount_per_job_created'] = loans.apply(
    lambda r: r['amount'] / r['jobs_created'] if r['jobs_created'] > 0 else r['amount'], axis=1
)

# Loan size categories
loans['small_loan'] = loans['amount'].apply(lambda x: 1 if x < 50000 else 0)
loans['medium_loan'] = loans['amount'].apply(lambda x: 1 if 50000 <= x < 250000 else 0)
loans['large_loan'] = loans['amount'].apply(lambda x: 1 if x >= 250000 else 0)

# Term categories
loans['short_term'] = loans['term_val'].apply(lambda x: 1 if x < 120 else 0)
loans['long_term'] = loans['term_val'].apply(lambda x: 1 if x >= 240 else 0)
print("\n--- TERM_VAL INVESTIGATION ---")
print("Default rate by short_term flag:")
print(loans.groupby('short_term')['is_default'].mean())
print("\nDefault rate by long_term flag:")
print(loans.groupby('long_term')['is_default'].mean())
print(f"\nCorrelation between term_val and is_default: {loans['term_val'].corr(loans['is_default']):.4f}")
# Geographic risk
high_risk_states = ['DC', 'FL', 'GA', 'NV', 'MD']
medium_risk_states = ['IL', 'NY', 'WV', 'MI', 'OH']
low_risk_states = ['TX', 'LA', 'SC', 'IA', 'NE']

loans['state_high_risk'] = loans['state'].apply(lambda x: 1 if x in high_risk_states else 0)
loans['state_medium_risk'] = loans['state'].apply(lambda x: 1 if x in medium_risk_states else 0)
loans['state_low_risk'] = loans['state'].apply(lambda x: 1 if x in low_risk_states else 0)

# NEW: Combined risk factors
loans['double_risk'] = loans.apply(
    lambda r: 1 if (r['sector_high_risk'] == 1 and r['state_high_risk'] == 1) else 0, axis=1
)

loans['triple_risk'] = loans.apply(
    lambda r: 1 if (r['is_new'] == 1 and r['sector_high_risk'] == 1 and r['state_high_risk'] == 1) else 0, axis=1
)


# Feature list
features = [
    'amount', 'term_val', 'employees', 'jobs_created', 'jobs_retained',
    'is_new', 'is_established', 'is_recent',
    'urban', 'rural', 'has_revline', 'is_lowdoc', 'is_franchise',
    'sector_high_risk', 'sector_medium_risk', 'sector_num',
    'state_high_risk', 'state_medium_risk', 'state_low_risk',
    'small_loan', 'medium_loan', 'large_loan',
    'short_term', 'long_term',
    'amount_per_employee', 'amount_per_job_created',
    'double_risk', 'triple_risk'
]
print(f"features ready: {len(features)}")
# Prepare
df = loans[features + ['is_default']].copy()
df = df.fillna(0)
df = df.replace([np.inf, -np.inf], 0)

# Cap extreme values
df['amount_per_employee'] = df['amount_per_employee'].clip(upper=df['amount_per_employee'].quantile(0.99))
df['amount_per_job_created'] = df['amount_per_job_created'].clip(upper=df['amount_per_job_created'].quantile(0.99))

X = df[features]
y = df['is_default']
print(f"dataset shape: {df.shape}")

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
print(f"train: {len(X_train)}  test: {len(X_test)}")

# Scale
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)


# Train BOTH models
lr_model = LogisticRegression(max_iter=1000, random_state=42, solver='lbfgs', class_weight='balanced')
lr_model.fit(X_train_scaled, y_train)
print("fitting random forest")
rf_model = RandomForestClassifier(
    n_estimators=100,
    max_depth=15,
    min_samples_split=50,
    min_samples_leaf=20,
    random_state=42,
    class_weight='balanced',
    n_jobs=-1
)
rf_model.fit(X_train, y_train)  # Note: Random Forest doesn't need scaling
print("fitting logistic regression")

# Evaluate BOTH

lr_pred = lr_model.predict(X_test_scaled)
lr_proba = lr_model.predict_proba(X_test_scaled)[:, 1]

lr_acc = accuracy_score(y_test, lr_pred)
lr_prec = precision_score(y_test, lr_pred)
lr_rec = recall_score(y_test, lr_pred)
lr_f1 = f1_score(y_test, lr_pred)
lr_auc = roc_auc_score(y_test, lr_proba)

print(f"Accuracy:  {lr_acc*100:.2f}%")
print(f"Precision: {lr_prec*100:.2f}%")
print(f"Recall:    {lr_rec*100:.2f}%")
print(f"F1 Score:  {lr_f1*100:.2f}%")
print(f"ROC AUC:   {lr_auc*100:.2f}%")
print("\nlogistic regression:")
print(f"  acc={lr_acc:.3f}  auc={lr_auc:.3f}")


rf_pred = rf_model.predict(X_test)
rf_proba = rf_model.predict_proba(X_test)[:, 1]

rf_acc = accuracy_score(y_test, rf_pred)
rf_prec = precision_score(y_test, rf_pred)
rf_rec = recall_score(y_test, rf_pred)
rf_f1 = f1_score(y_test, rf_pred)
rf_auc = roc_auc_score(y_test, rf_proba)

cm = confusion_matrix(y_test, rf_pred)
tn, fp, fn, tp = cm.ravel()

print("\nConfusion Matrix:")
print(f"  Correct Non-Defaults: {tn:,}")
print(f"  False Alarms:         {fp:,}")
print(f"  Missed Defaults:      {fn:,}")
print(f"  Correct Defaults:     {tp:,}")


# Feature importance (Random Forest)
feature_importance = pd.DataFrame({
    'feature': features,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)

print("\nfeature importances (top 15):")
for i, row in feature_importance.head(15).iterrows():
    print(f"  {row['feature']:<28} {row['importance']:.4f}")
# Save BEST model
best_model = rf_model if rf_acc > lr_acc else lr_model
best_model_name = "Random Forest" if rf_acc > lr_acc else "Logistic Regression"
best_acc = rf_acc if rf_acc > lr_acc else lr_acc
best_auc = rf_auc if rf_acc > lr_acc else lr_auc
with open('trained_model.pkl', 'wb') as f:
    pickle.dump(best_model, f)
with open('scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)
with open('feature_list.pkl', 'wb') as f:
    pickle.dump(features, f)
# Save performance
with open('model_performance.txt', 'w') as f:
    f.write("SBA LOAN DEFAULT RISK PREDICTION MODEL\n")
    f.write(f"Model Type: {best_model_name}\n")
    f.write(f"Training Date: February 18, 2026\n")
    f.write(f"Dataset: {len(loans):,} loans ({defaults:,} defaults)\n")
    f.write(f"Features: {len(features)} engineered features\n\n")
    f.write("PERFORMANCE METRICS:\n")
    f.write(f"Accuracy:  {best_acc*100:.2f}%\n")
    f.write(f"ROC AUC:   {best_auc*100:.2f}%\n\n")
    
    if rf_acc > lr_acc:
        f.write("RANDOM FOREST RESULTS:\n")
        f.write(f"Accuracy:  {rf_acc*100:.2f}%\n")
        f.write(f"Precision: {rf_prec*100:.2f}%\n")
        f.write(f"Recall:    {rf_rec*100:.2f}%\n")
        f.write(f"F1 Score:  {rf_f1*100:.2f}%\n")
        f.write(f"ROC AUC:   {rf_auc*100:.2f}%\n\n")
    else:
        f.write("LOGISTIC REGRESSION RESULTS:\n")
        f.write(f"Accuracy:  {lr_acc*100:.2f}%\n")
        f.write(f"Precision: {lr_prec*100:.2f}%\n")
        f.write(f"Recall:    {lr_rec*100:.2f}%\n")
        f.write(f"F1 Score:  {lr_f1*100:.2f}%\n")
        f.write(f"ROC AUC:   {lr_auc*100:.2f}%\n\n")
    
    f.write("CONFUSION MATRIX:\n")
    f.write(f"True Negatives:  {tn:,}\n")
    f.write(f"False Positives: {fp:,}\n")
    f.write(f"False Negatives: {fn:,}\n")
    f.write(f"True Positives:  {tp:,}\n\n")
    
    f.write("TOP 15 FEATURES:\n")
    for i, row in feature_importance.head(15).iterrows():
        f.write(f"{row['feature']:28s} : {row['importance']:.4f}\n")

print("model saved to models/")

# Business insights
# top features
print("\ntop 5 features:")
for rank, (i, row) in enumerate(feature_importance.head(5).iterrows(), 1):
    print(f"  {rank}. {row['feature']} ({row['importance']:.4f})")
print(f"\nbest model: {'rf' if rf_acc > lr_acc else 'lr'}  acc={best_acc:.3f}  auc={best_auc:.3f}")