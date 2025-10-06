import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import ViewerPage from "./pages/ViewerPage";
// import "./App.css";

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/viewer/:taskId" element={<ViewerPage />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
