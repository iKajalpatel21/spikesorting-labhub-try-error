// import React, { useRef, useState } from "react";
// import { BrowserRouter as Router, Routes, Route, useNavigate } from "react-router-dom";

// function Home() {
//   const navigate = useNavigate();
//   return (
//     <div style={{
//       minHeight: "100vh",
//       background: "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
//       display: "flex",
//       flexDirection: "column",
//       alignItems: "center",
//       justifyContent: "center",
//     }}>
//       <h1 style={{ color: "#fff", fontSize: "2.5rem", marginBottom: "40px" }}>
//         Welcome to Spikes Jobs!
//       </h1>
//       <div>
//         <button
//           style={{
//             margin: "20px",
//             padding: "20px 40px",
//             fontSize: "18px",
//             borderRadius: "8px",
//             border: "none",
//             background: "#4fc3f7",
//             color: "#fff",
//             cursor: "pointer",
//             boxShadow: "0 4px 14px rgba(0,0,0,0.15)",
//             transition: "background 0.2s",
//           }}
//           onClick={() => alert("New Pipeline clicked!")}
//         >
//           New Pipeline
//         </button>
//         <button
//           style={{
//             margin: "20px",
//             padding: "20px 40px",
//             fontSize: "18px",
//             borderRadius: "8px",
//             border: "none",
//             background: "#81c784",
//             color: "#fff",
//             cursor: "pointer",
//             boxShadow: "0 4px 14px rgba(0,0,0,0.15)",
//             transition: "background 0.2s",
//           }}
//           onClick={() => navigate("/submit-pipeline")}
//         >
//           Submit Pipeline
//         </button>
//       </div>
//     </div>
//   );
// }

// function SubmitPipeline() {
//   const [fileName, setFileName] = React.useState("");
//   const fileInputRef = React.useRef();

//   const handleFileChange = (e) => {
//     if (e.target.files.length > 0) {
//       setFileName(e.target.files[0].name);
//     } else {
//       setFileName("");
//     }
//   };

//   const handleSubmit = () => {
//     if (!fileName) {
//       alert("Please select a JSON file first!");
//       return;
//     }
//     alert(`Submitting file: ${fileName}`);
//     // Add your actual submit logic here
//   };

//   return (
//     <div
//       style={{
//         minHeight: "100vh",
//         background: "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
//         display: "flex",
//         flexDirection: "column",
//         alignItems: "center",
//         justifyContent: "center",
//       }}
//     >
//       <h2 style={{ color: "#fff", marginBottom: "30px" }}>Submit a Pipeline</h2>
//       <input
//         type="file"
//         accept=".json,application/json"
//         ref={fileInputRef}
//         style={{ display: "none" }}
//         onChange={handleFileChange}
//       />
//       <button
//         style={{
//           padding: "16px 32px",
//           fontSize: "18px",
//           borderRadius: "8px",
//           border: "none",
//           background: "#4fc3f7",
//           color: "#fff",
//           cursor: "pointer",
//           boxShadow: "0 4px 14px rgba(0,0,0,0.15)",
//           marginBottom: "20px",
//         }}
//         onClick={() => fileInputRef.current.click()}
//       >
//         Select JSON File
//       </button>
//       {fileName && (
//         <div style={{ color: "#fff", marginTop: "10px" }}>
//           Selected file: <b>{fileName}</b>
//         </div>
//       )}
//       <button
//         style={{
//           padding: "16px 32px",
//           fontSize: "18px",
//           borderRadius: "8px",
//           border: "none",
//           background: "#81c784",
//           color: "#fff",
//           cursor: "pointer",
//           boxShadow: "0 4px 14px rgba(0,0,0,0.15)",
//           marginTop: "30px",
//         }}
//         onClick={handleSubmit}
//       >
//         Submit
//       </button>
//     </div>
//   );
// }
// function App() {
//   return (
//     <Router>
//       <Routes>
//         <Route path="/" element={<Home />} />
//         <Route path="/submit-pipeline" element={<SubmitPipeline />} />
//       </Routes>
//     </Router>
//   );
// }
// export default App;

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
          onClick={() => navigate("/new-pipeline")}
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

function NewPipeline() {
  const [formData, setFormData] = useState({
    binfile: "",
    samplingRate: 30000.0,
    numberOfChannels: 64,
    gainToUV: 0.1949999928,
    offsetToUV: 0.0,
    probe: "",
    badChannels: []
  });
  const [resultJSON, setResultJSON] = useState("");

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleChannelToggle = (channelNum) => {
    setFormData(prev => ({
      ...prev,
      badChannels: prev.badChannels.includes(channelNum)
        ? prev.badChannels.filter(ch => ch !== channelNum)
        : [...prev.badChannels, channelNum]
    }));
  };

  const handleSubmit = () => {
    const jsonOutput = {
      "binfile": formData.binfile,
      "sampling rate": formData.samplingRate,
      "number of channels": formData.numberOfChannels,
      "gain_to_uV": formData.gainToUV,
      "offset_to_uV": formData.offsetToUV,
      "probe": formData.probe,
      "bad_channels": formData.badChannels.sort((a, b) => a - b)
    };
    setResultJSON(JSON.stringify(jsonOutput, null, 2));
  };

  const renderChannelCheckboxes = () => {
    const channels = [];
    for (let i = 1; i <= formData.numberOfChannels; i++) {
      channels.push(
        <label key={i} style={{ display: "flex", alignItems: "center", margin: "5px" }}>
          <input
            type="checkbox"
            checked={formData.badChannels.includes(i)}
            onChange={() => handleChannelToggle(i)}
            style={{ marginRight: "5px" }}
          />
          {i}
        </label>
      );
    }
    return channels;
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
      padding: "20px",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
    }}>
      <div style={{
        background: "rgba(255, 255, 255, 0.95)",
        padding: "30px",
        borderRadius: "12px",
        width: "100%",
        maxWidth: "600px",
        boxShadow: "0 8px 32px rgba(0,0,0,0.2)"
      }}>
        <h2 style={{ textAlign: "center", marginBottom: "30px", color: "#333" }}>
          Create Recording
        </h2>

        <div style={{ display: "grid", gap: "20px" }}>
          {/* Binfile */}
          <div>
            <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
              Binfile:
            </label>
            <input
              type="file"
              onChange={(e) => handleInputChange("binfile", e.target.files[0]?.name || "")}
              style={{ width: "100%", padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
            />
          </div>

          {/* Sampling Rate */}
          <div>
            <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
              Sampling Rate:
            </label>
            <input
              type="number"
              value={formData.samplingRate}
              onChange={(e) => handleInputChange("samplingRate", parseFloat(e.target.value))}
              style={{ width: "100%", padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
            />
          </div>

          {/* Number of Channels */}
          <div>
            <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
              Number of Channels:
            </label>
            <input
              type="number"
              value={formData.numberOfChannels}
              onChange={(e) => handleInputChange("numberOfChannels", parseInt(e.target.value))}
              style={{ width: "100%", padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
            />
          </div>

          {/* Gain to uV */}
          <div>
            <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
              Gain to uV:
            </label>
            <input
              type="number"
              step="any"
              value={formData.gainToUV}
              onChange={(e) => handleInputChange("gainToUV", parseFloat(e.target.value))}
              style={{ width: "100%", padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
            />
          </div>

          {/* Offset to uV */}
          <div>
            <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
              Offset to uV:
            </label>
            <input
              type="number"
              step="any"
              value={formData.offsetToUV}
              onChange={(e) => handleInputChange("offsetToUV", parseFloat(e.target.value))}
              style={{ width: "100%", padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
            />
          </div>

          {/* Probe */}
          <div>
            <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
              Probe:
            </label>
            <input
              type="file"
              onChange={(e) => handleInputChange("probe", e.target.files[0]?.name || "")}
              style={{ width: "100%", padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
            />
          </div>

          {/* Remove Bad Channels */}
          {formData.numberOfChannels > 0 && (
            <div>
              <label style={{ display: "block", marginBottom: "10px", fontWeight: "bold" }}>
                Remove Bad Channels:
              </label>
              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(60px, 1fr))",
                gap: "5px",
                maxHeight: "200px",
                overflowY: "auto",
                border: "1px solid #ddd",
                padding: "10px",
                borderRadius: "4px"
              }}>
                {renderChannelCheckboxes()}
              </div>
              {formData.badChannels.length > 0 && (
                <p style={{ marginTop: "10px", fontSize: "14px", color: "#666" }}>
                  Selected bad channels: {formData.badChannels.sort((a, b) => a - b).join(", ")}
                </p>
              )}
            </div>
          )}

          {/* Submit Button */}
          <button
            onClick={handleSubmit}
            style={{
              padding: "15px 30px",
              fontSize: "16px",
              borderRadius: "8px",
              border: "none",
              background: "#4fc3f7",
              color: "#fff",
              cursor: "pointer",
              boxShadow: "0 4px 14px rgba(0,0,0,0.15)",
              marginTop: "20px"
            }}
          >
            Submit
          </button>

          {/* JSON Result */}
          {resultJSON && (
            <div style={{ marginTop: "20px" }}>
              <h3 style={{ marginBottom: "10px" }}>Generated JSON:</h3>
              <pre style={{
                background: "#f5f5f5",
                padding: "15px",
                borderRadius: "4px",
                overflow: "auto",
                fontSize: "12px",
                border: "1px solid #ddd"
              }}>
                <code>{resultJSON}</code>
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SubmitPipeline() {
  const [fileName, setFileName] = useState("");
  const fileInputRef = useRef();

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
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
    }}>
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
        <Route path="/new-pipeline" element={<NewPipeline />} />
        <Route path="/submit-pipeline" element={<SubmitPipeline />} />
      </Routes>
    </Router>
  );
}

export default App;