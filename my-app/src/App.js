import React, { useRef, useState } from "react";
import { BrowserRouter as Router, Routes, Route, useNavigate } from "react-router-dom";

function Home() {
  const navigate = useNavigate();
  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
    }}>
      <h1 style={{ color: "#fff", fontSize: "2.5rem", marginBottom: "40px" }}>
        Welcome to Spikes Jobs!
      </h1>
      <div>
        <button
          style={{
            margin: "20px",
            padding: "20px 40px",
            fontSize: "18px",
            borderRadius: "8px",
            border: "none",
            background: "#4fc3f7",
            color: "#fff",
            cursor: "pointer",
            boxShadow: "0 4px 14px rgba(0,0,0,0.15)",
            transition: "background 0.2s",
          }}
          onClick={() => alert("New Pipeline clicked!")}
        >
          New Pipeline
        </button>
        <button
          style={{
            margin: "20px",
            padding: "20px 40px",
            fontSize: "18px",
            borderRadius: "8px",
            border: "none",
            background: "#81c784",
            color: "#fff",
            cursor: "pointer",
            boxShadow: "0 4px 14px rgba(0,0,0,0.15)",
            transition: "background 0.2s",
          }}
          onClick={() => navigate("/submit-pipeline")}
        >
          Submit Pipeline
        </button>
      </div>
    </div>
  );
}

function SubmitPipeline() {
  const [fileName, setFileName] = React.useState("");
  const fileInputRef = React.useRef();

  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      setFileName(e.target.files[0].name);
    } else {
      setFileName("");
    }
  };

  const handleSubmit = () => {
    if (!fileName) {
      alert("Please select a JSON file first!");
      return;
    }
    alert(`Submitting file: ${fileName}`);
    // Add your actual submit logic here
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <h2 style={{ color: "#fff", marginBottom: "30px" }}>Submit a Pipeline</h2>
      <input
        type="file"
        accept=".json,application/json"
        ref={fileInputRef}
        style={{ display: "none" }}
        onChange={handleFileChange}
      />
      <button
        style={{
          padding: "16px 32px",
          fontSize: "18px",
          borderRadius: "8px",
          border: "none",
          background: "#4fc3f7",
          color: "#fff",
          cursor: "pointer",
          boxShadow: "0 4px 14px rgba(0,0,0,0.15)",
          marginBottom: "20px",
        }}
        onClick={() => fileInputRef.current.click()}
      >
        Select JSON File
      </button>
      {fileName && (
        <div style={{ color: "#fff", marginTop: "10px" }}>
          Selected file: <b>{fileName}</b>
        </div>
      )}
      <button
        style={{
          padding: "16px 32px",
          fontSize: "18px",
          borderRadius: "8px",
          border: "none",
          background: "#81c784",
          color: "#fff",
          cursor: "pointer",
          boxShadow: "0 4px 14px rgba(0,0,0,0.15)",
          marginTop: "30px",
        }}
        onClick={handleSubmit}
      >
        Submit
      </button>
    </div>
  );
}
function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/submit-pipeline" element={<SubmitPipeline />} />
      </Routes>
    </Router>
  );
}
export default App;