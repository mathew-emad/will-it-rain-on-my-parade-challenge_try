import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score, r2_score, mean_squared_error
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, VotingClassifier, GradientBoostingClassifier
from sklearn.ensemble import RandomForestRegressor

df = pd.read_csv("global_weather_dataset.csv")

df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
df['month'] = df['date'].dt.month

df['temp_lag1'] = df['temperature'].shift(1)
df['hum_lag1'] = df['humidity'].shift(1)
df['wind_lag1'] = df['wind_speed'].shift(1)
df.dropna(inplace=True)

print("||||||||||Training Rain Prediction Model|||||||||")

X_rain = df[[
    'temperature', 'humidity', 'wind_speed', 
    'temp_lag1', 'hum_lag1', 'wind_lag1', 
    'month', 'latitude'
]]
y_rain = (df['precipitation'] > 0.5).astype(int)

X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(
    X_rain, y_rain, test_size=0.2, random_state=42, stratify=y_rain
)

scaler_rain = StandardScaler()
X_train_r_scaled = scaler_rain.fit_transform(X_train_r)
X_test_r_scaled = scaler_rain.transform(X_test_r)
joblib.dump(scaler_rain, "rain_scaler.pkl")

rf_model = RandomForestClassifier(n_estimators=150, class_weight='balanced', max_depth=12, random_state=42)
lr_model = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
gb_model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, random_state=42)

voting_clf = VotingClassifier(
    estimators=[('rf', rf_model), ('lr', lr_model), ('gb', gb_model)],
    voting='soft'
)
voting_clf.fit(X_train_r_scaled, y_train_r)

probabilities = voting_clf.predict_proba(X_test_r_scaled)[:, 1]
best_threshold = 0.5
best_f1 = 0.0

for thresh in np.arange(0.1, 0.95, 0.05):
    temp_preds = (probabilities >= thresh).astype(int)
    temp_f1 = f1_score(y_test_r, temp_preds)
    if temp_f1 > best_f1:
        best_f1 = temp_f1
        best_threshold = thresh

final_rain_preds = (probabilities >= best_threshold).astype(int)
print(f"Optimal Threshold: {best_threshold:.2f}")
print(f"Rain F1-Score: {best_f1:.3f}")
print(f"Rain Accuracy: {accuracy_score(y_test_r, final_rain_preds) * 100:.2f}%\n")

joblib.dump(voting_clf, "best_rain_model.pkl")
with open("best_threshold.txt", "w") as f:
    f.write(str(best_threshold))

print("|||||||||||Training Temperature Prediction Model||||||||||")

X_temp = df[[
    'humidity', 'wind_speed', 'precipitation', 
    'hum_lag1', 'wind_lag1', 'month', 'latitude'
]]
y_temp = df['temperature']

X_train_t, X_test_t, y_train_t, y_test_t = train_test_split(
    X_temp, y_temp, test_size=0.2, random_state=42
)

scaler_temp = StandardScaler()
X_train_t_scaled = scaler_temp.fit_transform(X_train_t)
X_test_t_scaled = scaler_temp.transform(X_test_t)
joblib.dump(scaler_temp, "temp_scaler.pkl")

rf_regressor = RandomForestRegressor(random_state=42)
param_grid = {
    'n_estimators': [100, 200],
    'max_depth': [10, 20, None]
}

grid_search = GridSearchCV(rf_regressor, param_grid, cv=5, scoring='r2', n_jobs=-1)
grid_search.fit(X_train_t_scaled, y_train_t)

best_temp_model = grid_search.best_estimator_
temp_predictions = best_temp_model.predict(X_test_t_scaled)

r2 = r2_score(y_test_t, temp_predictions)
mse = mean_squared_error(y_test_t, temp_predictions)

print(f"Best Temperature Model Params: {grid_search.best_params_}")
print(f"Temperature R2 Score: {r2:.3f}")
print(f"Temperature MSE: {mse:.2f}")

joblib.dump(best_temp_model, "best_temp_model.pkl")
print("\nAll models, scalers, and thresholds successfully saved.")