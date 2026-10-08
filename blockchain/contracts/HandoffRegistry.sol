// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

contract HandoffRegistry {

    struct HandoffProof {
        bytes32 receiptHash;
        uint256 timestamp;
        address anchoredBy;
        bool exists;
    }

    mapping(uint256 => HandoffProof) private handoffs;

    event HandoffAnchored(
        uint256 indexed handoffId,
        bytes32 indexed receiptHash,
        address indexed anchoredBy,
        uint256 timestamp
    );

    function anchorHandoff(
        uint256 handoffId,
        bytes32 receiptHash
    ) external {

        require(
            handoffId > 0,
            "Invalid handoff ID"
        );

        require(
            receiptHash != bytes32(0),
            "Invalid receipt hash"
        );

        require(
            !handoffs[handoffId].exists,
            "Handoff already anchored"
        );

        handoffs[handoffId] = HandoffProof({
            receiptHash: receiptHash,
            timestamp: block.timestamp,
            anchoredBy: msg.sender,
            exists: true
        });

        emit HandoffAnchored(
            handoffId,
            receiptHash,
            msg.sender,
            block.timestamp
        );
    }

    function getHandoff(
        uint256 handoffId
    )
        external
        view
        returns (
            bytes32 receiptHash,
            uint256 timestamp,
            address anchoredBy,
            bool exists
        )
    {
        HandoffProof memory proof = handoffs[handoffId];

        return (
            proof.receiptHash,
            proof.timestamp,
            proof.anchoredBy,
            proof.exists
        );
    }
}