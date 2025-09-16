import React from "react";
import "./App.css";

function App() {
  return (
    <div
      className="App"
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
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
          onClick={() => alert("New Job Submission clicked!")}
        >
          New Job Submission
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
          onClick={() => alert("Submit a Pipeline clicked!")}
        >
          Submit a Pipeline
        </button>
      </div>
    </div>
  );
}

export default App;