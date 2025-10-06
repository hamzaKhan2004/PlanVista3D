import React from "react";
import Upload from "../components/Upload";

const Home = () => {
  return (
    <div className="home-page">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Transform Your Blueprints into 3D Models
        </h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Upload your floor plan or blueprint image, and our AI-powered system
          will automatically generate a detailed 3D model that you can explore
          and interact with in real-time.
        </p>
      </div>

      <Upload />

      <div className="mt-12 grid md:grid-cols-3 gap-8 px-4">
        <div className="text-center">
          <div className="bg-indigo-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">📋</span>
          </div>
          <h3 className="text-lg font-semibold mb-2">Upload Blueprint</h3>
          <p className="text-gray-600">
            Upload your floor plan in PNG, JPG, or PDF format
          </p>
        </div>

        <div className="text-center">
          <div className="bg-indigo-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">🔄</span>
          </div>
          <h3 className="text-lg font-semibold mb-2">AI Processing</h3>
          <p className="text-gray-600">
            Our system analyzes walls, rooms, and generates 3D geometry
          </p>
        </div>

        <div className="text-center">
          <div className="bg-indigo-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">🏠</span>
          </div>
          <h3 className="text-lg font-semibold mb-2">3D Model</h3>
          <p className="text-gray-600">
            View and interact with your 3D model in the browser
          </p>
        </div>
      </div>
    </div>
  );
};

export default Home;
