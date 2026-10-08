from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import hashlib
import json
import os
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

from web3 import Web3
from eth_account import Account

from sklearn.ensemble import RandomForestClassifier


app = FastAPI(
    title="HandoffChain",
    description=(
        "Tamper-evident SOC shift handoff system with "
        "ML-based handoff risk assessment. Actual handoff data "
        "is stored off-chain while cryptographic receipt hashes "
        "are anchored on blockchain."
    ),
    version="1.1.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATABASE
# ============================================================

DATABASE_URL = "sqlite:///./handoffchain.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


class HandoffRecord(Base):
    __tablename__ = "handoffs"

    id = Column(Integer, primary_key=True, index=True)

    incident_id = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    alert = Column(Text, nullable=False)
    host = Column(String, nullable=False)
    status = Column(String, nullable=False)

    findings = Column(Text, nullable=False)
    assessment = Column(Text, nullable=False)
    pending_actions = Column(Text, nullable=False)

    receipt_hash = Column(String, nullable=False)
    created_at = Column(String, nullable=False)

    blockchain_tx = Column(String, nullable=True)
    blockchain_hash = Column(String, nullable=True)
    anchored_at = Column(String, nullable=True)


Base.metadata.create_all(bind=engine)


# ============================================================
# BLOCKCHAIN CONFIGURATION
# ============================================================

BLOCKCHAIN_RPC_URL = "http://127.0.0.1:8545"

CONTRACT_ADDRESS = Web3.to_checksum_address(
    "0x5FbDB2315678afecb367f032d93F642f64180aa3"
)

ABI_PATH = os.path.join(
    os.path.dirname(__file__),
    "abi",
    "HandoffRegistry.json"
)


# Hardhat Account #0.
# Local development blockchain only.
HARDHAT_PRIVATE_KEY = (
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
)


# ============================================================
# BLOCKCHAIN HELPERS
# ============================================================

def load_contract_abi():
    with open(ABI_PATH, "r", encoding="utf-8") as file:
        artifact = json.load(file)

    return artifact["abi"]


def get_web3():
    web3 = Web3(
        Web3.HTTPProvider(BLOCKCHAIN_RPC_URL)
    )

    if not web3.is_connected():
        raise RuntimeError(
            "Unable to connect to Hardhat blockchain at "
            "http://127.0.0.1:8545"
        )

    return web3


def get_contract(web3):
    return web3.eth.contract(
        address=CONTRACT_ADDRESS,
        abi=load_contract_abi()
    )


# ============================================================
# DATA MODELS
# ============================================================

class Handoff(BaseModel):
    incident_id: str
    severity: str
    alert: str
    host: str
    status: str
    findings: str
    assessment: str
    pending_actions: str


# ============================================================
# SHA-256 RECEIPT FUNCTIONS
# ============================================================

def generate_receipt_hash(handoff):
    handoff_data = {
        "incident_id": handoff.incident_id,
        "severity": handoff.severity,
        "alert": handoff.alert,
        "host": handoff.host,
        "status": handoff.status,
        "findings": handoff.findings,
        "assessment": handoff.assessment,
        "pending_actions": handoff.pending_actions,
    }

    canonical_data = json.dumps(
        handoff_data,
        sort_keys=True,
        separators=(",", ":")
    )

    return hashlib.sha256(
        canonical_data.encode("utf-8")
    ).hexdigest()


def generate_hash_from_record(record):
    """
    Recalculate the SHA-256 hash from the CURRENT database fields.

    If any handoff field changes after anchoring,
    the recalculated hash also changes.
    """

    handoff_data = {
        "incident_id": record.incident_id,
        "severity": record.severity,
        "alert": record.alert,
        "host": record.host,
        "status": record.status,
        "findings": record.findings,
        "assessment": record.assessment,
        "pending_actions": record.pending_actions,
    }

    canonical_data = json.dumps(
        handoff_data,
        sort_keys=True,
        separators=(",", ":")
    )

    return hashlib.sha256(
        canonical_data.encode("utf-8")
    ).hexdigest()


# ============================================================
# ML RISK ASSESSMENT
# ============================================================

def build_training_data():
    """
    Creates a small synthetic cybersecurity training dataset.

    This is a prototype/demo model. In a real deployment,
    the model would be trained using historical SOC incidents
    from the organization.
    """

    training_rows = []

    # Features:
    #
    # severity_score
    # active_status
    # findings_length
    # pending_actions_count
    # assessment_length
    # alert_length
    #
    # Label:
    # 0 = lower handoff risk
    # 1 = higher handoff risk

    for severity_score in [1, 2, 3, 4]:
        for active_status in [0, 1]:
            for findings_length in [50, 150, 300]:
                for pending_actions_count in [0, 1, 3, 5]:

                    assessment_length = (
                        80
                        if severity_score <= 2
                        else 180
                    )

                    alert_length = (
                        50
                        if severity_score <= 2
                        else 120
                    )

                    risk_value = (
                        severity_score * 2
                        + active_status * 2
                        + min(pending_actions_count, 5)
                        + (1 if findings_length > 200 else 0)
                    )

                    risk_label = 1 if risk_value >= 9 else 0

                    training_rows.append(
                        [
                            severity_score,
                            active_status,
                            findings_length,
                            pending_actions_count,
                            assessment_length,
                            alert_length,
                            risk_label
                        ]
                    )

    return training_rows


def train_risk_model():
    """
    Train a lightweight Random Forest classifier.

    The model is intentionally small so it can run locally
    without external services or paid compute.
    """

    rows = build_training_data()

    X = [
        row[:-1]
        for row in rows
    ]

    y = [
        row[-1]
        for row in rows
    ]

    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        max_depth=6
    )

    model.fit(X, y)

    return model


RISK_MODEL = train_risk_model()


def severity_to_score(severity):
    severity = severity.upper().strip()

    mapping = {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
        "CRITICAL": 4
    }

    return mapping.get(severity, 2)


def status_is_active(status):
    status = status.upper().strip()

    active_statuses = {
        "INVESTIGATING",
        "OPEN",
        "ACTIVE",
        "ESCALATED",
        "UNDER INVESTIGATION"
    }

    return 1 if status in active_statuses else 0


def count_pending_actions(pending_actions):
    """
    Estimate the number of pending actions from common
    separators used in the handoff form.
    """

    text = pending_actions.strip()

    if not text:
        return 0

    separators = [
        ",",
        ";",
        "\n"
    ]

    parts = [text]

    for separator in separators:
        new_parts = []

        for part in parts:
            new_parts.extend(
                part.split(separator)
            )

        parts = new_parts

    cleaned_parts = [
        part.strip()
        for part in parts
        if part.strip()
    ]

    return max(1, len(cleaned_parts))


def generate_risk_reasons(handoff, risk_score):
    reasons = []

    severity = handoff.severity.upper()
    status = handoff.status.upper()

    if severity in {"HIGH", "CRITICAL"}:
        reasons.append(
            f"{severity.title()} incident severity"
        )

    if status in {
        "INVESTIGATING",
        "OPEN",
        "ACTIVE",
        "ESCALATED",
        "UNDER INVESTIGATION"
    }:
        reasons.append(
            "Incident is still active"
        )

    pending_count = count_pending_actions(
        handoff.pending_actions
    )

    if pending_count >= 3:
        reasons.append(
            "Multiple pending actions remain"
        )
    elif pending_count >= 1:
        reasons.append(
            "Pending actions remain"
        )

    if len(handoff.findings) >= 200:
        reasons.append(
            "Detailed investigation findings recorded"
        )

    if not reasons:
        reasons.append(
            "No major high-risk indicators detected"
        )

    return reasons


def assess_handoff_risk(handoff):
    """
    Run the ML model against the current handoff.

    Returns:
        risk score
        risk level
        model information
        explanation factors
    """

    severity_score = severity_to_score(
        handoff.severity
    )

    active_status = status_is_active(
        handoff.status
    )

    findings_length = len(
        handoff.findings
    )

    pending_actions_count = count_pending_actions(
        handoff.pending_actions
    )

    assessment_length = len(
        handoff.assessment
    )

    alert_length = len(
        handoff.alert
    )

    features = [[
        severity_score,
        active_status,
        findings_length,
        pending_actions_count,
        assessment_length,
        alert_length
    ]]

    probabilities = RISK_MODEL.predict_proba(
        features
    )[0]

    # Probability of the high-risk class.
    high_risk_probability = float(
        probabilities[1]
    )

    risk_score = round(
        high_risk_probability * 100
    )

    if risk_score >= 70:
        risk_level = "HIGH"
    elif risk_score >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    reasons = generate_risk_reasons(
        handoff,
        risk_score
    )

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "reasons": reasons,
        "model": "Random Forest",
        "model_purpose": (
            "Prototype handoff risk prioritization"
        )
    }


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return {
        "project": "HandoffChain",
        "status": "running",
        "purpose": (
            "Tamper-evident SOC shift handoff "
            "with ML-based risk assessment"
        )
    }


# ============================================================
# ML RISK ENDPOINT
# ============================================================

@app.post("/handoffs/risk")
def predict_handoff_risk(handoff: Handoff):
    """
    Assess the operational risk/priority of a SOC handoff
    using the local Random Forest prototype model.

    This does NOT determine cryptographic integrity.
    SHA-256 + blockchain remain responsible for integrity
    verification.
    """

    result = assess_handoff_risk(
        handoff
    )

    return {
        "success": True,
        "message": "Handoff risk assessment completed",
        "risk": result
    }


# ============================================================
# CREATE HANDOFF
# ============================================================

@app.post("/handoffs")
def create_handoff(handoff: Handoff):
    """
    Create a structured SOC handoff and generate
    its SHA-256 cryptographic receipt.

    The actual incident data remains off-chain.
    """

    receipt_hash = generate_receipt_hash(
        handoff
    )

    created_at = (
        datetime.utcnow().isoformat()
        + "Z"
    )

    db = SessionLocal()

    try:
        record = HandoffRecord(
            incident_id=handoff.incident_id,
            severity=handoff.severity,
            alert=handoff.alert,
            host=handoff.host,
            status=handoff.status,
            findings=handoff.findings,
            assessment=handoff.assessment,
            pending_actions=handoff.pending_actions,
            receipt_hash=receipt_hash,
            created_at=created_at,
            blockchain_tx=None,
            blockchain_hash=None,
            anchored_at=None
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return {
            "message": "Handoff receipt created",
            "handoff_id": record.id,
            "receipt_hash": receipt_hash,
            "created_at": created_at,
            "handoff": handoff
        }

    finally:
        db.close()


# ============================================================
# BLOCKCHAIN ANCHOR
# ============================================================

@app.post("/handoffs/{handoff_id}/anchor")
def anchor_handoff(handoff_id: int):
    """
    Anchor the handoff's SHA-256 receipt hash
    on the blockchain.
    """

    db = SessionLocal()

    try:
        record = db.query(
            HandoffRecord
        ).filter(
            HandoffRecord.id == handoff_id
        ).first()

        if record is None:
            return {
                "success": False,
                "message": "Handoff not found"
            }

        if record.blockchain_tx:
            return {
                "success": False,
                "message": "Handoff already anchored",
                "handoff_id": handoff_id,
                "transaction_hash": record.blockchain_tx
            }

        web3 = get_web3()
        contract = get_contract(web3)

        account = Account.from_key(
            HARDHAT_PRIVATE_KEY
        )

        receipt_hash_bytes = bytes.fromhex(
            record.receipt_hash
        )

        nonce = web3.eth.get_transaction_count(
            account.address
        )

        transaction = contract.functions.anchorHandoff(
            handoff_id,
            receipt_hash_bytes
        ).build_transaction({
            "from": account.address,
            "nonce": nonce,
            "chainId": web3.eth.chain_id,
            "gas": 300000,
            "gasPrice": web3.eth.gas_price
        })

        signed_transaction = account.sign_transaction(
            transaction
        )

        tx_hash = web3.eth.send_raw_transaction(
            signed_transaction.raw_transaction
        )

        transaction_receipt = (
            web3.eth.wait_for_transaction_receipt(
                tx_hash
            )
        )

        transaction_hash = tx_hash.hex()

        record.blockchain_tx = transaction_hash
        record.blockchain_hash = record.receipt_hash
        record.anchored_at = (
            datetime.utcnow().isoformat()
            + "Z"
        )

        db.commit()

        return {
            "success": True,
            "message": (
                "Handoff hash anchored on blockchain"
            ),
            "handoff_id": handoff_id,
            "receipt_hash": record.receipt_hash,
            "blockchain_hash": record.blockchain_hash,
            "transaction_hash": transaction_hash,
            "block_number": transaction_receipt.blockNumber,
            "contract_address": CONTRACT_ADDRESS,
            "anchored_at": record.anchored_at
        }

    finally:
        db.close()


# ============================================================
# VERIFY HANDOFF
# ============================================================

@app.get("/handoffs/{handoff_id}/verify")
def verify_handoff(handoff_id: int):
    """
    Recalculate the hash from the CURRENT off-chain
    handoff data and compare it with the blockchain proof.
    """

    db = SessionLocal()

    try:
        record = db.query(
            HandoffRecord
        ).filter(
            HandoffRecord.id == handoff_id
        ).first()

        if record is None:
            return {
                "success": False,
                "message": "Handoff not found"
            }

        if not record.blockchain_tx:
            return {
                "success": False,
                "message": (
                    "Handoff has not been anchored "
                    "on blockchain"
                )
            }

        web3 = get_web3()
        contract = get_contract(web3)

        blockchain_data = (
            contract.functions.getHandoff(
                handoff_id
            ).call()
        )

        blockchain_hash_bytes = (
            blockchain_data[0]
        )

        blockchain_hash = (
            blockchain_hash_bytes.hex()
        )

        if blockchain_hash.startswith("0x"):
            blockchain_hash = blockchain_hash[2:]

        current_hash = (
            generate_hash_from_record(
                record
            )
        )

        verified = (
            current_hash.lower()
            == blockchain_hash.lower()
        )

        return {
            "success": True,
            "handoff_id": handoff_id,
            "stored_hash": record.receipt_hash,
            "current_hash": current_hash,
            "blockchain_hash": blockchain_hash,
            "verified": verified,
            "status": (
                "INTEGRITY VERIFIED"
                if verified
                else "INTEGRITY FAILED"
            ),
            "blockchain_transaction": (
                record.blockchain_tx
            ),
            "block_number": web3.eth.get_block(
                web3.eth.get_transaction(
                    record.blockchain_tx
                ).blockNumber
            ).number
        }

    finally:
        db.close()


# ============================================================
# DEMO TAMPER
# ============================================================

@app.post(
    "/handoffs/{handoff_id}/tamper",
    tags=["DEMO / SECURITY TESTING"]
)
def simulate_tamper(handoff_id: int):
    """
    DEMO-ONLY SECURITY TEST ENDPOINT.

    Intentionally modifies a stored handoff after its
    cryptographic proof has been anchored.

    The blockchain proof is deliberately NOT modified.
    """

    db = SessionLocal()

    try:
        record = db.query(
            HandoffRecord
        ).filter(
            HandoffRecord.id == handoff_id
        ).first()

        if record is None:
            return {
                "success": False,
                "message": "Handoff not found"
            }

        if not record.blockchain_tx:
            return {
                "success": False,
                "message": (
                    "Handoff must be anchored "
                    "before tampering"
                )
            }

        original_severity = record.severity

        # DEMO ONLY:
        # Intentionally modify the stored severity.
        if record.severity == "LOW":
            record.severity = "HIGH"
        else:
            record.severity = "LOW"

        db.commit()
        db.refresh(record)

        return {
            "success": True,
            "message": "Demo tamper applied",
            "handoff_id": handoff_id,
            "changed_field": "severity",
            "original_value": original_severity,
            "tampered_value": record.severity,
            "warning": (
                "DEMO ONLY: The blockchain proof "
                "was not changed. Verification "
                "should now fail."
            )
        }

    finally:
        db.close()