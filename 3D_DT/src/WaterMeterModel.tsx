import { useGLTF } from "@react-three/drei";

interface WaterMeterProps {
  color?: string;
}

export function WaterMeterModel({ color = "green" }: WaterMeterProps) {
  const { scene } = useGLTF("/assets/models/water_meter.glb");
  return (
    <primitive
      object={scene}
      scale={[1, 1, 1]}
    />
  );
}
