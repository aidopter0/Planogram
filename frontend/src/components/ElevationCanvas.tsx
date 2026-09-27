import { Canvas } from "@react-three/fiber";
import { OrthographicCamera } from "@react-three/drei";
import { useMemo } from "react";
import type { Placement, Product } from "../api";

type Props = {
  carrierWidthMm: number;
  availableWidthMm: number;
  placements: Placement[];
  productsById: Record<number, Product>;
};

function FacingStrip({
  placements,
  productsById,
  availableWidthMm,
}: {
  placements: Placement[];
  productsById: Record<number, Product>;
  availableWidthMm: number;
}) {
  const items = useMemo(() => {
    let x = 0;
    const scale = 0.01; // mm → scene units
    return [...placements]
      .sort((a, b) => a.sequence - b.sequence)
      .flatMap((p) => {
        const prod = productsById[p.product_id];
        const w = p.effective_width_mm * scale;
        const h = ((prod?.height_mm || 200) * scale) * (p.orientation === "rotated_90" ? 0.7 : 1);
        const faces = [];
        for (let i = 0; i < p.facings; i++) {
          faces.push({
            key: `${p.id}-${i}`,
            x: x + w / 2,
            w,
            h,
            color: prod?.front_image_url ? "#10b981" : "#94a3b8",
            label: prod?.sku || String(p.product_id),
            image: prod?.front_image_url || null,
          });
          x += w;
        }
        return faces;
      });
  }, [placements, productsById]);

  const shelfW = availableWidthMm * 0.01;
  const overflow = items.reduce((s, i) => s + i.w, 0) > shelfW + 0.001;

  return (
    <group position={[-shelfW / 2, 0, 0]}>
      {/* shelf plank */}
      <mesh position={[shelfW / 2, -0.15, 0]}>
        <boxGeometry args={[shelfW, 0.08, 0.4]} />
        <meshStandardMaterial color="#475569" />
      </mesh>
      {/* available width guide */}
      <mesh position={[shelfW / 2, -0.05, 0.21]}>
        <boxGeometry args={[shelfW, 0.02, 0.02]} />
        <meshStandardMaterial color={overflow ? "#f43f5e" : "#10b981"} />
      </mesh>
      {items.map((f) => (
        <group key={f.key} position={[f.x, f.h / 2, 0.05]}>
          <mesh>
            <boxGeometry args={[f.w * 0.92, f.h, 0.06]} />
            <meshStandardMaterial color={f.color} />
          </mesh>
          {/* pack-front plane */}
          <mesh position={[0, 0, 0.04]}>
            <planeGeometry args={[f.w * 0.88, f.h * 0.92]} />
            <meshStandardMaterial color="#ecfdf5" />
          </mesh>
        </group>
      ))}
      {/* Width label is shown in the HTML width meter — keep canvas geometry-only. */}
    </group>
  );
}

export default function ElevationCanvas(props: Props) {
  return (
    <Canvas shadows style={{ width: "100%", height: "100%" }}>
      <color attach="background" args={["#e2e8f0"]} />
      <ambientLight intensity={0.85} />
      <directionalLight position={[4, 6, 4]} intensity={0.7} />
      <OrthographicCamera makeDefault position={[0, 0.8, 6]} zoom={55} />
      <FacingStrip
        placements={props.placements}
        productsById={props.productsById}
        availableWidthMm={props.availableWidthMm}
      />
    </Canvas>
  );
}
