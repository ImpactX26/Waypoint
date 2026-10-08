import { network } from "hardhat";

async function main() {
  const { ethers } = await network.connect();

  const handoffRegistry = await ethers.deployContract("HandoffRegistry");

  await handoffRegistry.waitForDeployment();

  const contractAddress = await handoffRegistry.getAddress();

  console.log("HandoffRegistry deployed to:", contractAddress);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});