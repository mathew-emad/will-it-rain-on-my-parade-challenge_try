import requests
import pandas as pd
import time

locations = [
    {"name": "Cairo", "lat": 30.0444, "lng": 31.2357},
    {"name": "Alexandria", "lat": 31.2001, "lng": 29.9187},
    {"name": "London", "lat": 51.5074, "lng": -0.1278},
    {"name": "California", "lat": 36.7783, "lng": -119.4179},
    {"name": "Tokyo", "lat": 35.6762, "lng": 139.6503},
    {"name": "Singapore", "lat": 1.3521, "lng": 103.8198}
]
START_DATE = "20210101"
END_DATE = "20251231"
all_datasets = []

print("||||||collecting data||||||")

for loc in locations:
    print(f"collecting data on: {loc['name']}...")
    
    url = (
        f"https://power.larc.nasa.gov/api/temporal/daily/point?"
        f"parameters=PRECTOTCORR,T2M,RH2M,WS10M&community=RE"
        f"&longitude={loc['lng']}&latitude={loc['lat']}"
        f"&start={START_DATE}&end={END_DATE}&format=JSON"
    )
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:

            params = response.json()['properties']['parameter']

            dates = list(params['T2M'].keys())
            temperatures = list(params['T2M'].values())
            humidities = list(params['RH2M'].values())
            wind_speeds = list(params['WS10M'].values())
            precipitations = list(params['PRECTOTCORR'].values())

            df_temp = pd.DataFrame({
                'date': dates,
                'latitude': loc['lat'],
                'temperature': temperatures,
                'humidity': humidities,
                'wind_speed': wind_speeds,
                'precipitation': precipitations
            })
            all_datasets.append(df_temp)
        else:
            print(f"error in collecting {loc['name']}'s data : {response.status_code}")
            
    except Exception as e:
        print(f"connection error during collecting{loc['name']}'s data: {e}")
        
    time.sleep(1) 
    
if all_datasets:
    final_df = pd.concat(all_datasets, ignore_index=True)
    final_df = final_df[
        (final_df['temperature'] != -999) & 
        (final_df['humidity'] != -999) & 
        (final_df['precipitation'] != -999)
    ]
    final_df.to_csv("global_weather_dataset.csv", index=False)
    print(f"\n successfully collected: {len(final_df)} days")