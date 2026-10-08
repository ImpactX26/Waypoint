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


app = FastAPI(
    title="HandoffChain",
    description=(
        "Tamper-evident SOC shift handoff system. "
        "Actual handoff data is stored off-chain while "
        "cryptographic receipt hashes are anchored on blockchain."
    ),
    version="1.0.0"
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
# This key is for the local Hardhat development blockchain only.
HARDHAT_PRIVATE_KEY = (
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
)


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


class Handoff(BaseModel):
    incident_id: str
    severity: str
    alert: str
    host: str
    status: str
    findings: str
    assessment: str
    pending_actions: str


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

    This is the core integrity check:
    if any handoff field changes after anchoring,
    the recalculated hash will also change.
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


@app.get("/")
def home():
    return {
        "project": "HandoffChain",
        "status": "running",
        "purpose": "Tamper-evident SOC shift handoff"
    }


@app.post("/handoffs")
def create_handoff(handoff: Handoff):
    """
    Create a structured SOC handoff and generate
    its SHA-256 cryptographic receipt.

    The actual incident data remains off-chain.
    """

    receipt_hash = generate_receipt_hash(handoff)

    created_at = datetime.utcnow().isoformat() + "Z"

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


@app.post("/handoffs/{handoff_id}/anchor")
def anchor_handoff(handoff_id: int):
    """
    Anchor the handoff's SHA-256 receipt hash
    on the blockchain.
    """

    db = SessionLocal()

    try:
        record = db.query(HandoffRecord).filter(
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

        transaction_receipt = web3.eth.wait_for_transaction_receipt(
            tx_hash
        )

        transaction_hash = tx_hash.hex()

        record.blockchain_tx = transaction_hash
        record.blockchain_hash = record.receipt_hash
        record.anchored_at = datetime.utcnow().isoformat() + "Z"

        db.commit()

        return {
            "success": True,
            "message": "Handoff hash anchored on blockchain",
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


@app.get("/handoffs/{handoff_id}/verify")
def verify_handoff(handoff_id: int):
    """
    Recalculate the hash from the CURRENT off-chain
    handoff data and compare it with the blockchain proof.
    """

    db = SessionLocal()

    try:
        record = db.query(HandoffRecord).filter(
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
                "message": "Handoff has not been anchored on blockchain"
            }

        web3 = get_web3()
        contract = get_contract(web3)

        blockchain_data = contract.functions.getHandoff(
            handoff_id
        ).call()

        blockchain_hash_bytes = blockchain_data[0]

        blockchain_hash = blockchain_hash_bytes.hex()

        if blockchain_hash.startswith("0x"):
            blockchain_hash = blockchain_hash[2:]

        # Recalculate from CURRENT off-chain fields.
        current_hash = generate_hash_from_record(record)

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
            "blockchain_transaction": record.blockchain_tx,
            "block_number": web3.eth.get_block(
                web3.eth.get_transaction(
                    record.blockchain_tx
                ).blockNumber
            ).number
        }

    finally:
        db.close()


@app.post(
    "/handoffs/{handoff_id}/tamper",
    tags=["DEMO / SECURITY TESTING"]
)
def simulate_tamper(handoff_id: int):
    """
    DEMO-ONLY SECURITY TEST ENDPOINT.

    This endpoint intentionally modifies a stored handoff
    after its cryptographic proof has been anchored.

    It is used only to demonstrate the tamper-detection
    capability of HandoffChain.

    The blockchain proof is deliberately NOT modified.
    """

    db = SessionLocal()

    try:
        record = db.query(HandoffRecord).filter(
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
                "message": "Handoff must be anchored before tampering"
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
                "DEMO ONLY: The blockchain proof was not changed. "
                "Verification should now fail."
            )
        }

    finally:
        db.close()