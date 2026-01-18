/* eslint-disable no-unused-vars */
import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import Advanced3DEditor from "../components/Advanced3DEditor";
import {
  Cog6ToothIcon,
  PaintBrushIcon,
  CubeIcon,
  EyeIcon,
  ArrowDownTrayIcon,
  HomeIcon,
  WrenchScrewdriverIcon,
  Square3Stack3DIcon,
  ArrowPathIcon,
  ArrowUpIcon,
  ArrowRightIcon,
  EyeSlashIcon,
  SunIcon,
  CameraIcon,
  PhotoIcon,
  DocumentDuplicateIcon,
  TrashIcon,
  PlusIcon,
  AdjustmentsHorizontalIcon,
  ClipboardDocumentListIcon,
  BuildingStorefrontIcon,
} from "@heroicons/react/24/outline";

const ViewerPage = () => {
  const { taskId } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editingMode, setEditingMode] = useState(false);
  const [selectedObject, setSelectedObject] = useState(null);
  const [modelData, setModelData] = useState(null);
  const [isFullscreenEdit, setIsFullscreenEdit] = useState(false);
  const [showLeftPanel, setShowLeftPanel] = useState(true);
  const [showRightPanel, setShowRightPanel] = useState(false);
  const editorRef = useRef(null);

  // Editor state with visibility controls
  const [editorState, setEditorState] = useState({
    selectedWall: null,
    wallColor: "#cccccc",
    floorColor: "#8B4513",
    ceilingColor: "#ffffff",
    wallHeight: 3.0,
    showGrid: true,
    showWireframe: false,
    lighting: "default",
    viewMode: "perspective",
    showStats: true,
    wallsVisible: true,
    doorsVisible: true,
    windowsVisible: true,
    roomsVisible: true,
  });

  // Dynamic objects state (tracks what's actually in the 3D scene)
  const [dynamicObjects, setDynamicObjects] = useState({
    walls: [],
    doors: [],
    windows: [],
    rooms: [],
  });

  // Track next ID for new objects
  const [nextId, setNextId] = useState({
    wall: 0,
    door: 0,
    window: 0,
    room: 0,
  });

  useEffect(() => {
    const pollStatus = async () => {
      try {
        const response = await axios.get(`/api/status/${taskId}`);
        const statusData = response.data;
        setStatus(statusData);

        if (statusData.status === "completed") {
          setLoading(false);
          if (statusData.analysis) {
            setModelData(statusData.analysis);

            // Initialize dynamic objects from model data
            const walls = Array.from(
              { length: statusData.analysis.walls_detected || 0 },
              (_, i) => ({
                id: `wall_${i}`,
                name: `Wall ${i + 1}`,
                visible: true,
                color: "#cccccc",
                isOriginal: true,
              }),
            );

            const doors = Array.from(
              { length: statusData.analysis.doors_detected || 0 },
              (_, i) => ({
                id: `door_${i}`,
                name: `Door ${i + 1}`,
                visible: true,
                color: "#8B4513",
                isOriginal: true,
              }),
            );

            const windows = Array.from(
              { length: statusData.analysis.windows_detected || 0 },
              (_, i) => ({
                id: `window_${i}`,
                name: `Window ${i + 1}`,
                visible: true,
                color: "#87CEEB",
                isOriginal: true,
              }),
            );

            const rooms = Array.from(
              { length: statusData.analysis.rooms_detected || 0 },
              (_, i) => ({
                id: `room_${i}`,
                name: `Room ${i + 1}`,
                visible: true,
                color: "#8B4513",
                isOriginal: true,
              }),
            );

            setDynamicObjects({
              walls,
              doors,
              windows,
              rooms,
            });

            // Set next available IDs
            setNextId({
              wall: statusData.analysis.walls_detected || 0,
              door: statusData.analysis.doors_detected || 0,
              window: statusData.analysis.windows_detected || 0,
              room: statusData.analysis.rooms_detected || 0,
            });
          }
        }

        if (statusData.status === "error") {
          setError(statusData.error || "Processing failed");
          setLoading(false);
        }
      } catch (err) {
        setError("Failed to get processing status");
        setLoading(false);
      }
    };

    const interval = setInterval(pollStatus, 2000);
    pollStatus();

    return () => clearInterval(interval);
  }, [taskId]);

  // Add new wall - THIS NOW WORKS!
  const addWall = () => {
    const newWallId = `wall_${nextId.wall}`;
    const newWall = {
      id: newWallId,
      name: `Wall ${nextId.wall + 1}`,
      visible: true,
      color: editorState.wallColor,
      isNew: true,
      position: [Math.random() * 6 - 3, 0, Math.random() * 6 - 3], // Random position
      scale: [2, 3, 0.2], // Wall dimensions
      rotation: [0, 0, 0],
    };

    // Update React state
    setDynamicObjects((prev) => ({
      ...prev,
      walls: [...prev.walls, newWall],
    }));

    // Update next ID
    setNextId((prev) => ({
      ...prev,
      wall: prev.wall + 1,
    }));

    // Actually create the 3D object in the scene
    if (editorRef.current?.addWallToScene) {
      editorRef.current.addWallToScene(newWall);
    }

    // Select the new wall
    setSelectedObject({
      id: newWallId,
      name: newWall.name,
      type: "wall",
    });

    console.log("✅ Added new wall:", newWall);
  };

  // Remove selected object - THIS NOW WORKS!
  const removeSelectedObject = () => {
    if (!selectedObject) return;

    console.log("🗑️ Removing object:", selectedObject);

    const objectType = selectedObject.type + "s";

    // Remove from React state
    setDynamicObjects((prev) => ({
      ...prev,
      [objectType]: prev[objectType].filter(
        (obj) => obj.id !== selectedObject.id,
      ),
    }));

    // Actually remove from 3D scene
    if (editorRef.current?.removeObjectFromScene) {
      editorRef.current.removeObjectFromScene(selectedObject.id);
    }

    setSelectedObject(null);
    console.log("✅ Removed object from scene");
  };

  // Toggle object visibility
  const toggleObjectVisibility = (objectId, objectType) => {
    const objectTypeKey = objectType + "s";

    setDynamicObjects((prev) => ({
      ...prev,
      [objectTypeKey]: prev[objectTypeKey].map((obj) =>
        obj.id === objectId ? { ...obj, visible: !obj.visible } : obj,
      ),
    }));

    console.log(`👁️ Toggled visibility for ${objectId}`);
  };

  // Toggle entire category visibility
  const toggleCategoryVisibility = (category) => {
    const newState = !editorState[`${category}Visible`];
    setEditorState((prev) => ({
      ...prev,
      [`${category}Visible`]: newState,
    }));

    // Update all objects in category
    setDynamicObjects((prev) => ({
      ...prev,
      [category]: prev[category].map((obj) => ({ ...obj, visible: newState })),
    }));

    console.log(`👁️ Toggled category ${category}: ${newState}`);
  };

  // Update object color
  const updateObjectColor = (color) => {
    if (!selectedObject) return;

    const objectType = selectedObject.type + "s";

    setDynamicObjects((prev) => ({
      ...prev,
      [objectType]: prev[objectType].map((obj) =>
        obj.id === selectedObject.id ? { ...obj, color } : obj,
      ),
    }));

    setEditorState((prev) => ({
      ...prev,
      wallColor: color,
    }));

    // Update color in 3D scene
    if (editorRef.current?.updateObjectColorInScene) {
      editorRef.current.updateObjectColorInScene(selectedObject.id, color);
    }

    console.log(`🎨 Updated color for ${selectedObject.id}: ${color}`);
  };

  const downloadModel = async () => {
    if (status.model_file) {
      try {
        const response = await axios.get(`/api/download/${status.model_file}`, {
          responseType: "blob",
        });

        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", status.model_file);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } catch (err) {
        setError("Failed to download model");
      }
    }
  };

  // Viewport control functions
  const resetView = () => {
    if (editorRef.current?.resetCamera) {
      editorRef.current.resetCamera();
    }
  };

  const setTopView = () => {
    if (editorRef.current?.setTopView) {
      editorRef.current.setTopView();
    }
  };

  const setFrontView = () => {
    if (editorRef.current?.setFrontView) {
      editorRef.current.setFrontView();
    }
  };

  const setSideView = () => {
    if (editorRef.current?.setSideView) {
      editorRef.current.setSideView();
    }
  };

  const takeScreenshot = () => {
    if (editorRef.current?.takeScreenshot) {
      editorRef.current.takeScreenshot();
    }
  };

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && editingMode) {
        setEditingMode(false);
        setIsFullscreenEdit(false);
        setSelectedObject(null);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [editingMode]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-6"></div>
          <h2 className="text-2xl font-semibold mb-4">Processing Blueprint</h2>
          <p className="text-gray-400 mb-6">
            Status: {status.status || "Initializing..."}
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="bg-red-900/20 border border-red-500 rounded-xl p-8 max-w-md">
          <h2 className="text-2xl font-semibold text-red-400 mb-4">
            Processing Error
          </h2>
          <p className="text-red-300 mb-6">{error}</p>
          <button
            onClick={() => navigate("/")}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (status.status === "completed") {
    const modelUrl = `/api/download/${status.model_file}`;

    return (
      <div className="min-h-screen bg-gray-900 text-white">
        {/* Enhanced Top Toolbar */}
        <div className="bg-gray-800 border-b border-gray-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <h1 className="text-xl font-bold text-blue-400 flex items-center">
                <BuildingStorefrontIcon className="w-6 h-6 mr-2" />
                3D Blueprint Editor
              </h1>

              <div className="flex items-center space-x-4">
                <button
                  // onClick={() => setEditingMode(!editingMode)}
                  onClick={() => {
                    const newMode = !editingMode;
                    setEditingMode(newMode);
                    setIsFullscreenEdit(newMode);
                  }}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                    editingMode
                      ? "bg-blue-600 text-white shadow-lg"
                      : "bg-gray-700 hover:bg-gray-600 text-gray-300"
                  }`}
                >
                  <WrenchScrewdriverIcon className="w-5 h-5" />
                  <span>
                    {/* {editingMode ? "Exit Edit" : "Edit Mode"} */}
                    {editingMode && (
                      <button
                        onClick={() => {
                          setEditingMode(false);
                          setIsFullscreenEdit(false);
                          setSelectedObject(null);
                        }}
                        className="absolute top-4 right-4 z-50 bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg text-white"
                      >
                        Exit Edit (ESC)
                      </button>
                    )}
                  </span>
                </button>

                {/* Add Wall Button */}
                {editingMode && (
                  <button
                    onClick={addWall}
                    className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-green-700 hover:bg-green-600 text-white transition-colors"
                  >
                    <PlusIcon className="w-5 h-5" />
                    <span>Add Wall</span>
                  </button>
                )}

                {/* Remove Object Button */}
                {editingMode && selectedObject && (
                  <button
                    onClick={removeSelectedObject}
                    className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-red-700 hover:bg-red-600 text-white transition-colors"
                  >
                    <TrashIcon className="w-5 h-5" />
                    <span>Remove {selectedObject.type}</span>
                  </button>
                )}

                <div className="flex items-center space-x-2 text-sm text-gray-400 bg-gray-700 px-3 py-2 rounded-lg">
                  <CubeIcon className="w-4 h-4 text-blue-400" />
                  <span>
                    {dynamicObjects.walls.filter((w) => w.visible).length} Walls
                  </span>
                  <span>•</span>
                  <span>
                    {dynamicObjects.rooms.filter((r) => r.visible).length} Rooms
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <button
                onClick={takeScreenshot}
                className="flex items-center space-x-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                <CameraIcon className="w-5 h-5" />
                <span>Screenshot</span>
              </button>

              <button
                onClick={downloadModel}
                className="flex items-center space-x-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                <ArrowDownTrayIcon className="w-5 h-5" />
                <span>Export GLB</span>
              </button>

              <button
                onClick={() => navigate("/")}
                className="flex items-center space-x-2 bg-gray-700 hover:bg-gray-600 text-gray-300 px-4 py-2 rounded-lg transition-colors"
              >
                <HomeIcon className="w-5 h-5" />
                <span>New Project</span>
              </button>
            </div>
          </div>
        </div>

        {/* Main Content */}
        {/* <div className="flex h-[calc(100vh-73px)]"> */}
        <div
          className={`flex transition-all duration-300 ${
            isFullscreenEdit
              ? "fixed inset-0 z-50 bg-gray-900"
              : "h-[calc(100vh-73px)]"
          }`}
        >
          {/* Enhanced Left Panel - Object Properties */}
          {editingMode && (
            <div className="w-96 bg-gray-800 border-r border-gray-700 overflow-y-auto">
              <div className="p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center">
                  <Cog6ToothIcon className="w-5 h-5 mr-2 text-blue-400" />
                  Object Properties
                </h3>

                {selectedObject ? (
                  <div className="space-y-6">
                    {/* Selected Object Info with Blue Highlight */}
                    <div className="bg-blue-900/30 border border-blue-600/50 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <label className="block text-sm font-medium text-blue-200">
                          🔹 Selected: {selectedObject.name || "Object"}
                        </label>
                        <div className="flex space-x-2">
                          <button
                            onClick={() =>
                              toggleObjectVisibility(
                                selectedObject.id,
                                selectedObject.type,
                              )
                            }
                            className="p-1 hover:bg-blue-700/50 rounded"
                            title="Toggle Visibility"
                          >
                            {dynamicObjects[selectedObject.type + "s"]?.find(
                              (obj) => obj.id === selectedObject.id,
                            )?.visible ? (
                              <EyeIcon className="w-4 h-4 text-blue-400" />
                            ) : (
                              <EyeSlashIcon className="w-4 h-4 text-gray-400" />
                            )}
                          </button>

                          <button
                            onClick={removeSelectedObject}
                            className="p-1 hover:bg-red-700/50 rounded"
                            title="Delete"
                          >
                            <TrashIcon className="w-4 h-4 text-red-400" />
                          </button>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <p className="text-sm text-blue-300">
                          Type: {selectedObject.type || "Wall"}
                        </p>
                        <p className="text-sm text-blue-300">
                          ID: {selectedObject.id || "N/A"}
                        </p>
                        <p className="text-sm text-blue-300">
                          Status:{" "}
                          {dynamicObjects[selectedObject.type + "s"]?.find(
                            (obj) => obj.id === selectedObject.id,
                          )?.visible
                            ? "✅ Visible"
                            : "❌ Hidden"}
                        </p>
                      </div>
                    </div>

                    {/* Color Controls */}
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2 flex items-center">
                        <PaintBrushIcon className="w-4 h-4 mr-2" />
                        Object Color
                      </label>
                      <div className="flex items-center space-x-3">
                        <input
                          type="color"
                          value={editorState.wallColor}
                          onChange={(e) => updateObjectColor(e.target.value)}
                          className="w-12 h-10 rounded border border-gray-600 bg-gray-700 cursor-pointer"
                        />
                        <input
                          type="text"
                          value={editorState.wallColor}
                          onChange={(e) => updateObjectColor(e.target.value)}
                          className="flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm text-white focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    </div>

                    {/* Height Control for Walls */}
                    {selectedObject.type === "wall" && (
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2 flex items-center">
                          <ArrowUpIcon className="w-4 h-4 mr-2" />
                          Wall Height: {editorState.wallHeight}m
                        </label>
                        <input
                          type="range"
                          min="2"
                          max="5"
                          step="0.1"
                          value={editorState.wallHeight}
                          onChange={(e) =>
                            setEditorState({
                              ...editorState,
                              wallHeight: parseFloat(e.target.value),
                            })
                          }
                          className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>2m</span>
                          <span>5m</span>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <Square3Stack3DIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>Select an object to edit properties</p>
                    <p className="text-sm mt-2">
                      Click on any 3D object in edit mode
                    </p>
                    <p className="text-sm mt-1 text-blue-400">
                      Selected objects will be highlighted in blue
                    </p>
                  </div>
                )}

                {/* Action Buttons */}
                {editingMode && (
                  <div className="mt-8 border-t border-gray-700 pt-6">
                    <h4 className="text-md font-semibold mb-4 flex items-center">
                      <PlusIcon className="w-4 h-4 mr-2 text-green-400" />
                      Quick Actions
                    </h4>

                    <div className="space-y-2">
                      <button
                        onClick={addWall}
                        className="w-full flex items-center space-x-2 px-4 py-2 bg-green-700 hover:bg-green-600 text-white rounded-lg transition-colors"
                      >
                        <PlusIcon className="w-4 h-4" />
                        <span>Add New Wall</span>
                      </button>

                      {selectedObject && (
                        <button
                          onClick={removeSelectedObject}
                          className="w-full flex items-center space-x-2 px-4 py-2 bg-red-700 hover:bg-red-600 text-white rounded-lg transition-colors"
                        >
                          <TrashIcon className="w-4 h-4" />
                          <span>Delete Selected</span>
                        </button>
                      )}
                    </div>
                  </div>
                )}

                {/* Global Settings */}
                <div className="mt-8 border-t border-gray-700 pt-6">
                  <h4 className="text-md font-semibold mb-4 flex items-center">
                    <AdjustmentsHorizontalIcon className="w-4 h-4 mr-2 text-purple-400" />
                    Global Settings
                  </h4>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Floor Color
                      </label>
                      <input
                        type="color"
                        value={editorState.floorColor}
                        onChange={(e) =>
                          setEditorState({
                            ...editorState,
                            floorColor: e.target.value,
                          })
                        }
                        className="w-full h-10 rounded border border-gray-600 bg-gray-700 cursor-pointer"
                      />
                    </div>

                    <div className="space-y-3">
                      <label className="flex items-center space-x-3 p-2 hover:bg-gray-700 rounded">
                        <input
                          type="checkbox"
                          checked={editorState.showGrid}
                          onChange={(e) =>
                            setEditorState({
                              ...editorState,
                              showGrid: e.target.checked,
                            })
                          }
                          className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded"
                        />
                        <CubeIcon className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-300">Show Grid</span>
                      </label>

                      <label className="flex items-center space-x-3 p-2 hover:bg-gray-700 rounded">
                        <input
                          type="checkbox"
                          checked={editorState.showWireframe}
                          onChange={(e) =>
                            setEditorState({
                              ...editorState,
                              showWireframe: e.target.checked,
                            })
                          }
                          className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded"
                        />
                        <Square3Stack3DIcon className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-300">
                          Wireframe Mode
                        </span>
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 3D Viewport */}
          <div className="flex-1 relative">
            {editingMode && (
              <div className="absolute top-1/2 left-4 -translate-y-1/2 bg-gray-800/95 backdrop-blur rounded-xl shadow-xl border border-gray-700 z-50">
                <div className="flex flex-col p-2 space-y-2">
                  <button title="Select" className="tool-btn">
                    🖱️
                  </button>
                  <button title="Move" className="tool-btn">
                    ↔️
                  </button>
                  <button title="Rotate" className="tool-btn">
                    ⟳
                  </button>
                  <button title="Scale" className="tool-btn">
                    ⬚
                  </button>
                  <button
                    title="Add Wall"
                    onClick={addWall}
                    className="tool-btn"
                  >
                    🧱
                  </button>
                  <button
                    title="Delete"
                    onClick={removeSelectedObject}
                    className="tool-btn"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            )}

            {/* Model Part  */}
            <Advanced3DEditor
              ref={editorRef}
              modelUrl={modelUrl}
              editingMode={editingMode}
              editorState={editorState}
              dynamicObjects={dynamicObjects}
              onObjectSelect={setSelectedObject}
              selectedObject={selectedObject}
            />

            {/* Enhanced Viewport Controls */}
            <div className="absolute top-4 right-4 bg-gray-800/95 backdrop-blur rounded-lg shadow-lg">
              <div className="p-3">
                <div className="text-xs text-gray-400 mb-3 text-center font-medium">
                  VIEW CONTROLS
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={resetView}
                    className="p-3 hover:bg-gray-700 rounded-lg transition-colors group"
                    title="Reset View"
                  >
                    <ArrowPathIcon className="w-5 h-5 text-gray-300 group-hover:text-blue-400" />
                  </button>
                  <button
                    onClick={() => {}}
                    className="p-3 hover:bg-gray-700 rounded-lg transition-colors group"
                    title="Perspective View"
                  >
                    <EyeIcon className="w-5 h-5 text-gray-300 group-hover:text-blue-400" />
                  </button>
                  <button
                    onClick={setTopView}
                    className="p-3 hover:bg-gray-700 rounded-lg transition-colors group"
                    title="Top View"
                  >
                    <ArrowUpIcon className="w-5 h-5 text-gray-300 group-hover:text-green-400" />
                  </button>
                  <button
                    onClick={setFrontView}
                    className="p-3 hover:bg-gray-700 rounded-lg transition-colors group"
                    title="Front View"
                  >
                    <ArrowRightIcon className="w-5 h-5 text-gray-300 group-hover:text-green-400" />
                  </button>
                </div>
              </div>
            </div>

            {/* Selection Info Overlay */}
            {selectedObject && editingMode && (
              <div className="absolute top-4 left-4 bg-blue-900/90 backdrop-blur border border-blue-500 rounded-lg px-4 py-2 shadow-lg">
                <div className="flex items-center space-x-3 text-sm">
                  <div className="w-3 h-3 bg-blue-400 rounded-full animate-pulse"></div>
                  <span className="text-blue-200">
                    Selected: {selectedObject.name}
                  </span>
                  <span className="text-blue-300">({selectedObject.type})</span>
                </div>
              </div>
            )}

            {/* Enhanced Status Bar */}
            {editorState.showStats && (
              <div className="absolute bottom-4 left-4 bg-gray-800/95 backdrop-blur rounded-lg px-4 py-3 shadow-lg">
                <div className="flex items-center space-x-6 text-sm text-gray-400">
                  <div className="flex items-center space-x-2">
                    <CubeIcon className="w-4 h-4 text-blue-400" />
                    <span>
                      Objects:{" "}
                      {dynamicObjects.walls.length +
                        dynamicObjects.doors.length +
                        dynamicObjects.windows.length}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <PhotoIcon className="w-4 h-4 text-green-400" />
                    <span>
                      Scale: {modelData?.scale_factor?.toFixed(1) || "1.0"}x
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    {editingMode ? (
                      <WrenchScrewdriverIcon className="w-4 h-4 text-yellow-400" />
                    ) : (
                      <EyeIcon className="w-4 h-4 text-blue-400" />
                    )}
                    <span>{editingMode ? "Edit Mode" : "View Mode"}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Enhanced Right Panel - Scene Hierarchy */}
          {editingMode && (
            <div className="w-64 bg-gray-800 border-l border-gray-700 overflow-y-auto">
              <div className="p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold flex items-center">
                    <ClipboardDocumentListIcon className="w-5 h-5 mr-2 text-purple-400" />
                    Scene Objects
                  </h3>
                  <button
                    onClick={addWall}
                    className="p-1 hover:bg-gray-700 rounded"
                    title="Add Wall"
                  >
                    <PlusIcon className="w-4 h-4 text-green-400" />
                  </button>
                </div>

                <div className="space-y-3">
                  {/* Walls Section */}
                  <div className="text-sm">
                    <div className="font-medium text-gray-300 mb-2 flex items-center justify-between">
                      <div className="flex items-center">
                        <CubeIcon className="w-4 h-4 mr-2 text-blue-400" />
                        Walls ({dynamicObjects.walls.length})
                      </div>
                      <button
                        onClick={() => toggleCategoryVisibility("walls")}
                        className="p-1 hover:bg-gray-700 rounded"
                      >
                        {editorState.wallsVisible ? (
                          <EyeIcon className="w-4 h-4 text-blue-400" />
                        ) : (
                          <EyeSlashIcon className="w-4 h-4 text-gray-400" />
                        )}
                      </button>
                    </div>
                    {dynamicObjects.walls.map((wall) => (
                      <div
                        key={wall.id}
                        className={`pl-6 py-2 rounded cursor-pointer transition-all flex items-center justify-between ${
                          selectedObject?.id === wall.id
                            ? "bg-blue-600 text-white shadow-lg border border-blue-400"
                            : "hover:bg-gray-700 text-gray-400 hover:text-gray-200"
                        }`}
                        onClick={() =>
                          setSelectedObject({
                            id: wall.id,
                            name: wall.name,
                            type: "wall",
                          })
                        }
                      >
                        <div className="flex items-center">
                          <span className="mr-2">🧱</span>
                          <span>{wall.name}</span>
                          {wall.isNew && (
                            <span className="ml-2 text-xs bg-green-600 px-1 rounded">
                              NEW
                            </span>
                          )}
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleObjectVisibility(wall.id, "wall");
                          }}
                          className="p-1 hover:bg-gray-600 rounded"
                        >
                          {wall.visible ? (
                            <EyeIcon className="w-3 h-3" />
                          ) : (
                            <EyeSlashIcon className="w-3 h-3 text-gray-500" />
                          )}
                        </button>
                      </div>
                    ))}
                  </div>

                  {/* Similar sections for doors, windows, rooms... */}
                  <div className="text-sm">
                    <div className="font-medium text-gray-300 mb-2 flex items-center">
                      <ArrowRightIcon className="w-4 h-4 mr-2 text-green-400" />
                      Doors ({dynamicObjects.doors.length})
                    </div>
                    {dynamicObjects.doors.map((door) => (
                      <div
                        key={door.id}
                        className={`pl-6 py-2 rounded cursor-pointer transition-all flex items-center justify-between ${
                          selectedObject?.id === door.id
                            ? "bg-blue-600 text-white shadow-lg"
                            : "hover:bg-gray-700 text-gray-400"
                        }`}
                        onClick={() =>
                          setSelectedObject({
                            id: door.id,
                            name: door.name,
                            type: "door",
                          })
                        }
                      >
                        <div className="flex items-center">
                          <span className="mr-2">🚪</span>
                          <span>{door.name}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return null;
};

export default ViewerPage;
