/* eslint-disable no-unused-vars */
/* eslint-disable react-hooks/rules-of-hooks */
import React, {
  Suspense,
  useRef,
  useState,
  useEffect,
  forwardRef,
  useImperativeHandle,
} from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import {
  OrbitControls,
  useGLTF,
  Environment,
  Grid,
  Html,
} from "@react-three/drei";
import { Color, BoxGeometry, MeshStandardMaterial, Mesh } from "three";

const EditableModel = ({
  url,
  editingMode,
  editorState,
  dynamicObjects,
  onObjectSelect,
  selectedObject,
}) => {
  const { scene } = useGLTF(url);
  const modelRef = useRef();
  const [hoveredObject, setHoveredObject] = useState(null);
  const [dynamicMeshes, setDynamicMeshes] = useState(new Map());

  // Handle adding new objects to the scene
  useEffect(() => {
    if (scene) {
      // Add new walls to scene
      dynamicObjects.walls.forEach((wall) => {
        if (wall.isNew && !dynamicMeshes.has(wall.id)) {
          console.log("🧱 Adding new wall to 3D scene:", wall);

          // Create new wall geometry
          const geometry = new BoxGeometry(
            wall.scale[0],
            wall.scale[1],
            wall.scale[2]
          );
          const material = new MeshStandardMaterial({
            color: new Color(wall.color),
          });
          const mesh = new Mesh(geometry, material);

          // Set position and properties
          mesh.position.set(
            wall.position[0],
            wall.position[1],
            wall.position[2]
          );
          mesh.name = wall.id;
          mesh.castShadow = true;
          mesh.receiveShadow = true;

          // Add to scene
          scene.add(mesh);

          // Track the mesh
          setDynamicMeshes((prev) => new Map(prev.set(wall.id, mesh)));
        }
      });

      // Remove deleted objects from scene
      dynamicMeshes.forEach((mesh, id) => {
        const stillExists = [
          ...dynamicObjects.walls,
          ...dynamicObjects.doors,
          ...dynamicObjects.windows,
          ...dynamicObjects.rooms,
        ].some((obj) => obj.id === id);

        if (!stillExists) {
          console.log("🗑️ Removing object from 3D scene:", id);
          scene.remove(mesh);
          mesh.geometry?.dispose();
          mesh.material?.dispose();
          setDynamicMeshes((prev) => {
            const newMap = new Map(prev);
            newMap.delete(id);
            return newMap;
          });
        }
      });
    }
  }, [scene, dynamicObjects, dynamicMeshes]);

  // Handle material and visibility updates
  useEffect(() => {
    if (scene && editingMode) {
      scene.traverse((child) => {
        if (child.isMesh) {
          const objectId = child.name;

          // Find object in dynamic objects
          let objectData = null;
          let objectType = "";

          if (objectId.includes("wall")) {
            objectData = dynamicObjects.walls.find((w) => w.id === objectId);
            objectType = "wall";
          } else if (objectId.includes("door")) {
            objectData = dynamicObjects.doors.find((d) => d.id === objectId);
            objectType = "door";
          } else if (objectId.includes("window")) {
            objectData = dynamicObjects.windows.find((w) => w.id === objectId);
            objectType = "window";
          } else if (objectId.includes("room")) {
            objectData = dynamicObjects.rooms.find((r) => r.id === objectId);
            objectType = "room";
          }

          // Apply visibility
          if (objectData) {
            child.visible = objectData.visible;

            // Apply color
            if (child.material) {
              child.material.color = new Color(objectData.color);
            }
          }

          // Apply global category visibility
          if (objectType === "wall" && !editorState.wallsVisible)
            child.visible = false;
          if (objectType === "door" && !editorState.doorsVisible)
            child.visible = false;
          if (objectType === "window" && !editorState.windowsVisible)
            child.visible = false;
          if (objectType === "room" && !editorState.roomsVisible)
            child.visible = false;

          // Wireframe mode
          if (child.material) {
            child.material.wireframe = editorState.showWireframe;
          }

          // Blue highlight for selected object
          if (selectedObject && child.name === selectedObject.id) {
            if (child.material) {
              child.material.emissive = new Color(0x0066ff);
              child.material.emissiveIntensity = 0.3;
            }
          } else if (hoveredObject === child.name) {
            if (child.material) {
              child.material.emissive = new Color(0x333333);
              child.material.emissiveIntensity = 0.1;
            }
          } else {
            if (child.material) {
              child.material.emissive = new Color(0x000000);
              child.material.emissiveIntensity = 0;
            }
          }
        }
      });
    }
  }, [
    scene,
    editingMode,
    editorState,
    selectedObject,
    hoveredObject,
    dynamicObjects,
  ]);

  const handleClick = (event) => {
    if (editingMode && event.object) {
      event.stopPropagation();
      const objectName = event.object.name;

      let objectType = "unknown";
      let displayName = objectName;

      if (objectName.includes("wall")) {
        objectType = "wall";
        displayName = objectName.replace("wall_", "Wall ");
      } else if (objectName.includes("door")) {
        objectType = "door";
        displayName = objectName.replace("door_", "Door ");
      } else if (objectName.includes("window")) {
        objectType = "window";
        displayName = objectName.replace("window_", "Window ");
      } else if (objectName.includes("room")) {
        objectType = "room";
        displayName = objectName.replace("room_", "Room ");
      }

      onObjectSelect({
        id: objectName,
        name: displayName,
        type: objectType,
        mesh: event.object,
      });
    }
  };

  const handlePointerOver = (event) => {
    if (editingMode && event.object) {
      setHoveredObject(event.object.name);
      document.body.style.cursor = "pointer";
    }
  };

  const handlePointerOut = () => {
    if (editingMode) {
      setHoveredObject(null);
      document.body.style.cursor = "default";
    }
  };

  return (
    <primitive
      ref={modelRef}
      object={scene}
      scale={1}
      position={[0, 0, 0]}
      onClick={handleClick}
      onPointerOver={handlePointerOver}
      onPointerOut={handlePointerOut}
    />
  );
};

const CameraController = forwardRef((props, ref) => {
  const { camera, gl, scene } = useThree();
  const controlsRef = useRef();

  useImperativeHandle(ref, () => ({
    resetCamera: () => {
      camera.position.set(15, 15, 15);
      camera.lookAt(0, 0, 0);
      if (controlsRef.current) {
        controlsRef.current.reset();
      }
    },
    setTopView: () => {
      camera.position.set(0, 25, 0);
      camera.lookAt(0, 0, 0);
      if (controlsRef.current) {
        controlsRef.current.update();
      }
    },
    setFrontView: () => {
      camera.position.set(0, 5, 25);
      camera.lookAt(0, 0, 0);
      if (controlsRef.current) {
        controlsRef.current.update();
      }
    },
    setSideView: () => {
      camera.position.set(25, 5, 0);
      camera.lookAt(0, 0, 0);
      if (controlsRef.current) {
        controlsRef.current.update();
      }
    },
    takeScreenshot: () => {
      const link = document.createElement("a");
      link.setAttribute("download", `blueprint-3d-${Date.now()}.png`);
      link.setAttribute(
        "href",
        gl.domElement
          .toDataURL("image/png")
          .replace("image/png", "image/octet-stream")
      );
      link.click();
    },
  }));

  return (
    <OrbitControls
      ref={controlsRef}
      camera={camera}
      domElement={gl.domElement}
      enablePan={true}
      enableZoom={true}
      enableRotate={true}
      minDistance={5}
      maxDistance={100}
      enableDamping={true}
      dampingFactor={0.05}
      maxPolarAngle={Math.PI / 2}
    />
  );
});

const LoadingFallback = () => (
  <mesh>
    <boxGeometry args={[2, 2, 2]} />
    <meshStandardMaterial color="#666666" />
    <Html center>
      <div className="text-white text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
        <div>Loading 3D Model...</div>
      </div>
    </Html>
  </mesh>
);

const Advanced3DEditor = forwardRef(
  (
    {
      modelUrl,
      editingMode,
      editorState,
      dynamicObjects,
      onObjectSelect,
      selectedObject,
    },
    ref
  ) => {
    const cameraControlsRef = useRef();
    const sceneRef = useRef();

    useImperativeHandle(ref, () => ({
      resetCamera: () => cameraControlsRef.current?.resetCamera(),
      setTopView: () => cameraControlsRef.current?.setTopView(),
      setFrontView: () => cameraControlsRef.current?.setFrontView(),
      setSideView: () => cameraControlsRef.current?.setSideView(),
      takeScreenshot: () => cameraControlsRef.current?.takeScreenshot(),

      // These functions are now handled automatically by the EditableModel component
      addWallToScene: (wallData) => {
        console.log("✅ Wall will be added by EditableModel effect:", wallData);
      },

      removeObjectFromScene: (objectId) => {
        console.log(
          "✅ Object will be removed by EditableModel effect:",
          objectId
        );
      },

      updateObjectColorInScene: (objectId, color) => {
        console.log(
          "✅ Color will be updated by EditableModel effect:",
          objectId,
          color
        );
      },
    }));

    const getLightingIntensity = () => {
      switch (editorState.lighting) {
        case "bright":
          return { ambient: 0.8, directional: 2 };
        case "soft":
          return { ambient: 0.6, directional: 1 };
        case "dramatic":
          return { ambient: 0.2, directional: 3 };
        default:
          return { ambient: 0.4, directional: 1.5 };
      }
    };

    const lightIntensity = getLightingIntensity();

    return (
      <div style={{ width: "100%", height: "100%" }}>
        <Canvas
          camera={{ position: [15, 15, 15], fov: 60 }}
          shadows
          gl={{ preserveDrawingBuffer: true, antialias: true }}
        >
          <Suspense fallback={<LoadingFallback />}>
            {/* Enhanced Dynamic Lighting */}
            <ambientLight intensity={lightIntensity.ambient} />
            <directionalLight
              position={[10, 20, 10]}
              intensity={lightIntensity.directional}
              castShadow
              shadow-mapSize-width={2048}
              shadow-mapSize-height={2048}
            />
            <pointLight position={[0, 0, 10]} intensity={0.3} />
            <pointLight
              position={[-10, -10, 5]}
              intensity={0.2}
              color="#4444ff"
            />

            {/* Environment */}
            <Environment preset="city" />

            {/* Enhanced Grid */}
            {editorState.showGrid && (
              <Grid
                infiniteGrid
                fadeDistance={50}
                fadeStrength={5}
                cellColor="#444444"
                sectionColor="#666666"
                cellThickness={0.6}
                sectionThickness={1.5}
              />
            )}

            {/* 3D Model with Dynamic Objects */}
            <EditableModel
              url={modelUrl}
              editingMode={editingMode}
              editorState={editorState}
              dynamicObjects={dynamicObjects}
              onObjectSelect={onObjectSelect}
              selectedObject={selectedObject}
            />

            {/* Camera Controls */}
            <CameraController ref={cameraControlsRef} />
          </Suspense>
        </Canvas>
      </div>
    );
  }
);

export default Advanced3DEditor;
