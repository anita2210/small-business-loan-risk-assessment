import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, classification_report
import pickle

print("Libraries imported!\n")

# Load data
print("[1/8] Loading data...")
loans = pd.read_csv('../data/loans_sample.csv')
print(f"✓ Loaded {len(loans):,} loans\n")

# Create target
print("[2/8] Creating target variable...")
loans['is_default'] = loans['chgoffdate'].apply(
    lambda x: 0 if (pd.isna(x) or str(x) in ['N', '']) else 1
)
defaults = loans['is_default'].sum()
print(f"✓ Defaults: {defaults:,} ({defaults/len(loans)*100:.1f}%)\n")

# ENHANCED FEATURE ENGINEERING
print("[3/8] Engineering features (ENHANCED)...")

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

print("✓ 30+ features engineered!\n")

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

# Prepare
print("[4/8] Preparing dataset...")
df = loans[features + ['is_default']].copy()
df = df.fillna(0)
df = df.replace([np.inf, -np.inf], 0)

# Cap extreme values
df['amount_per_employee'] = df['amount_per_employee'].clip(upper=df['amount_per_employee'].quantile(0.99))
df['amount_per_job_created'] = df['amount_per_job_created'].clip(upper=df['amount_per_job_created'].quantile(0.99))

X = df[features]
y = df['is_default']
print(f" Dataset: {len(df):,} records with {len(features)} features\n")

# Split
print("[5/8] Splitting data...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
print(f" Train: {len(X_train):,} | Test: {len(X_test):,}\n")

# Scale
print("[6/8] Scaling features...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
print(" Scaled!\n")

# Train BOTH models
print("[7/8] Training models...")
print("Training Logistic Regression...")
lr_model = LogisticRegression(max_iter=1000, random_state=42, solver='lbfgs', class_weight='balanced')
lr_model.fit(X_train_scaled, y_train)
print(" Logistic Regression trained!")

print("\nTraining Random Forest (this takes 1-2 minutes)...")
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
print(" Random Forest trained!\n")

# Evaluate BOTH
print("[8/8] Evaluating models...")
print("LOGISTIC REGRESSION PERFORMANCE")


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

print("RANDOM FOREST PERFORMANCE")


rf_pred = rf_model.predict(X_test)
rf_proba = rf_model.predict_proba(X_test)[:, 1]

rf_acc = accuracy_score(y_test, rf_pred)
rf_prec = precision_score(y_test, rf_pred)
rf_rec = recall_score(y_test, rf_pred)
rf_f1 = f1_score(y_test, rf_pred)
rf_auc = roc_auc_score(y_test, rf_proba)

cm = confusion_matrix(y_test, rf_pred)
tn, fp, fn, tp = cm.ravel()

print(f"Accuracy:  {rf_acc*100:.2f}% ⭐")
print(f"Precision: {rf_prec*100:.2f}%")
print(f"Recall:    {rf_rec*100:.2f}%")
print(f"F1 Score:  {rf_f1*100:.2f}%")
print(f"ROC AUC:   {rf_auc*100:.2f}% ⭐")

print("\nConfusion Matrix:")
print(f"  Correct Non-Defaults: {tn:,}")
print(f"  False Alarms:         {fp:,}")
print(f"  Missed Defaults:      {fn:,}")
print(f"  Correct Defaults:     {tp:,}")


print(f" WINNER: {'Random Forest' if rf_acc > lr_acc else 'Logistic Regression'}")
print(f"   Accuracy improved by {abs(rf_acc - lr_acc)*100:.1f} percentage points!")

# Feature importance (Random Forest)
print("\nTOP 15 MOST IMPORTANT FEATURES (Random Forest):")
feature_importance = pd.DataFrame({
    'feature': features,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)

for i, row in feature_importance.head(15).iterrows():
    bar_length = int(row['importance'] * 50)
    bar = '█' * bar_length
    print(f"{row['feature']:28s} {bar} {row['importance']:.4f}")

# Save BEST model
best_model = rf_model if rf_acc > lr_acc else lr_model
best_model_name = "Random Forest" if rf_acc > lr_acc else "Logistic Regression"
best_acc = rf_acc if rf_acc > lr_acc else lr_acc
best_auc = rf_auc if rf_acc > lr_acc else lr_auc

print(f"\n[SAVING] Saving {best_model_name} model...")
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

print(f" {best_model_name} model saved!")
print(" Performance report saved!\n")

# Business insights
print("KEY INSIGHTS FROM MODEL")

print("\n STRONGEST DEFAULT PREDICTORS:")
top_5 = feature_importance.head(5)
for i, row in top_5.iterrows():
    print(f"  {i+1}. {row['feature']}")

print(f"\n BUSINESS RECOMMENDATION:")
if 'is_new' in top_5['feature'].values:
    print("    New businesses are a major risk factor - require extra scrutiny!")
if 'state_high_risk' in top_5['feature'].values:
    print("    Geographic location matters - adjust pricing by state!")
if 'sector_high_risk' in top_5['feature'].values:
    print("    Industry sector is critical - avoid high-risk sectors!")
if 'amount' in top_5['feature'].values:
    print("    Loan size impacts risk - don't assume small = safe!")


print(" MODEL TRAINING COMPLETE!")
print(f"\n Final Accuracy: {best_acc*100:.2f}%")
print(f" ROC AUC Score: {best_auc*100:.2f}%")
print("\n Ready to integrate into dashboard!")