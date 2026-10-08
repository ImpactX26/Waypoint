# HandoffChain

### Tamper-Evident SOC Shift Handoff System

HandoffChain is a cybersecurity prototype designed to protect the integrity of **Security Operations Center (SOC) shift handoffs**.

It combines structured incident handoff records, SHA-256 cryptographic hashing, blockchain-based proof anchoring, integrity verification, and a Random Forest-based risk prioritization layer.

The system keeps the actual SOC incident information **off-chain** while anchoring only its cryptographic proof on a local Ethereum-compatible blockchain.

---

## Problem

SOC analysts commonly work in shifts. During a shift transition, incident information must be transferred from an outgoing analyst to an incoming analyst.

The challenge is not only recording the handoff, but also being able to determine whether the accepted handoff was **modified afterward**.

If a handoff record is changed after its original receipt was created, a conventional application or database may not provide an independent reference that proves what the original record contained.

---

## Proposed Solution

HandoffChain creates a cryptographic fingerprint of each SOC handoff using **SHA-256**.

The system:

1. Creates a structured SOC handoff.
2. Assesses its risk using a Random Forest prototype.
3. Completes the handoff workflow.
4. Generates a SHA-256 receipt hash.
5. Stores the actual handoff data off-chain.
6. Anchors the receipt hash on blockchain.
7. Recalculates the hash during verification.
8. Compares the current hash with the blockchain-anchored hash.
9. Detects modification when the hashes no longer match.

### Core principle

**Incident Data → OFF-CHAIN**

**Cryptographic Proof → ON-CHAIN**

---

## Workflow

<p align="center">

<strong>CREATE</strong>
→ <strong>RISK</strong>
→ <strong>SIGN</strong>
→ <strong>ACCEPT</strong>
→ <strong>RECEIPT</strong>
→ <strong>ANCHOR</strong>
→ <strong>VERIFY</strong>

</p>

After verification, the system can perform a controlled tamper demonstration:

<p align="center">

<strong>VERIFY ✓</strong>
→ <strong>TAMPER</strong>
→ <strong>VERIFY ✗</strong>

</p>

---

## How It Works

### 1. Create Handoff

The outgoing SOC analyst enters structured incident information such as:

* Incident ID
* Severity
* Alert
* Affected host
* Status
* Findings
* Assessment
* Pending actions

The complete handoff is stored in the SQLite database.

### 2. Risk Assessment

The handoff is evaluated using a **Random Forest** prototype.

The current prototype considers incident characteristics such as severity, activity status, and pending actions to produce:

* Risk score
* Risk level
* Risk reasons

The ML component is intended for **handoff risk prioritization**.

It is not responsible for detecting blockchain tampering.

### 3. Receipt Generation

A canonical representation of the handoff is created and processed using SHA-256.

The resulting hash acts as a unique cryptographic fingerprint of the handoff.

Even a small change to the underlying handoff data results in a different hash.

### 4. Blockchain Anchoring

The SHA-256 receipt hash is sent to the `HandoffRegistry` Solidity smart contract.

The blockchain stores:

* Handoff ID
* Receipt hash
* Timestamp
* Address that anchored the proof

The sensitive incident information itself is not stored on-chain.

### 5. Integrity Verification

When verification is requested, HandoffChain:

1. Reads the current handoff from the database.
2. Recalculates its SHA-256 hash.
3. Retrieves the original receipt hash from the blockchain.
4. Compares both hashes.

If they match:

**INTEGRITY VERIFIED**

If they differ:

**INTEGRITY FAILED**

---

## Tamper Detection

HandoffChain includes a controlled security demonstration.

For example, an originally anchored handoff may contain:

```text
Severity: HIGH
```

The tamper demonstration changes the stored handoff to:

```text
Severity: LOW
```

The blockchain proof remains unchanged.

The system then recalculates the current handoff hash.

```text
Original Hash
      ↓
Blockchain Anchor
      ↓
Handoff Modified
      ↓
New Hash
      ↓
Compare
      ↓
Hash Mismatch
      ↓
INTEGRITY FAILED
```

This demonstrates that changing the handoff after anchoring produces a different cryptographic fingerprint.

> The tamper operation is intentionally implemented as a controlled demonstration and is not intended to represent normal user functionality.

---

## Why SHA-256?

SHA-256 provides a deterministic cryptographic fingerprint of the handoff.

For the same canonical handoff:

```text
Same Data → Same Hash
```

After modification:

```text
Changed Data → Different Hash
```

Therefore, the hash provides an efficient way to detect whether the handoff content has changed.

---

## Why Blockchain?

A normal SHA-256 hash can detect changes, but if both the handoff data and its reference hash are controlled by the same application or database, an attacker with sufficient access could potentially modify both.

HandoffChain uses blockchain as an **independent, tamper-evident reference** for the original receipt hash.

The application can therefore compare the current handoff against a proof that is stored separately from the off-chain incident record.

---

## Why Not Store the Incident Data on Blockchain?

SOC incident information can contain sensitive operational details.

Storing the complete incident record on-chain would introduce unnecessary privacy, storage, and cost concerns.

HandoffChain therefore uses a hybrid model:

| Data                 | Storage            |
| -------------------- | ------------------ |
| Incident details     | SQLite / off-chain |
| Findings             | SQLite / off-chain |
| Assessment           | SQLite / off-chain |
| Pending actions      | SQLite / off-chain |
| SHA-256 receipt hash | Blockchain         |
| Blockchain timestamp | Blockchain         |
| Anchoring address    | Blockchain         |

This keeps the sensitive information off-chain while preserving an independent integrity reference.

---

## Architecture

```text
┌───────────────────────────────┐
│        React Frontend         │
│                               │
│  Create / Risk / Sign /       │
│  Accept / Anchor / Verify     │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│       FastAPI Backend         │
│                               │
│  Handoff Management           │
│  SHA-256 Receipt Generation   │
│  Risk Assessment              │
│  Verification Logic           │
│  Web3.py Integration          │
└───────┬───────────────┬───────┘
        │               │
        ▼               ▼
┌───────────────┐   ┌────────────────────┐
│ SQLite        │   │ Hardhat Blockchain │
│               │   │                    │
│ Full Handoff  │   │ Receipt Hash       │
│ Data          │   │ Timestamp          │
└───────────────┘   │ Anchoring Address  │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │ HandoffRegistry    │
                    │ Solidity Contract   │
                    └────────────────────┘
```

---

## Technology Stack

### Frontend

* React
* Vite
* JavaScript
* CSS

### Backend

* Python
* FastAPI
* SQLAlchemy
* SQLite
* Web3.py

### Machine Learning

* scikit-learn
* Random Forest

### Cryptography

* SHA-256

### Blockchain

* Solidity
* Hardhat
* Ethereum-compatible local network

### Development

* Visual Studio Code
* PowerShell
* Git / GitHub

---

## Smart Contract

The project uses a Solidity smart contract named:

```text
HandoffRegistry
```

The contract maintains a mapping between a handoff ID and its blockchain proof.

Each anchored proof contains:

```text
Receipt Hash
Timestamp
Anchoring Address
Existence Status
```

The primary contract operations are:

```text
anchorHandoff()
getHandoff()
```

The contract prevents the same handoff ID from being anchored more than once.

---

## Machine Learning Layer

The ML component provides an additional prioritization layer for SOC handoffs.

The current prototype uses a Random Forest model to produce a risk assessment.

Example response:

```text
Risk Score: 89 / 100
Risk Level: HIGH

Reasons:
- High incident severity
- Incident is still active
- Multiple pending actions remain
```

The ML component is separate from the cryptographic integrity mechanism.

### Important distinction

```text
Random Forest
      ↓
Handoff Risk Prioritization

SHA-256 + Blockchain
      ↓
Handoff Integrity Verification
```

The ML model does **not** determine whether a handoff was tampered with.

---

## Security Model

HandoffChain separates the system into two layers:

### Off-Chain Layer

Contains the actual SOC handoff information.

```text
Incident Data
     ↓
SQLite
```

### Integrity Layer

Contains the cryptographic proof.

```text
Handoff
   ↓
SHA-256
   ↓
Receipt Hash
   ↓
Blockchain
```

This separation allows the system to protect the integrity of the handoff without placing the complete incident record on-chain.

---

## HandoffChain vs. SIEM

HandoffChain is **not a replacement for a SIEM**.

A SIEM focuses on areas such as:

* Security event collection
* Log aggregation
* Monitoring
* Correlation
* Alerting
* Detection

HandoffChain focuses specifically on the **integrity of SOC shift handoff records**.

It can therefore be viewed as an integrity/proof layer around the handoff process rather than a complete security monitoring platform.

---

## Project Structure

```text
HandoffChain/
│
├── abi/
│   └── HandoffRegistry.json
│
├── blockchain/
│   ├── contracts/
│   │   └── HandoffRegistry.sol
│   │
│   ├── scripts/
│   │   └── deploy.ts
│   │
│   ├── hardhat.config.ts
│   ├── package.json
│   └── package-lock.json
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   │
│   ├── package.json
│   └── package-lock.json
│
├── main.py
├── start-demo.ps1
├── .gitignore
└── README.md
```

---

## Running the Project

### Requirements

* Python
* Node.js
* npm
* Git
* VS Code

### Start the complete demo

From the project root:

```powershell
cd C:\Users\Pranav\Desktop\HandoffChain
.\start-demo.ps1
```

The startup script launches the required local services for the demonstration.

### Manual startup

If required, the components can also be started separately:

#### Blockchain

```powershell
cd blockchain
npx hardhat node
```

#### Smart Contract

In another terminal:

```powershell
cd blockchain
npx hardhat run scripts/deploy.ts --network localhost
```

#### Backend

From the project root with the Python environment activated:

```powershell
uvicorn main:app --reload
```

#### Frontend

```powershell
cd frontend
npm run dev
```

The frontend is served through the Vite development server.

---

## Demonstration Sequence

The recommended demonstration is:

```text
1. Create Handoff
2. Run Risk Assessment
3. Complete Sign Stage
4. Complete Accept Stage
5. Generate SHA-256 Receipt
6. Anchor Receipt Hash
7. Verify Integrity
8. Show INTEGRITY VERIFIED
9. Simulate Controlled Tamper
10. Verify Again
11. Show INTEGRITY FAILED
```

The most important demonstration is the final comparison:

```text
Current Hash ≠ Blockchain Hash
             ↓
     INTEGRITY FAILED
```

This provides a visible demonstration of the core security concept.

---

## Example Handoff

A demonstration handoff can contain:

```text
Incident ID:
INC-2048

Severity:
HIGH

Alert:
Suspicious authentication activity detected from an unusual source

Affected Host:
FIN-SRV-01

Status:
INVESTIGATING
```

Additional findings, assessment, and pending actions are included in the structured handoff.

---

## Prototype Scope

HandoffChain is a **working prototype** demonstrating the concept of blockchain-backed integrity verification for SOC shift handoffs.

The current implementation uses:

* SQLite for off-chain storage
* Hardhat for the local blockchain
* A local blockchain development account for transaction signing
* SHA-256 for receipt generation
* Random Forest for prototype risk prioritization

The blockchain used in the demonstration is a **local Ethereum-compatible Hardhat network**, not a public Ethereum deployment.

The current `SIGN` and `ACCEPT` stages represent workflow states in the prototype. They should not be interpreted as independent cryptographic analyst signatures.

---

## Security Considerations

HandoffChain demonstrates integrity verification rather than complete SOC security.

The prototype does not attempt to replace:

* SIEM platforms
* Identity and access management
* Endpoint detection systems
* Incident response platforms
* Production key management
* Enterprise blockchain infrastructure

Its focus is narrower:

> **Provide an independent, tamper-evident integrity reference for SOC shift handoff records.**

---

## Key Takeaway

HandoffChain addresses a specific integrity problem in SOC shift transitions.

Instead of relying only on an application database to preserve the history of an accepted handoff, the system creates a cryptographic fingerprint of the handoff and anchors that fingerprint on blockchain.

The actual incident data remains off-chain, while the blockchain preserves the independent integrity reference.

```text
SOC Handoff
     ↓
SHA-256 Fingerprint
     ↓
Blockchain Anchor
     ↓
Later Verification
     ↓
MATCH    → INTEGRITY VERIFIED
MISMATCH → INTEGRITY FAILED
```

**HandoffChain — proving whether an accepted SOC handoff remained unchanged.**
