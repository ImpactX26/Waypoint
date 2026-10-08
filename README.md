# HandoffChain
Tamper-Evident SOC Shift Handoff System

## Overview
## Problem
## Proposed Solution
## How HandoffChain Works
## System Architecture
## Workflow
CREATE → RISK → SIGN → ACCEPT → RECEIPT → ANCHOR → VERIFY

## ML Risk Assessment
Random Forest
Risk score / 100
Risk prioritization — not tamper detection

## Cryptographic Integrity
SHA-256 receipt
Off-chain incident data
On-chain hash anchor

## Tamper Detection
Original hash
      ↓
Blockchain anchor
      ↓
Field modified
      ↓
New hash
      ↓
Hash mismatch
      ↓
INTEGRITY FAILED

## Why Blockchain?
## Why Off-Chain Storage?
## Technology Stack
## Project Structure
## Running the Project
## Demo Sequence
## Security Notes
## Current Prototype Scope
