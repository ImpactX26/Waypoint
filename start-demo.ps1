# HandoffChain Demo Startup
# Starts Hardhat, deploys the smart contract,
# then starts FastAPI and React.

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "          HANDOFFCHAIN DEMO" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------
# 1. START HARDHAT BLOCKCHAIN
# ---------------------------------------------------------

Write-Host "Starting Hardhat blockchain..." -ForegroundColor Yellow

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$projectRoot\blockchain'; npx hardhat node"
)

# Give Hardhat time to start
Start-Sleep -Seconds 5

# ---------------------------------------------------------
# 2. DEPLOY SMART CONTRACT
# ---------------------------------------------------------

Write-Host "Deploying HandoffRegistry..." -ForegroundColor Yellow

Push-Location "$projectRoot\blockchain"

npx hardhat run scripts/deploy.ts --network localhost

$deployExitCode = $LASTEXITCODE

Pop-Location

if ($deployExitCode -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Smart contract deployment failed." -ForegroundColor Red
    Write-Host "Check the Hardhat window before continuing." -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}

Write-Host "Smart contract deployed successfully." -ForegroundColor Green

# ---------------------------------------------------------
# 3. START FASTAPI BACKEND
# ---------------------------------------------------------

Write-Host "Starting FastAPI backend..." -ForegroundColor Yellow

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$projectRoot'; .\.venv\Scripts\Activate.ps1; uvicorn main:app --reload"
)

Start-Sleep -Seconds 3

# ---------------------------------------------------------
# 4. START REACT FRONTEND
# ---------------------------------------------------------

Write-Host "Starting React frontend..." -ForegroundColor Yellow

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$projectRoot\frontend'; npm run dev"
)

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "       HANDOFFCHAIN IS STARTING" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend:  http://localhost:5173" -ForegroundColor Green
Write-Host "Backend:   http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Blockchain: http://127.0.0.1:8545" -ForegroundColor Green
Write-Host ""
Write-Host "CREATE -> SIGN -> ACCEPT -> ANCHOR -> VERIFY" -ForegroundColor Cyan
Write-Host ""