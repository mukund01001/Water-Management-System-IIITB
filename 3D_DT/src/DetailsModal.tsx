import { useState } from "react";
import Plot from "react-plotly.js";

interface Props {
  meterId: string;
  close: () => void;
  data: any[];
}

export function DetailsModal({ meterId, close, data }: Props) {
  const readings = data.filter((r) => r.meter_id === meterId);

  // Prepare plot data
  const x = readings.map((r) => r.timestamp);
  const y = readings.map((r) => r.consumption_liters);

  const [valve, setValve] = useState("Open");

  const isLeak = readings.some((r) => r.is_leak);

  return (
    <div style={{
      position: "fixed",
      top: 50,
      left: 50,
      background: "#333",
      color: "#fff",
      padding: 20,
      borderRadius: 8,
      zIndex: 999,
      maxHeight: "90vh",
      overflowY: "auto"
    }}>
      <h3>{meterId}</h3>

      <p>Leak detected? <strong style={{ color: isLeak ? "red" : "lime" }}>
        {isLeak ? "YES" : "No"}
      </strong></p>

      <Plot
        data={[{
          x,
          y,
          type: "scatter",
          mode: "lines+markers",
          marker: { color: isLeak ? "red" : "blue" }
        }]}
        layout={{
          title: "Consumption History",
          paper_bgcolor: "#333",
          plot_bgcolor: "#333",
          font: { color: "#fff" }
        }}
      />

      <button
        onClick={() => setValve(valve === "Open" ? "Closed" : "Open")}
        style={{
          marginTop: 10,
          background: isLeak ? "red" : "green",
          color: "#fff",
          border: "none",
          padding: "8px 16px",
          cursor: "pointer"
        }}
      >
        Toggle Valve (Currently {valve})
      </button>

      <br /><br />
      <button onClick={close} style={{
        background: "#555",
        color: "#fff",
        border: "none",
        padding: "8px 16px",
        cursor: "pointer"
      }}>
        Close
      </button>
    </div>
  );
}
