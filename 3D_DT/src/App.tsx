import { Canvas } from "@react-three/fiber";
import { OrbitControls, Html } from "@react-three/drei";
import { useEffect, useState, Suspense } from "react";
import axios from "axios";
import { create } from "zustand";
import "./App.css";
import { DetailsModal } from "./DetailsModal";
import { WaterMeterModel } from "./WaterMeterModel";

// === Zustand Store for global state ===
interface StoreState {
  selectedMeter: string | null;
  setSelectedMeter: (id: string | null) => void;
}
const useStore = create<StoreState>((set) => ({
  selectedMeter: null,
  setSelectedMeter: (id) => set({ selectedMeter: id }),
}));

// === Main App Component ===
export default function App() {
  const [data, setData] = useState<any[]>([]);
  const { selectedMeter, setSelectedMeter } = useStore();

  useEffect(() => {
    axios
      .get("/combined_water_data.json")
      .then((res) => {
        console.log("✅ JSON loaded", res.data);
        setData(res.data);
      })
      .catch(console.error);
  }, []);

  const uniqueMeters = [...new Set(data.map((d) => d.meter_id))];

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header-bar">
        <h1>🚰 Campus Water Digital Twin</h1>
      </header>

      <div className="main-layout">
        {/* Sidebar */}
        <aside className="sidebar">
          <h2>Water Meters</h2>
          <ul>
            {uniqueMeters.map((id) => (
              <li
                key={id}
                onClick={() => setSelectedMeter(id)}
                className={selectedMeter === id ? "selected" : ""}
              >
                {id}
              </li>
            ))}
          </ul>
        </aside>

        {/* 3D Canvas */}
        <div className="canvas-container">
          <Canvas camera={{ position: [0, 20, 30], fov: 45 }}>
            <ambientLight intensity={0.6} />
            <pointLight position={[10, 10, 10]} />
            <OrbitControls />

            {/* Floor */}
            <mesh position={[0, -0.1, 0]}>
              <boxGeometry args={[100, 0.2, 100]} />
              <meshStandardMaterial color="#ccc" />
            </mesh>

            {/* All Water Meters */}
            {uniqueMeters.map((id, i) => {
              const posX = (i % 10) * 5 - 20;
              const posZ = Math.floor(i / 10) * 5 - 10;

              const readings = data.filter((d) => d.meter_id === id);
              const latest = readings[readings.length - 1];
              const consumption = latest?.consumption_liters || 0;
              const isLeak = latest?.is_leak;
              const color = isLeak ? "red" : "green";

              return (
                <group
                  key={id}
                  position={[posX, 0, posZ]}
                  onClick={() => setSelectedMeter(id)}
                >
                  <Suspense fallback={null}>
                    <WaterMeterModel color={color} />
                  </Suspense>
                  <Html distanceFactor={10}>
                    <div className="label">
                      <strong>{id}</strong><br />
                      {consumption.toFixed(1)} L
                    </div>
                  </Html>
                </group>
              );
            })}
          </Canvas>
        </div>
      </div>

      {/* Modal for Details */}
      {selectedMeter && (
        <DetailsModal
          meterId={selectedMeter}
          close={() => setSelectedMeter(null)}
          data={data}
        />
      )}
    </div>
  );
}
