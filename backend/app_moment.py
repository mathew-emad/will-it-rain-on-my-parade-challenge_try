from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import numpy as np
import os

app = FastAPI(title="NASA Weather Prediction API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
print("Loading models and scalers...")
rain_model = joblib.load("best_rain_model.pkl")
rain_scaler = joblib.load("rain_scaler.pkl")
temp_model = joblib.load("best_temp_model.pkl")
temp_scaler = joblib.load("temp_scaler.pkl")

with open("best_threshold.txt", "r") as f:
    BEST_THRESHOLD = float(f.read().strip())

class WeatherInput(BaseModel):
    temperature: float
    humidity: float
    wind_speed: float
    temp_lag1: float
    hum_lag1: float
    wind_lag1: float
    month: int
    latitude: float
    precipitation: float

@app.get("/")
def home():
    return {"message": "NASA Weather API is running successfully!"}

@app.post("/predict")
def predict_weather(data: WeatherInput):
    rain_features = np.array([[
        data.temperature, data.humidity, data.wind_speed,
        data.temp_lag1, data.hum_lag1, data.wind_lag1,
        data.month, data.latitude
    ]])
    rain_scaled = rain_scaler.transform(rain_features)
    rain_prob = rain_model.predict_proba(rain_scaled)[:, 1][0]
    is_raining = int(rain_prob >= BEST_THRESHOLD)
    temp_features = np.array([[
        data.humidity, data.wind_speed, data.precipitation,
        data.hum_lag1, data.wind_lag1,
        data.month, data.latitude
    ]])
    temp_scaled = temp_scaler.transform(temp_features)
    predicted_temp = temp_model.predict(temp_scaled)[0]

    return {
        "predicted_temperature": round(float(predicted_temp), 2),
        "rain_probability": round(float(rain_prob), 2),
        "will_it_rain": bool(is_raining),
        "threshold_used": BEST_THRESHOLD    
    }
# py -m uvicorn app_moment:app --reload