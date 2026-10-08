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
    description="Tamper-evident SOC shift handoff system",
    version="1.0.0"
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# BLOCKCHAIN CONFIGURATION
# ---------------------------------------------------------

BLOCKCHAIN_RPC_URL = "http://127.0.0.1:8545"

CONTRACT_ADDRESS = Web3.to_checksum_address(
    "0x5FbDB2315678afecb367f032d93F642f64180aa3"
)

ABI_PATH = os.path.join(
    os.path.dirname(__file__),
    "abi",
    "HandoffRegistry.json"
)


# Hardhat's first local test account.
# This account exists only on the local development blockchain.
HARDHAT_PRIVATE_KEY = (
    "0x59c6995e998f97a5a0044976f0945389dc9e86dae88a8f5d"
    "f3c7b8f5f7a8c5f3"
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


# ---------------------------------------------------------
# REQUEST MODEL
# ---------------------------------------------------------

class Handoff(BaseModel):
    incident_id: str
    severity: str
    alert: str
    host: str
    status: str
    findings: str
    assessment: str
    pending_actions: str


# ---------------------------------------------------------
# SHA-256 RECEIPT
# ---------------------------------------------------------

def generate_receipt_hash(handoff: Handoff):

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

    receipt_hash = hashlib.sha256(
        canonical_data.encode("utf-8")
    ).hexdigest()

    return receipt_hash


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

@app.get("/")
def home():

    return {
        "project": "HandoffChain",
        "status": "running",
        "purpose": "Tamper-evident SOC shift handoff"
    }


# ---------------------------------------------------------
# CREATE HANDOFF
# ---------------------------------------------------------

@app.post("/handoffs")
def create_handoff(handoff: Handoff):

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


# ---------------------------------------------------------
# ANCHOR HANDOFF HASH ON BLOCKCHAIN
# ---------------------------------------------------------

@app.post("/handoffs/{handoff_id}/anchor")
def anchor_handoff(handoff_id: int):

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


# ---------------------------------------------------------
# VERIFY HANDOFF INTEGRITY
# ---------------------------------------------------------

@app.get("/handoffs/{handoff_id}/verify")
def verify_handoff(handoff_id: int):

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

        local_hash = record.receipt_hash

        verified = (
            local_hash.lower()
            == blockchain_hash.lower()
        )

        return {
            "success": True,
            "handoff_id": handoff_id,
            "stored_hash": local_hash,
            "blockchain_hash": blockchain_hash,
            "verified": verified,
            "status": (
                "INTEGRITY VERIFIED"
                if verified
                else "INTEGRITY FAILED"
            ),
            "blockchain_transaction": record.blockchain_tx,
            "block_number": blockchain_data[1]
        }

    finally:

        db.close()