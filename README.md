# HandOffChain

**Blockchain-Backed Incident Handoff and Integrity Verification**

HandOffChain is an incident handoff system designed to maintain the integrity and traceability of operational handoff records. It combines a web interface, a Python backend, an SQLite database, cryptographic hashing, and a Solidity smart contract to create, transfer, anchor, and verify handoff records.

The system does not use machine learning or AI-based risk prediction. Integrity verification is performed using SHA-256 hashing and blockchain records.

## Features

* Create incident handoff records.
* Sign off and accept handoffs through the application workflow.
* Store handoff information in an SQLite database.
* Generate SHA-256 integrity receipts from handoff data.
* Anchor receipt hashes on a local Ethereum-compatible blockchain.
* Verify handoff integrity by comparing the current record with its anchored receipt.
* Demonstrate tampering by modifying a record after anchoring and checking whether verification detects the change.
* View blockchain transaction details and verification results.

## Technology Stack

| Component              | Technology      |
| ---------------------- | --------------- |
| Frontend               | React, Vite     |
| Backend                | Python, FastAPI |
| Database               | SQLite          |
| Blockchain development | Hardhat 3       |
| Smart contract         | Solidity        |
| Blockchain interaction | Web3.py         |
| Integrity mechanism    | SHA-256         |
| Local blockchain       | Hardhat Network |

## System Workflow

The application follows six primary steps.

### 1. CREATE — Create the handoff

The user enters the incident and handoff details, such as severity, affected host, findings, assessment, and pending actions. The backend stores the record in SQLite and assigns it an incident identifier.

### 2. SIGN — Sign off the handoff

The handoff proceeds through the sign-off stage in the application workflow, indicating that the outgoing party has reviewed the information.

### 3. ACCEPT — Accept the handoff

The receiving party accepts the handoff. This represents the transfer of responsibility and provides a clear workflow stage for tracking the incident.

### 4. RECEIPT — Generate the integrity receipt

The system generates a SHA-256 hash from a canonical representation of the handoff data. This receipt acts as a fingerprint of the record at the time of generation.

### 5. ANCHOR — Record the receipt on the blockchain

The backend submits the receipt hash to the deployed HandoffRegistry smart contract on the local blockchain. The transaction hash and blockchain receipt information can be used to trace the anchoring operation.

The complete handoff record remains in SQLite; the blockchain is used to record the integrity reference rather than the full incident data.

### 6. VERIFY — Verify integrity

The system retrieves the anchored receipt and recalculates the hash of the current handoff data. It compares the calculated hash with the recorded blockchain hash.

* **Verification passes:** the current record matches the anchored integrity reference.
* **Verification fails:** the current record differs from the anchored version, or the expected blockchain reference cannot be verified.

A tampering demonstration can modify a record after anchoring and run verification again to illustrate integrity detection.

## Architecture

```text
React + Vite Frontend
          |
          v
     FastAPI Backend
       /         \
      v           v
 SQLite Database  SHA-256 Receipt
                       |
                       v
               HandoffRegistry
               Solidity Contract
                       |
                       v
                Hardhat Network
```

## Project Structure

```text
HandOffChain/
├── abi/
├── blockchain/
│   ├── contracts/
│   │   └── HandoffRegistry.sol
│   ├── scripts/
│   ├── artifacts/
│   ├── cache/
│   ├── hardhat.config.ts
│   └── package.json
├── frontend/
├── .venv/
├── handoffchain.db
├── main.py
├── start-demo.ps1
└── README.md
```

## Prerequisites

Install the following software:

* Python 3
* Node.js and npm
* Visual Studio Code (recommended)

The Python virtual environment and Node.js dependencies must be installed before launching the application.

## Setup

### 1. Open the project directory

```powershell
cd C:\Users\Pranav\Desktop\HandOffChain
```

### 2. Prepare the Python environment

Activate the existing virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the backend dependencies if a `requirements.txt` file is provided:

```powershell
pip install -r requirements.txt
```

If the project does not contain `requirements.txt`, install dependencies according to the imports in `main.py` rather than assuming the file exists.

### 3. Install blockchain dependencies

```powershell
cd .\blockchain
npm install
```

Compile the smart contract:

```powershell
npx hardhat compile
```

### 4. Install frontend dependencies

```powershell
cd ..\frontend
npm install
```

## Running the Application

The project includes `start-demo.ps1`, which is intended to launch the local blockchain, deploy the contract, start the backend, and start the frontend.

From the project root:

```powershell
cd C:\Users\Pranav\Desktop\HandOffChain
.\start-demo.ps1
```

If the script fails, start each component separately and resolve any compilation or deployment errors before testing the complete workflow.

Expected local endpoints, subject to the configuration in the project:

* Frontend: `http://localhost:5173`
* Backend API: `http://127.0.0.1:8000`
* Backend API documentation: `http://127.0.0.1:8000/docs`
* Local blockchain RPC: `http://127.0.0.1:8545`

## Demonstration Procedure

1. Start the blockchain, backend, and frontend.
2. Create a new incident handoff.
3. Complete the sign-off and acceptance stages.
4. Generate the integrity receipt.
5. Anchor the receipt hash on the local blockchain.
6. Verify the handoff and observe the successful result.
7. Use the tampering demonstration, if enabled, to modify the anchored record.
8. Verify again and observe whether the integrity check detects the modification.

## Security and Scope

HandOffChain demonstrates record-integrity verification using cryptographic hashing and blockchain anchoring. SQLite stores the application records, while the smart contract stores the associated integrity reference.

The demonstration uses a local development blockchain and is not, by itself, a production deployment. The local network, development accounts, and test configuration should not be used with real operational or sensitive incident data.

SHA-256 provides an integrity comparison, not confidentiality. Blockchain anchoring does not encrypt incident records, prove that the original information was truthful, or automatically authenticate a person's identity. Authentication, authorization, secure key management, and production deployment controls would be required for a real-world system.

## Conclusion

HandOffChain provides a workflow for creating and transferring incident handoffs, generating cryptographic receipts, anchoring those receipts on a blockchain, and checking whether records have changed. Its primary focus is **traceability and integrity verification without machine-learning components**.
