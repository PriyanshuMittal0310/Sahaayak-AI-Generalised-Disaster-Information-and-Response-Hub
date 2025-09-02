# Function to check if a port is in use
function Test-PortInUse {
    param([int]$port)
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse("127.0.0.1"), $port)
        $listener.Start()
        $listener.Stop()
        return $false
    } catch {
        return $true
    }
}

# Check if required ports are available
$portsInUse = @()
if (Test-PortInUse -port 8000) { $portsInUse += 8000 }
if (Test-PortInUse -port 3000) { $portsInUse += 3000 }

if ($portsInUse.Count -gt 0) {
    Write-Host "Error: The following ports are already in use: $($portsInUse -join ', ')" -ForegroundColor Red
    Write-Host "Please close any applications using these ports and try again." -ForegroundColor Yellow
    exit 1
}

# Install frontend dependencies
Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
Set-Location frontend
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error installing frontend dependencies. See above for details." -ForegroundColor Red
    exit 1
}
Set-Location ..

# Start backend server
Write-Host "Starting backend server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m pip install -r requirements.txt; python -m uvicorn main:app --reload"

# Wait a moment for backend to start
Start-Sleep -Seconds 5

# Start frontend server
Write-Host "Starting frontend development server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm start"

# Display helpful information
Write-Host "`nServers are starting up..." -ForegroundColor Green
Write-Host "- Backend API: http://localhost:8000"
Write-Host "- API Documentation: http://localhost:8000/docs"
Write-Host "- Frontend: http://localhost:3000`n"

Write-Host "Note: The frontend may take a few minutes to start up for the first time." -ForegroundColor Yellow
Write-Host "      Please wait for the browser to open automatically." -ForegroundColor Yellow
