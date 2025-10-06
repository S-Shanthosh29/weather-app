// //import logo from './logo.svg';
// import './App.css';

// import React from "react";

// function App() {
//   return (
//     <div className="App">
//       <h1>Future Weather Forecasts</h1>
//       <p>This is showing up correctly.</p>
//     </div>
//   );
// }

// export default App;

import React, { useState } from "react";

function App() {
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    setResult(null);

    try {
      const res = await fetch("http://localhost:5000/api/weather", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          latitude,
          longitude,
          start_date: startDate + "T00",
          end_date: endDate + "T00",
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Unknown error");
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h1>NASA Weather App 🌦️</h1>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        <input
          type="text"
          placeholder="Latitude (e.g. 38.89)"
          value={latitude}
          onChange={(e) => setLatitude(e.target.value)}
          required
        />
        <input
          type="text"
          placeholder="Longitude (e.g. -88.18)"
          value={longitude}
          onChange={(e) => setLongitude(e.target.value)}
          required
        />
        <label>Start Date (between 2015–2020)</label>
        <input
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          required
        />
        <label>End Date (between 2015–2020)</label>
        <input
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? "Loading..." : "Get Weather Data"}
        </button>
      </form>

      {error && <p style={{ color: "red" }}>⚠️ {error}</p>}

      {result && (
        <div style={{ marginTop: 20 }}>
          <h2>Results</h2>
          <p>
            <strong>Average Daily Precipitation:</strong> {result.metadata.average_daily_precip_mm} mm
          </p>

          <h3>📅 Monthly Averages</h3>
          <ul>
            {result.monthly_averages.map((m) => (
              <li key={m.month}>
                Month {m.month}: {m.data.toFixed(2)} mm
              </li>
            ))}
          </ul>

          <h3>🔮 6-Month Predictions</h3>
          <ul>
            {result.six_month_predictions.map((p, index) => (
              <li key={index}>
                Month {p.month}: {p.predicted_avg_precip_mm} mm
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;
