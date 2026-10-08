import { useState } from "react";
import "./App.css";

function App() {
  const [formData, setFormData] = useState({
    incident_id: "",
    severity: "HIGH",
    alert: "",
    host: "",
    status: "INVESTIGATING",
    findings: "",
    assessment: "",
    pending_actions: "",
  });

  const [receipt, setReceipt] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [workflow, setWorkflow] = useState({
    create: true,
    sign: false,
    accept: false,
    receipt: false,
    anchor: false,
    verify: false,
  });

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const createHandoff = async (event) => {
    event.preventDefault();

    setLoading(true);
    setError("");
    setReceipt(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/handoffs", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data = await response.json();

      setReceipt(data);

      setWorkflow({
        create: true,
        sign: false,
        accept: false,
        receipt: true,
        anchor: false,
        verify: false,
      });
    } catch (err) {
      console.error(err);

      setError(
        "Unable to create handoff. Make sure the FastAPI backend is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSign = () => {
    if (!receipt) {
      return;
    }

    setWorkflow((previous) => ({
      ...previous,
      sign: true,
    }));
  };

  const handleAccept = () => {
    if (!receipt || !workflow.sign) {
      return;
    }

    setWorkflow((previous) => ({
      ...previous,
      accept: true,
    }));
  };

  const workflowItems = [
    {
      key: "create",
      number: "01",
      label: "CREATE",
      description: "Create handoff",
    },
    {
      key: "sign",
      number: "02",
      label: "SIGN",
      description: "Outgoing analyst",
    },
    {
      key: "accept",
      number: "03",
      label: "ACCEPT",
      description: "Incoming analyst",
    },
    {
      key: "receipt",
      number: "04",
      label: "RECEIPT",
      description: "SHA-256 proof",
    },
    {
      key: "anchor",
      number: "05",
      label: "ANCHOR",
      description: "Blockchain",
    },
    {
      key: "verify",
      number: "06",
      label: "VERIFY",
      description: "Integrity check",
    },
  ];

  return (
    <div className="app">
      <header className="header">
        <div>
          <div className="brand">HandoffChain</div>
          <div className="subtitle">
            Tamper-Evident SOC Shift Handoff System
          </div>
        </div>

        <div className="connection-status">
          <span className="status-dot"></span>
          Backend Connected
        </div>
      </header>

      <main className="main">
        <section className="workflow-section">
          <div className="section-label">HANDOFF WORKFLOW</div>

          <div className="workflow">
            {workflowItems.map((item, index) => (
              <div className="workflow-wrapper" key={item.key}>
                <div
                  className={`workflow-step ${
                    workflow[item.key] ? "active" : ""
                  }`}
                >
                  <div className="workflow-number">{item.number}</div>

                  <div>
                    <div className="workflow-label">{item.label}</div>
                    <div className="workflow-description">
                      {item.description}
                    </div>
                  </div>
                </div>

                {index < workflowItems.length - 1 && (
                  <div className="workflow-line"></div>
                )}
              </div>
            ))}
          </div>
        </section>

        <section className="content">
          <div className="form-card">
            <div className="card-header">
              <div>
                <div className="card-title">Create SOC Handoff</div>
                <div className="card-description">
                  Record the current SOC incident state for the incoming
                  analyst.
                </div>
              </div>

              <div className="security-badge">OFF-CHAIN DATA</div>
            </div>

            <form onSubmit={createHandoff}>
              <div className="form-grid">
                <div className="field">
                  <label>Incident ID</label>

                  <input
                    name="incident_id"
                    value={formData.incident_id}
                    onChange={handleChange}
                    placeholder="INC-2048"
                    required
                  />
                </div>

                <div className="field">
                  <label>Severity</label>

                  <select
                    name="severity"
                    value={formData.severity}
                    onChange={handleChange}
                  >
                    <option value="LOW">LOW</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HIGH">HIGH</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                </div>

                <div className="field field-full">
                  <label>Alert</label>

                  <input
                    name="alert"
                    value={formData.alert}
                    onChange={handleChange}
                    placeholder="Suspicious authentication activity detected"
                    required
                  />
                </div>

                <div className="field">
                  <label>Affected Host</label>

                  <input
                    name="host"
                    value={formData.host}
                    onChange={handleChange}
                    placeholder="FIN-SRV-01"
                    required
                  />
                </div>

                <div className="field">
                  <label>Status</label>

                  <select
                    name="status"
                    value={formData.status}
                    onChange={handleChange}
                  >
                    <option value="OPEN">OPEN</option>
                    <option value="INVESTIGATING">INVESTIGATING</option>
                    <option value="CONTAINED">CONTAINED</option>
                    <option value="RESOLVED">RESOLVED</option>
                  </select>
                </div>

                <div className="field field-full">
                  <label>Findings</label>

                  <textarea
                    name="findings"
                    value={formData.findings}
                    onChange={handleChange}
                    placeholder="Describe the investigation findings..."
                    rows="4"
                    required
                  />
                </div>

                <div className="field field-full">
                  <label>Assessment</label>

                  <textarea
                    name="assessment"
                    value={formData.assessment}
                    onChange={handleChange}
                    placeholder="Current assessment of the incident..."
                    rows="3"
                    required
                  />
                </div>

                <div className="field field-full">
                  <label>Pending Actions</label>

                  <textarea
                    name="pending_actions"
                    value={formData.pending_actions}
                    onChange={handleChange}
                    placeholder="Actions that the incoming analyst needs to continue..."
                    rows="3"
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                className="primary-button"
                disabled={loading}
              >
                {loading ? "CREATING HANDOFF..." : "CREATE HANDOFF"}
              </button>
            </form>

            {receipt && (
              <div className="handoff-actions">
                <button
                  type="button"
                  className={`secondary-button ${
                    workflow.sign ? "completed-button" : ""
                  }`}
                  onClick={handleSign}
                  disabled={workflow.sign}
                >
                  {workflow.sign ? "✓ HANDOFF SIGNED" : "SIGN HANDOFF"}
                </button>

                <button
                  type="button"
                  className={`secondary-button ${
                    workflow.accept ? "completed-button" : ""
                  }`}
                  onClick={handleAccept}
                  disabled={!workflow.sign || workflow.accept}
                >
                  {workflow.accept ? "✓ HANDOFF ACCEPTED" : "ACCEPT HANDOFF"}
                </button>
              </div>
            )}

            {error && <div className="error-message">{error}</div>}
          </div>

          <aside className="receipt-card">
            <div className="receipt-header">
              <div>
                <div className="receipt-title">Cryptographic Receipt</div>

                <div className="receipt-subtitle">
                  SHA-256 integrity proof
                </div>
              </div>

              <div className="receipt-status">
                {receipt ? "✓ RECEIPT CREATED" : "AWAITING HANDOFF"}
              </div>
            </div>

            {!receipt ? (
              <div className="receipt-empty">
                <div className="empty-icon">⌑</div>

                <div className="empty-title">Awaiting Handoff</div>

                <div className="empty-text">
                  Submit an incident handoff to generate its cryptographic
                  receipt.
                </div>
              </div>
            ) : (
              <div className="receipt-details">
                <div className="receipt-row">
                  <span>Handoff ID</span>
                  <strong>#{receipt.handoff_id}</strong>
                </div>

                <div className="receipt-row">
                  <span>Incident</span>
                  <strong>{receipt.handoff.incident_id}</strong>
                </div>

                <div className="receipt-row">
                  <span>Created At</span>
                  <strong>{receipt.created_at}</strong>
                </div>

                <div className="hash-section">
                  <div className="hash-label">
                    SHA-256 RECEIPT HASH
                  </div>

                  <div className="hash-value">
                    {receipt.receipt_hash}
                  </div>
                </div>

                <div className="storage-note">
                  <div className="storage-icon">●</div>

                  <div>
                    <strong>Incident data stored OFF-CHAIN</strong>

                    <p>
                      Only the cryptographic proof will be anchored on
                      blockchain.
                    </p>
                  </div>
                </div>

                {workflow.sign && (
                  <div className="signed-note">
                    <div className="storage-icon">✓</div>

                    <div>
                      <strong>Handoff signed</strong>

                      <p>
                        The outgoing analyst has signed the current handoff.
                      </p>
                    </div>
                  </div>
                )}

                {workflow.accept && (
                  <div className="accepted-note">
                    <div className="storage-icon">✓</div>

                    <div>
                      <strong>Handoff accepted</strong>

                      <p>
                        The incoming analyst has accepted the handoff.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </aside>
        </section>
      </main>
    </div>
  );
}

export default App;