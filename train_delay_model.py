import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

print("🤖 Generating synthetic training dataset for logistics delays...")

# Seed for reproducibility
np.random.seed(42)
n_samples = 5000

# Features:
# 1. distance_km (50 to 1200 km)
distance = np.random.uniform(50, 1200, n_samples)
# 2. payload_weight_kg (500 to 25000 kg)
payload = np.random.uniform(500, 25000, n_samples)
# 3. weather_severity (0: Clear, 1: Fog, 2: Rain, 3: Storm)
weather = np.random.choice([0, 1, 2, 3], size=n_samples, p=[0.60, 0.20, 0.15, 0.05])
# 4. departure_hour (0 to 23)
hour = np.random.randint(0, 24, n_samples)
# 5. is_weekend (0 or 1)
is_weekend = np.random.choice([0, 1], size=n_samples, p=[0.71, 0.29])

# Realistic delay logic probability function
delay_prob = (
    (distance / 1200) * 0.35 +
    (payload / 25000) * 0.15 +
    (weather / 3) * 0.30 +
    ((hour >= 8) & (hour <= 11) | (hour >= 17) & (hour <= 20)) * 0.15 +
    (is_weekend) * 0.05
)

# Target: 1 = Delayed, 0 = On Time
labels = (delay_prob + np.random.normal(0, 0.08, n_samples) > 0.45).astype(int)

X = np.column_stack([distance, payload, weather, hour, is_weekend])
y = labels

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(f"Dataset ready with {n_samples} trips. Training Random Forest model...")
clf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"✅ Model trained successfully! Test Accuracy: {acc * 100:.2f}%")

# Create output folder and save model artifact
os.makedirs("shipments/ml", exist_ok=True)
model_path = "shipments/ml/delay_model.joblib"
joblib.dump(clf, model_path)
print(f"💾 Model saved to: {model_path}")