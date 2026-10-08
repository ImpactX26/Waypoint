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
  const [riskResult, setRiskResult] = useState(null);
  const [anchorResult, setAnchorResult] = useState(null);
  const [verifyResult, setVerifyResult] = useState(null);
  const [tamperResult, setTamperResult] = useState(null);

  const [error, setError] = useState("");
  const [riskError, setRiskError] = useState("");

  const [loading, setLoading] = useState(false);
  const [riskLoading, setRiskLoading] = useState(false);
  const [anchorLoading, setAnchorLoading] = useState(false);
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [tamperLoading, setTamperLoading] = useState(false);

  const [workflow, setWorkflow] = useState({
    create: true,
    risk: false,
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

  const assessRisk = async () => {
    setRiskLoading(true);
    setRiskError("");

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/handoffs/risk",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(formData),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.message || `Risk assessment returned ${response.status}`
        );
      }

      if (!data.success) {
        throw new Error(
          data.message || "Unable to assess handoff risk"
        );
      }

      setRiskResult(data);

      setWorkflow((previous) => ({
        ...previous,
        risk: true,
      }));

      return data;
    } catch (err) {
      console.error(err);

      setRiskError(
        err.message ||
          "Unable to assess handoff risk. Make sure the FastAPI backend is running."
      );

      return null;
    } finally {
      setRiskLoading(false);
    }
  };

  const createHandoff = async (event) => {
    event.preventDefault();

    setLoading(true);
    setError("");
    setRiskError("");

    setReceipt(null);
    setRiskResult(null);
    setAnchorResult(null);
    setVerifyResult(null);
    setTamperResult(null);

    setWorkflow({
      create: true,
      risk: false,
      sign: false,
      accept: false,
      receipt: false,
      anchor: false,
      verify: false,
    });

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

      setWorkflow((previous) => ({
        ...previous,
        create: true,
        receipt: true,
      }));

      // Run ML risk assessment using the same handoff data.
      await assessRisk();
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

  const handleAnchor = async () => {
    if (!receipt || !workflow.accept) {
      return;
    }

    setAnchorLoading(true);
    setError("");
    setAnchorResult(null);
    setVerifyResult(null);
    setTamperResult(null);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/handoffs/${receipt.handoff_id}/anchor`,
        {
          method: "POST",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.message || `Backend returned ${response.status}`
        );
      }

      if (!data.success) {
        throw new Error(data.message || "Unable to anchor handoff");
      }

      setAnchorResult(data);

      setWorkflow((previous) => ({
        ...previous,
        anchor: true,
        verify: false,
      }));
    } catch (err) {
      console.error(err);

      setError(
        err.message ||
          "Unable to anchor handoff. Make sure Hardhat and the FastAPI backend are running."
      );
    } finally {
      setAnchorLoading(false);
    }
  };

  const handleVerify = async () => {
    if (!receipt || !workflow.anchor) {
      return;
    }

    setVerifyLoading(true);
    setError("");
    setVerifyResult(null);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/handoffs/${receipt.handoff_id}/verify`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.message || `Backend returned ${response.status}`
        );
      }

      if (!data.success) {
        throw new Error(data.message || "Unable to verify handoff");
      }

      setVerifyResult(data);

      setWorkflow((previous) => ({
        ...previous,
        verify: data.verified,
      }));
    } catch (err) {
      console.error(err);

      setError(
        err.message ||
          "Unable to verify handoff. Make sure Hardhat and the FastAPI backend are running."
      );
    } finally {
      setVerifyLoading(false);
    }
  };

  const handleTamper = async () => {
    if (!receipt || !workflow.anchor) {
      return;
    }

    setTamperLoading(true);
    setError("");
    setTamperResult(null);
    setVerifyResult(null);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/handoffs/${receipt.handoff_id}/tamper`,
        {
          method: "POST",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.message || `Backend returned ${response.status}`
        );
      }

      if (!data.success) {
        throw new Error(data.message || "Unable to simulate tamper");
      }

      setTamperResult(data);

      setWorkflow((previous) => ({
        ...previous,
        verify: false,
      }));
    } catch (err) {
      console.error(err);

      setError(
        err.message ||
          "Unable to simulate tamper. Make sure the FastAPI backend is running."
      );
    } finally {
      setTamperLoading(false);
    }
  };

  const workflowItems = [
    {
      key: "create",
      number: "01",
      label: "CREATE",
      description: "Create handoff",
    },
    {
      key: "risk",
      number: "02",
      label: "RISK",
      description: "ML assessment",
    },
    {
      key: "sign",
      number: "03",
      label: "SIGN",
      description: "Outgoing analyst",
    },
    {
      key: "accept",
      number: "04",
      label: "ACCEPT",
      description: "Incoming analyst",
    },
    {
      key: "receipt",
      number: "05",
      label: "RECEIPT",
      description: "SHA-256 proof",
    },
    {
      key: "anchor",
      number: "06",
      label: "ANCHOR",
      description: "Blockchain",
    },
    {
      key: "verify",
      number: "07",
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
                {loading
                  ? "CREATING HANDOFF..."
                  : "CREATE HANDOFF"}
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
                  {workflow.sign
                    ? "✓ HANDOFF SIGNED"
                    : "SIGN HANDOFF"}
                </button>

                <button
                  type="button"
                  className={`secondary-button ${
                    workflow.accept ? "completed-button" : ""
                  }`}
                  onClick={handleAccept}
                  disabled={!workflow.sign || workflow.accept}
                >
                  {workflow.accept
                    ? "✓ HANDOFF ACCEPTED"
                    : "ACCEPT HANDOFF"}
                </button>

                <button
                  type="button"
                  className={`secondary-button ${
                    workflow.anchor ? "completed-button" : ""
                  }`}
                  onClick={handleAnchor}
                  disabled={
                    !workflow.accept ||
                    anchorLoading ||
                    workflow.anchor
                  }
                >
                  {anchorLoading
                    ? "ANCHORING..."
                    : workflow.anchor
                    ? "✓ HASH ANCHORED"
                    : "ANCHOR HASH"}
                </button>

                <button
                  type="button"
                  className={`secondary-button ${
                    workflow.verify
                      ? "completed-button"
                      : verifyResult && !verifyResult.verified
                      ? "failed-button"
                      : ""
                  }`}
                  onClick={handleVerify}
                  disabled={!workflow.anchor || verifyLoading}
                >
                  {verifyLoading
                    ? "VERIFYING..."
                    : verifyResult
                    ? verifyResult.verified
                      ? "✓ INTEGRITY VERIFIED"
                      : "✕ INTEGRITY FAILED"
                    : "VERIFY INTEGRITY"}
                </button>

                {workflow.anchor && (
                  <button
                    type="button"
                    className="tamper-button"
                    onClick={handleTamper}
                    disabled={tamperLoading}
                  >
                    {tamperLoading
                      ? "SIMULATING TAMPER..."
                      : tamperResult
                      ? "✓ TAMPER SIMULATED"
                      : "SIMULATE TAMPER"}
                  </button>
                )}
              </div>
            )}

            {error && (
              <div className="error-message">{error}</div>
            )}
          </div>

          <aside className="receipt-card">
            <div className="receipt-header">
              <div>
                <div className="receipt-title">
                  Cryptographic Receipt
                </div>

                <div className="receipt-subtitle">
                  SHA-256 integrity proof
                </div>
              </div>

              <div className="receipt-status">
                {verifyResult
                  ? verifyResult.verified
                    ? "✓ INTEGRITY VERIFIED"
                    : "✕ INTEGRITY FAILED"
                  : tamperResult
                  ? "⚠ TAMPER SIMULATED"
                  : anchorResult
                  ? "✓ HASH ANCHORED"
                  : receipt
                  ? "✓ RECEIPT CREATED"
                  : "AWAITING HANDOFF"}
              </div>
            </div>

            {!receipt ? (
              <div className="receipt-empty">
                <div className="empty-icon">⌑</div>

                <div className="empty-title">
                  Awaiting Handoff
                </div>

                <div className="empty-text">
                  Submit an incident handoff to generate its
                  cryptographic receipt.
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
                  <strong>
                    {receipt.handoff.incident_id}
                  </strong>
                </div>

                <div className="receipt-row">
                  <span>Created At</span>
                  <strong>{receipt.created_at}</strong>
                </div>

                {/* ML RISK ASSESSMENT */}
                {riskResult && (
                  <div className="risk-card">
                    <div className="risk-header">
                      <div>
                        <div className="risk-title">
                          ML Handoff Risk Assessment
                        </div>

                        <div className="risk-subtitle">
                          Random Forest prioritization
                        </div>
                      </div>

                      <div
                        className={`risk-level risk-${riskResult.risk.risk_level.toLowerCase()}`}
                      >
                        {riskResult.risk.risk_level}
                      </div>
                    </div>

                    <div className="risk-score-row">
                      <div className="risk-score">
                        {riskResult.risk.risk_score}
                      </div>

                      <div className="risk-score-label">
                        <span>RISK SCORE</span>
                        <strong>/ 100</strong>
                      </div>
                    </div>

                    <div className="risk-meter">
                      <div
                        className="risk-meter-fill"
                        style={{
                          width: `${Math.min(
                            100,
                            Math.max(
                              0,
                              riskResult.risk.risk_score
                            )
                          )}%`,
                        }}
                      ></div>
                    </div>

                    <div className="risk-reasons">
                      <div className="risk-reasons-title">
                        Assessment Factors
                      </div>

                      {riskResult.risk.reasons.map(
                        (reason, index) => (
                          <div
                            className="risk-reason"
                            key={index}
                          >
                            <span>•</span>
                            <span>{reason}</span>
                          </div>
                        )
                      )}
                    </div>

                    <div className="risk-model">
                      Model:{" "}
                      <strong>
                        {riskResult.risk.model}
                      </strong>
                    </div>
                  </div>
                )}

                {riskError && (
                  <div className="risk-error">
                    <strong>Risk assessment unavailable</strong>
                    <p>{riskError}</p>

                    <button
                      type="button"
                      className="secondary-button"
                      onClick={assessRisk}
                      disabled={riskLoading}
                    >
                      {riskLoading
                        ? "ASSESSING..."
                        : "RETRY RISK ASSESSMENT"}
                    </button>
                  </div>
                )}

                {riskLoading && !riskResult && (
                  <div className="risk-loading">
                    <div className="risk-loading-title">
                      ML Risk Assessment
                    </div>

                    <div>
                      Random Forest is evaluating the
                      handoff...
                    </div>
                  </div>
                )}

                <div className="hash-section">
                  <div className="hash-label">
                    SHA-256 RECEIPT HASH
                  </div>

                  <div className="hash-value">
                    {receipt.receipt_hash}
                  </div>

                  <div className="hash-explanation">
                    Cryptographic fingerprint of the complete
                    handoff state.
                  </div>
                </div>

                <div className="storage-note">
                  <div className="storage-icon">●</div>

                  <div>
                    <strong>
                      Incident data stored OFF-CHAIN
                    </strong>

                    <p>
                      Sensitive SOC handoff data remains in the
                      application database. Only its
                      cryptographic proof is anchored on
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
                        The outgoing analyst has completed the
                        signing stage.
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
                        The incoming analyst has accepted the
                        handoff.
                      </p>
                    </div>
                  </div>
                )}

                {anchorResult && (
                  <div className="blockchain-proof">
                    <div className="blockchain-proof-header">
                      <div className="storage-icon">⛓</div>

                      <div>
                        <strong>
                          Blockchain Proof Anchored
                        </strong>

                        <p>
                          The SHA-256 receipt has been recorded
                          on the blockchain.
                        </p>
                      </div>
                    </div>

                    <div className="proof-grid">
                      <div className="proof-item">
                        <span>BLOCK NUMBER</span>
                        <strong>
                          #{anchorResult.block_number}
                        </strong>
                      </div>

                      <div className="proof-item">
                        <span>HANDOFF ID</span>
                        <strong>
                          #{anchorResult.handoff_id}
                        </strong>
                      </div>
                    </div>

                    <div className="proof-field">
                      <span>BLOCKCHAIN HASH</span>
                      <code>
                        {anchorResult.blockchain_hash}
                      </code>
                    </div>

                    <div className="proof-field">
                      <span>TRANSACTION HASH</span>
                      <code>
                        {anchorResult.transaction_hash}
                      </code>
                    </div>

                    <div className="proof-field">
                      <span>CONTRACT ADDRESS</span>
                      <code>
                        {anchorResult.contract_address}
                      </code>
                    </div>

                    <div className="proof-field">
                      <span>ANCHORED AT</span>
                      <code>
                        {anchorResult.anchored_at}
                      </code>
                    </div>
                  </div>
                )}

                {tamperResult && (
                  <div className="tamper-note">
                    <div className="storage-icon">⚠</div>

                    <div>
                      <strong>Demo tamper applied</strong>

                      <p>
                        Severity changed from{" "}
                        <strong>
                          {tamperResult.original_value}
                        </strong>{" "}
                        to{" "}
                        <strong>
                          {tamperResult.tampered_value}
                        </strong>
                        .
                      </p>

                      <p>
                        The blockchain proof remains unchanged.
                      </p>
                    </div>
                  </div>
                )}

                {verifyResult && (
                  <div
                    className={
                      verifyResult.verified
                        ? "accepted-note"
                        : "error-message"
                    }
                  >
                    <div className="storage-icon">
                      {verifyResult.verified ? "✓" : "✕"}
                    </div>

                    <div>
                      <strong>
                        {verifyResult.status}
                      </strong>

                      <p>
                        The current handoff hash was
                        recalculated and compared with the
                        blockchain-anchored hash.
                      </p>

                      <div className="verification-comparison">
                        <div>
                          <span>CURRENT HASH</span>
                          <code>
                            {verifyResult.current_hash}
                          </code>
                        </div>

                        <div>
                          <span>BLOCKCHAIN HASH</span>
                          <code>
                            {verifyResult.blockchain_hash}
                          </code>
                        </div>
                      </div>

                      <div className="verification-source">
                        Blockchain transaction:{" "}
                        <code>
                          {
                            verifyResult.blockchain_transaction
                          }
                        </code>
                      </div>

                      <div className="verification-source">
                        Blockchain block:{" "}
                        <strong>
                          #{verifyResult.block_number}
                        </strong>
                      </div>
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