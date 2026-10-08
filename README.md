# HandoffChain

## Tamper-Evident SOC Shift Handoff System

HandoffChain is a cybersecurity and blockchain prototype designed to provide a tamper-evident integrity layer for Security Operations Center (SOC) shift handoffs.

It records a structured incident handoff off-chain, generates a SHA-256 cryptographic receipt, anchors that receipt on a blockchain, and later verifies whether the handoff has been modified.

---

## Problem

SOC analysts commonly work in shifts, meaning incident information must be transferred from an outgoing analyst to an incoming analyst.

A handoff may be accepted and stored, but the system needs a way to determine whether the recorded handoff was changed afterwards.

A normal database record alone does not provide an independent integrity reference.

HandoffChain addresses this by creating a cryptographic proof of the handoff and anchoring that proof on blockchain.

---

## Proposed Solution

HandoffChain separates the incident information from its integrity proof.

The actual SOC handoff data remains stored off-chain in a local SQLite database.

A SHA-256 hash is generated from the complete handoff state.

Only this cryptographic receipt is anchored on the blockchain through a Solidity smart contract.

During verification, HandoffChain recalculates the hash from the current off-chain handoff and compares it with the blockchain-anchored hash.

If the values match, the handoff is considered intact.

If the values differ, the system reports an integrity failure.

---

## Core Workflow

```text
CREATE
   ↓
SIGN
   ↓
ACCEPT
   ↓
SHA-256 RECEIPT
   ↓
ANCHOR HASH ON BLOCKCHAIN
   ↓
VERIFY
   ↓
SIMULATE TAMPER
   ↓
VERIFY AGAIN
   ↓
INTEGRITY FAILED
