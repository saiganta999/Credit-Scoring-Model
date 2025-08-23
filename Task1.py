import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, classification_report, roc_curve, auc
from sklearn.utils import resample
import warnings
warnings.filterwarnings('ignore')
import joblib

np.random.seed(42)

def generate_credit_data(n_samples=10000):
    np.random.seed(42)
    
    age = np.random.normal(45, 15, n_samples).astype(int)
    age = np.clip(age, 18, 100)
    
    income = np.random.lognormal(10.5, 0.35, n_samples)
    income = np.clip(income, 20000, 200000)
    
    debt_to_income = np.random.beta(2, 5, n_samples) * 100
    credit_utilization = np.random.beta(3, 4, n_samples) * 100
    num_credit_lines = np.random.poisson(8, n_samples)
    num_credit_lines = np.clip(num_credit_lines, 1, 20)
    
    payment_history = np.random.beta(7, 3, n_samples) * 100
    
    derogatory_marks = np.random.poisson(0.7, n_samples)
    
    credit_age = np.random.exponential(15, n_samples)
    credit_age = np.clip(credit_age, 0, 50)
    
    recent_inquiries = np.random.poisson(1.5, n_samples)
    
    employment_options = ['employed', 'self-employed', 'unemployed', 'retired']
    employment_status = np.random.choice(employment_options, n_samples, p=[0.6, 0.2, 0.15, 0.05])
    
    home_options = ['mortgage', 'own', 'rent', 'other']
    home_status = np.random.choice(home_options, n_samples, p=[0.4, 0.3, 0.25, 0.05])
    
    loan_amount = np.random.lognormal(9.5, 0.8, n_samples)
    
    base_prob = (
        0.3 * (income / 100000) + 
        0.2 * (payment_history / 100) - 
        0.15 * (debt_to_income / 100) - 
        0.1 * (credit_utilization / 100) - 
        0.05 * derogatory_marks / 5 +
        0.1 * (credit_age / 30) -
        0.05 * recent_inquiries / 5
    )
    
    emp_status_map = {'employed': 0.1, 'self-employed': 0.05, 'unemployed': -0.2, 'retired': 0.0}
    home_status_map = {'mortgage': 0.05, 'own': 0.1, 'rent': -0.05, 'other': -0.1}
    
    for i in range(n_samples):
        base_prob[i] += emp_status_map[employment_status[i]] + home_status_map[home_status[i]]
    
    base_prob = np.clip(base_prob, 0.05, 0.95)
    creditworthy = np.random.binomial(1, base_prob)
    
    data = pd.DataFrame({
        'age': age,
        'income': income,
        'debt_to_income_ratio': debt_to_income,
        'credit_utilization': credit_utilization,
        'number_of_credit_lines': num_credit_lines,
        'payment_history_score': payment_history,
        'derogatory_marks': derogatory_marks,
        'credit_age_years': credit_age,
        'recent_inquiries': recent_inquiries,
        'employment_status': employment_status,
        'home_ownership': home_status,
        'loan_amount': loan_amount,
        'creditworthy': creditworthy
    })
    
    return data

print("Generating synthetic credit data...")
credit_data = generate_credit_data(10000)
print(f"Dataset shape: {credit_data.shape}")

print("\nClass distribution:")
print(credit_data['creditworthy'].value_counts())
print(f"Percentage of creditworthy applicants: {credit_data['creditworthy'].mean():.2%}")

print("\nPerforming data preprocessing and feature engineering...")

credit_data['income_to_loan_ratio'] = credit_data['income'] / credit_data['loan_amount']
credit_data['credit_lines_per_year'] = credit_data['number_of_credit_lines'] / (credit_data['credit_age_years'] + 1)
credit_data['payment_history_to_credit_age'] = credit_data['payment_history_score'] / (credit_data['credit_age_years'] + 1)

X = credit_data.drop('creditworthy', axis=1)
y = credit_data['creditworthy']

categorical_cols = ['employment_status', 'home_ownership']
numerical_cols = [col for col in X.columns if col not in categorical_cols]

numerical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

categorical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
])

preprocessor = ColumnTransformer(
    transformers=[
        ('num', numerical_transformer, numerical_cols),
        ('cat', categorical_transformer, categorical_cols)
    ])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Training set size: {X_train.shape}")
print(f"Test set size: {X_test.shape}")

print("\nUsing class weights to handle class imbalance...")

models = {
    'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000, class_weight='balanced'),
    'Decision Tree': DecisionTreeClassifier(random_state=42, class_weight='balanced'),
    'Random Forest': RandomForestClassifier(random_state=42, n_estimators=100, class_weight='balanced'),
    'Gradient Boosting': GradientBoostingClassifier(random_state=42)
}

results = {}
for name, model in models.items():
    print(f"\nTraining {name}...")
    
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', model)
    ])
    
    pipeline.fit(X_train, y_train)
    
    y_pred = pipeline.predict(X_test)
    y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
    
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    
    results[name] = {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'roc_auc': roc_auc,
        'model': pipeline
    }
    
    print(f"{name} Results:")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1-Score: {f1:.4f}")
    print(f"ROC-AUC: {roc_auc:.4f}")

print("\n" + "="*50)
print("MODEL PERFORMANCE COMPARISON")
print("="*50)

results_df = pd.DataFrame.from_dict(results, orient='index')
results_df = results_df[['accuracy', 'precision', 'recall', 'f1', 'roc_auc']]
print(results_df.round(4))

best_model_name = results_df['f1'].idxmax()
best_model = results[best_model_name]['model']
print(f"\nBest model: {best_model_name} (F1-Score: {results_df.loc[best_model_name, 'f1']:.4f})")

print(f"\nDetailed evaluation of {best_model_name}:")
y_pred_best = best_model.predict(X_test)
y_pred_proba_best = best_model.predict_proba(X_test)[:, 1]

print("\nClassification Report:")
print(classification_report(y_test, y_pred_best))

print("Confusion Matrix:")
cm = confusion_matrix(y_test, y_pred_best)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
plt.title(f'Confusion Matrix - {best_model_name}')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')
plt.show()

fpr, tpr, _ = roc_curve(y_test, y_pred_proba_best)
roc_auc = auc(fpr, tpr)

plt.figure()
plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title(f'Receiver Operating Characteristic - {best_model_name}')
plt.legend(loc="lower right")
plt.show()

if hasattr(best_model.named_steps['classifier'], 'feature_importances_'):
    print("\nFeature Importance:")
    
    preprocessor = best_model.named_steps['preprocessor']
    feature_names = numerical_cols.copy()
    
    ohe = preprocessor.named_transformers_['cat'].named_steps['onehot']
    cat_features = ohe.get_feature_names_out(categorical_cols)
    feature_names.extend(cat_features)
    
    importances = best_model.named_steps['classifier'].feature_importances_
    
    feature_importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importances
    }).sort_values('importance', ascending=False)
    
    plt.figure(figsize=(10, 8))
    sns.barplot(x='importance', y='feature', data=feature_importance_df.head(15))
    plt.title('Top 15 Feature Importances')
    plt.tight_layout()
    plt.show()
    
    print("Top 10 most important features:")
    print(feature_importance_df.head(10).to_string(index=False))

print(f"\nPerforming cross-validation for {best_model_name}...")
cv_scores = cross_val_score(best_model, X, y, cv=5, scoring='f1')
print(f"Cross-validation F1 scores: {cv_scores}")
print(f"Mean F1 score: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

if best_model_name == 'Random Forest':
    print("\nPerforming hyperparameter tuning for Random Forest...")
    
    param_grid = {
        'classifier__n_estimators': [50, 100, 200],
        'classifier__max_depth': [None, 10, 20],
        'classifier__min_samples_split': [2, 5, 10]
    }
    
    grid_search = GridSearchCV(
        estimator=best_model,
        param_grid=param_grid,
        cv=3,
        scoring='f1',
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X_train, y_train)
    
    print(f"Best parameters: {grid_search.best_params_}")
    print(f"Best cross-validation score: {grid_search.best_score_:.4f}")
    
    best_tuned_model = grid_search.best_estimator_
    y_pred_tuned = best_tuned_model.predict(X_test)
    f1_tuned = f1_score(y_test, y_pred_tuned)
    print(f"Tuned model F1-score on test set: {f1_tuned:.4f}")

print("\nExample prediction on new data:")
new_applicant = pd.DataFrame({
    'age': [35],
    'income': [75000],
    'debt_to_income_ratio': [25.5],
    'credit_utilization': [30.2],
    'number_of_credit_lines': [5],
    'payment_history_score': [85.5],
    'derogatory_marks': [0],
    'credit_age_years': [8],
    'recent_inquiries': [1],
    'employment_status': ['employed'],
    'home_ownership': ['mortgage'],
    'loan_amount': [15000],
    'income_to_loan_ratio': [75000 / 15000],
    'credit_lines_per_year': [5 / 8],
    'payment_history_to_credit_age': [85.5 / 8]
})

prediction = best_model.predict(new_applicant)
prediction_proba = best_model.predict_proba(new_applicant)

credit_status = "Creditworthy" if prediction[0] == 1 else "Not Creditworthy"
confidence = prediction_proba[0][prediction[0]]

print(f"Prediction: {credit_status} (confidence: {confidence:.2%})")

joblib.dump(best_model, 'credit_scoring_model.pkl')
print("\nBest model saved as 'credit_scoring_model.pkl'")