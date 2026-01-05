import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const Upload = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    setFile(selectedFile);
    setError("");
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file");
      return;
    }

    const ext = file.name.split(".").pop().toLowerCase();
    const allowed = ["dxf", "png", "jpg", "jpeg"];
    if (!allowed.includes(ext)) {
      setError("Supported formats: DXF, PNG, JPG, JPEG.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setUploading(true);
      setError("");

      const response = await axios.post("/api/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      const { task_id } = response.data;
      navigate(`/viewer/${task_id}`);
    } catch (error) {
      setError(
        error.response?.data?.error || "Upload failed. Please try again."
      );
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-container">
      <div className="bg-white p-8 rounded-lg shadow-md max-w-md mx-auto">
        <h2 className="text-2xl font-bold mb-6 text-center">
          Upload Blueprint
        </h2>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Blueprint (DXF / Image)
          </label>
          <input
            type="file"
            accept=".dxf,.png,.jpg,.jpeg"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-500
                   file:mr-4 file:py-2 file:px-4
                   file:rounded-full file:border-0
                   file:text-sm file:font-semibold
                   file:bg-indigo-50 file:text-indigo-700
                   hover:file:bg-indigo-100"
          />
        </div>

        {file && (
          <div className="mb-4 p-3 bg-gray-50 rounded">
            <p className="text-sm text-gray-600">Selected: {file.name}</p>
            <p className="text-xs text-gray-500">
              Size: {(file.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>
        )}

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={uploading || !file}
          className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md
                   hover:bg-indigo-700 disabled:bg-gray-400 
                   disabled:cursor-not-allowed transition duration-200"
        >
          {uploading ? "Processing..." : "Generate 3D Model"}
        </button>

        <div className="mt-4 text-xs text-gray-500">
          <p>Supported formats: DXF, PNG, JPG, JPEG</p>
          <p>Max file size: 16MB</p>
        </div>
      </div>
    </div>
  );
};

export default Upload;
