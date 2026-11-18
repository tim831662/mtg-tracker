$ErrorActionPreference = "Stop"

function Invoke-SetupCommand {
    param (
        [string]$Command,
        [string[]]$Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Command failed with exit code $LASTEXITCODE. Fix the error above and run setup again."
    }
}

Push-Location $PSScriptRoot
try {
    foreach ($command in @("uv", "npm.cmd", "docker")) {
        if (!(Get-Command $command -ErrorAction SilentlyContinue)) {
            throw "Missing $command. Install the requirements listed in README.md, then reopen PowerShell."
        }
    }

    Write-Host "Checking Docker Desktop..."
    Invoke-SetupCommand "docker" @("info", "--format", "{{.ServerVersion}}")

    if (!(Test-Path -LiteralPath ".env")) {
        Copy-Item -LiteralPath ".env.example" -Destination ".env"
    }

    Write-Host "Installing Python dependencies..."
    Invoke-SetupCommand "uv" @("sync", "--locked", "--extra", "dev")

    Write-Host "Installing frontend dependencies..."
    Invoke-SetupCommand "npm.cmd" @("--prefix", "frontend", "ci")

    Write-Host "Starting PostgreSQL and waiting for it to be ready..."
    Invoke-SetupCommand "docker" @("compose", "up", "-d", "--wait", "--wait-timeout", "90", "db")

    Write-Host "Updating database tables..."
    Invoke-SetupCommand "uv" @("run", "alembic", "upgrade", "head")

    Write-Host "Loading sample tournaments and decks..."
    Invoke-SetupCommand "uv" @(
        "run", "python", "-m", "mtg_tracker.importers.tournaments",
        "database/seeds/sample_tournament_data.json"
    )

    Write-Host "Setup complete. Follow 'Run the app' in README.md to start the two servers."
}
catch {
    Write-Host "Setup stopped. $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
finally {
    Pop-Location
}
