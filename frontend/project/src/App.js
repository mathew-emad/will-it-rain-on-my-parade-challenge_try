import { useState } from "react";
import "./App.css";
import "leaflet/dist/leaflet.css";
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from "react-leaflet";
import { Icon } from "leaflet";
import da_icon from "./image/location.png";
import DatePicker from "react-datepicker";
import MeWhenDate from "./date_picker";

function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng);
    },
  });
  return null;
}

export default function App() {
  const [selectedPosition, setSelectedPosition] = useState(null);
  const [selectedDate, setSelectedDate] = useState(null);
  const [predictionResult, setPredictionResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const customicon = new Icon({
    iconUrl: da_icon,
    iconSize: [25, 25],
    iconAnchor: [15, 30],
  });

  const handleSubmit = async () => {
    if (!selectedDate || !selectedPosition) {
      alert("Please select both date and position first!");
      return;
    }

    setLoading(true);
    setPredictionResult(null);

    const lat = selectedPosition.lat;
    const lng = selectedPosition.lng;

    const today = new Date();
    const targetDate = new Date(selectedDate);
    const diffTime = targetDate - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    let startDateStr, endDateStr;

    if (diffDays > 30) {
      const pastYear = targetDate.getFullYear() - 1;
      const monthStr = String(targetDate.getMonth() + 1).padStart(2, '0');
      
      startDateStr = `${pastYear}${monthStr}01`;
      endDateStr = `${pastYear}${monthStr}02`;
    } else {
      const baseDate = new Date();
      baseDate.setDate(baseDate.getDate() - 7);
      
      const prevBaseDate = new Date(baseDate);
      prevBaseDate.setDate(baseDate.getDate() - 1);

      startDateStr = prevBaseDate.toISOString().split("T")[0].replaceAll("-", "");
      endDateStr = baseDate.toISOString().split("T")[0].replaceAll("-", "");
    }

    const nasaUrl = `https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR,T2M,RH2M,WS10M&community=RE&longitude=${lng}&latitude=${lat}&start=${startDateStr}&end=${endDateStr}&format=JSON`;

    try {
      const response = await fetch(nasaUrl);
      if (!response.ok) throw new Error("Failed to fetch data from NASA API");

      const data = await response.json();
      const params = data.properties.parameter;

      const dates = Object.keys(params.T2M);
      const mainDateKey = dates[dates.length - 1];
      const prevDateKey = dates[0];

      const temp = params.T2M[mainDateKey];
      const humidity = params.RH2M[mainDateKey];
      const rain = params.PRECTOTCORR[mainDateKey];
      const wind = params.WS10M[mainDateKey];

      const temp_lag1 = params.T2M[prevDateKey];
      const hum_lag1 = params.RH2M[prevDateKey];
      const wind_lag1 = params.WS10M[prevDateKey];

      const validTemp = (temp && temp !== -999) ? temp : 25.0;
      const validHumidity = (humidity && humidity !== -999) ? humidity : 50.0;
      const validRain = (rain && rain !== -999) ? rain : 0.0;
      const validWind = (wind && wind !== -999) ? wind : 10.0;

      const validTempLag = (temp_lag1 && temp_lag1 !== -999) ? temp_lag1 : validTemp;
      const validHumLag = (hum_lag1 && hum_lag1 !== -999) ? hum_lag1 : validHumidity;
      const validWindLag = (wind_lag1 && wind_lag1 !== -999) ? wind_lag1 : validWind;

      const requestData = {
        temperature: validTemp,
        humidity: validHumidity,
        wind_speed: validWind,
        temp_lag1: validTempLag,
        hum_lag1: validHumLag,
        wind_lag1: validWindLag,
        month: targetDate.getMonth() + 1,
        latitude: lat,
        precipitation: validRain
      };

      const backendResponse = await fetch("http://127.0.0.1:8000/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
      });

      if (!backendResponse.ok) throw new Error("Failed to get prediction from backend");
      
      const backendResult = await backendResponse.json();

      let tempStatus = "Normal";
      if (backendResult.predicted_temperature >= 40) tempStatus = "Very Hot";
      else if (backendResult.predicted_temperature >= 33) tempStatus = "Hot";
      else if (backendResult.predicted_temperature <= 12) tempStatus = "Cold";
      else if (backendResult.predicted_temperature <= 5) tempStatus = "Very cold";

      const humidityStatus = validHumidity > 65 ? "Humid" : "Dry";

      setPredictionResult({
        temp: backendResult.predicted_temperature,
        tempStatus,
        humidity: validHumidity,
        humidityStatus,
        rain: validRain,
        willItRain: backendResult.will_it_rain,
        rainProbability: backendResult.rain_probability,
        wind: validWind,
      });

    } catch (error) {
      console.error("Fetch Error:", error);
      alert("An error occurred while connecting to the backend or NASA API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", width: "100vw", backgroundColor: "#f29d5b", padding: "20px", boxSizing: "border-box" }}>
      <h1 style={{ color: "#black", textAlign: "center", margin: "0 0 20px 0"  }}>
        Will It Rain On My Parade
      </h1>
      <div style={{ display: "flex", gap: "20px", width: "100%", justifyContent: "center", alignItems: "flex-start" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "20px", width: "35%" }}>
          <div style={{
            zIndex: 1000, 
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "15px",
            borderRadius: "10px",
            backgroundColor: "#f58a07",
            borderColor:"black",
            border:"1px solid black"
          }}>
            <MeWhenDate selectedDate={selectedDate} setSelectedDate={setSelectedDate} /> 
            <button 
              onClick={handleSubmit} 
              disabled={loading}
              style={{
                padding: "8px 16px",
                backgroundColor: loading ? "#909cc2" : "#084887",
                color: "white",
                border: "none",
                borderRadius: "4px",
                cursor: loading ? "not-allowed" : "pointer",
                fontWeight: "bold",
              }}
            >
              {loading ? "Loading" : "Check Weather"}
            </button>
          </div>

          {predictionResult && (
            <div style={{
              padding: "20px",
              border: "1px solid #030303",
              borderRadius: "8px",
              backgroundColor: "#4f2a20",
              textAlign: "center"
            }}>
              <h3 style={{ margin: "0 0 15px 0", color: "#909CC2" }}>Predicted Weather Conditions</h3>
              <p style={{ margin: "5px 0" ,color:"white" }}>Temperature: <b>{predictionResult.temp} °C</b> ({predictionResult.tempStatus})</p>
              <p style={{ margin: "5px 0",color:"white" }}>Humidity: <b>{predictionResult.humidity} %</b> ({predictionResult.humidityStatus})</p>
              <p style={{ margin: "5px 0" ,color:"white"}}>Rainfall: <b>{predictionResult.rain} mm</b> ({predictionResult.willItRain ? "Rainy" : "Clear / No Rain"})</p>
              <p style={{ margin: "5px 0" ,color:"white"}}>Rain Probability: <b>{(predictionResult.rainProbability * 100).toFixed(1)}%</b></p>
              <p style={{ margin: "5px 0" ,color:"white"}}>Wind Speed: <b>{predictionResult.wind} m/s</b></p>
            </div>
          )}

        </div>
        <div style={{ width: "60%" }}>
          <MapContainer 
            center={[30.0333, 31.2333]} 
            zoom={6}
            style={{ height: "65vh", width: "100%", borderRadius: "8px"}}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <MapClickHandler onMapClick={setSelectedPosition} />
            {selectedPosition && (
              <Marker position={selectedPosition} icon={customicon}>
                <Popup>
                  <strong>Coordinates:</strong><br />
                  Latitude: {selectedPosition.lat.toFixed(4)}<br />
                  Longitude: {selectedPosition.lng.toFixed(4)}
                </Popup>
              </Marker>
            )}
          </MapContainer>
        </div>

      </div>
    </div>
  );
}