import hardhatToolboxMochaEthersPlugin from "@nomicfoundation/hardhat-toolbox-mocha-ethers";
import { defineConfig } from "hardhat/config";

export default defineConfig({
plugins: [hardhatToolboxMochaEthersPlugin],

paths: {
sources: "./contracts",
},

solidity: {
profiles: {
default: { version: "0.8.34" },
production: {
version: "0.8.34",
settings: {
optimizer: { enabled: true, runs: 200 },
},
},
},
},

networks: {
localhost: {
type: "http",
chainType: "l1",
url: "http://127.0.0.1:8545",
},
hardhatMainnet: {
type: "edr-simulated",
chainType: "l1",
},
hardhatOp: {
type: "edr-simulated",
chainType: "op",
},
},
});
