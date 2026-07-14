"use client";

import { useState, useEffect } from "react";

export default function Home() {
  const [error, setError] = useState<string | null>(null);
  const [documents, setDocuments] = useState<string[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<string | null>(null);

  useEffect(() => {
    async function fetchDocuments() {
      try {
        const response = await fetch("http://localhost:8000/documents");
        const data = await response.json();
        setDocuments(data);
        if (data.length > 0) {
          setSelectedDocument(data[0]);
        }
      } catch (err) {
        console.error("Failed to fetch documents:", err);
      }
    }
    fetchDocuments();
  }, []);

  async function handleFileUpload(
    event: React.ChangeEvent<HTMLInputElement>
  ) {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("http://localhost:8000/upload", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    console.log(data);

    // Check if response contains an error
    if (data["Error Message"]) {
      setError(`Error: ${file.name} has already been uploaded`);
      // Clear error after 5 seconds
      setTimeout(() => setError(null), 5000);
    } else {
      setError(null);
      // Refresh documents list
      const docsResponse = await fetch("http://localhost:8000/documents");
      const docsData = await docsResponse.json();
      setDocuments(docsData);
      if (docsData.length > 0) {
        setSelectedDocument(docsData[0]);
      }
    }
  }

  return (
    <main className="page-shell">
      <div className="page-frame">
        <div className="sidebar">
          <label htmlFor="file-input" className="upload-button">
            <img
              className="upload-icon"
              src="/plus-svgrepo-com.svg"
              alt="Upload File"
            />
            <span>New File</span>
          </label>

          <div className="documents-tabs">
            {documents.map((doc) => (
              <button
                key={doc}
                className={`document-tab ${selectedDocument === doc ? "active" : ""}`}
                onClick={() => setSelectedDocument(doc)}
              >
                {doc}
              </button>
            ))}
          </div>
        </div>

        <div className="page-title-container">
          <h1 className="page-title">DocuChat</h1>
        </div>

        <div className="page-content">
          {error && <div className="error-message">{error}</div>}

          <div className="input-container">
            <input
              type="text"
              className="message-input"
              placeholder="Type your message..."
            />
            <button className="send-button">
              <img
                src="/send-svgrepo-com.svg"
                alt="Send"
                className="send-icon"
              />
            </button>
          </div>
        </div>
      </div>

      <input
        type="file"
        id="file-input"
        onChange={handleFileUpload}
      />
    </main>
  );
}