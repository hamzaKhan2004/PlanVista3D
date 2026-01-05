/* eslint-disable no-unused-vars */
/* eslint-disable react-hooks/rules-of-hooks */
import React, { Suspense, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, useGLTF, Environment, Grid } from "@react-three/drei";

const Model = ({ url }) => {
  const [error, setError] = useState(null);

  try {
    const { scene } = useGLTF(url);
    const modelRef = useRef();

    useFrame((state) => {
      if (modelRef.current) {
        // Optional: Add subtle rotation
        modelRef.current.rotation.y += 0.005;
      }
    });

    return (
      <primitive ref={modelRef} object={scene} scale={1} position={[0, 0, 0]} />
    );
  } catch (err) {
    console.error("Error loading GLB model:", err);
    setError(err.message);
    return null;
  }
};

const LoadingFallback = () => (
  <mesh>
    <boxGeometry args={[1, 1, 1]} />
    <meshStandardMaterial color="gray" />
  </mesh>
);

const Viewer3D = ({ modelUrl }) => {
  return (
    <div style={{ width: "100%", height: "600px" }}>
      <Canvas camera={{ position: [10, 10, 10], fov: 75 }} shadows>
        <Suspense fallback={<LoadingFallback />}>
          {/* Lighting */}
          <ambientLight intensity={0.4} />
          <directionalLight
            position={[10, 10, 5]}
            intensity={1}
            castShadow
            shadow-mapSize-width={2048}
            shadow-mapSize-height={2048}
          />
          <pointLight position={[-10, -10, -10]} intensity={0.5} />

          {/* Environment */}
          <Environment preset="apartment" />

          {/* Grid */}
          <Grid infiniteGrid fadeDistance={50} fadeStrength={5} />

          {/* 3D Model */}
          <Model url={modelUrl} />

          {/* Camera Controls */}
          <OrbitControls
            enablePan={true}
            enableZoom={true}
            enableRotate={true}
            minDistance={3}
            maxDistance={50}
          />
        </Suspense>
      </Canvas>
    </div>
  );
};

export default Viewer3D;
