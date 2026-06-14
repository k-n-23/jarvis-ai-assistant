# Jarvis setup script for Windows
# Run with: powershell -ExecutionPolicy Bypass -File setup.ps1

Write-Host "== Jarvis Setup ==" -ForegroundColor Cyan

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python not found. Install from https://python.org" -ForegroundColor Red
    exit 1
}
$ver = python --version
Write-Host "Found: $ver" -ForegroundColor Green

# Install dependencies
Write-Host "`nInstalling Python packages..." -ForegroundColor Cyan
pip install -r requirements.txt

# Check if PyAudio failed (common on Windows)
$pyaudio = python -c "import pyaudio; print('ok')" 2>$null
if ($pyaudio -ne "ok") {
    Write-Host "`nPyAudio install may have failed. Trying pipwin fallback..." -ForegroundColor Yellow
    pip install pipwin
    pipwin install pyaudio
}

# Prompt for API keys
Write-Host "`n== API Key Setup ==" -ForegroundColor Cyan
Write-Host "You need an Anthropic API key from https://console.anthropic.com"
$apiKey = Read-Host "Enter your ANTHROPIC_API_KEY (or press Enter to skip)"
if ($apiKey) {
    [System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", $apiKey, "User")
    Write-Host "ANTHROPIC_API_KEY saved to user environment." -ForegroundColor Green
}

Write-Host "`n(Optional) OpenWeatherMap key from https://openweathermap.org/api"
$weatherKey = Read-Host "Enter your WEATHER_API_KEY (or press Enter to skip)"
if ($weatherKey) {
    [System.Environment]::SetEnvironmentVariable("WEATHER_API_KEY", $weatherKey, "User")
    Write-Host "WEATHER_API_KEY saved to user environment." -ForegroundColor Green
}

$city = Read-Host "Your default city for weather (e.g. London, Mumbai) [default: New York]"
if ($city) {
    [System.Environment]::SetEnvironmentVariable("JARVIS_CITY", $city, "User")
} else {
    [System.Environment]::SetEnvironmentVariable("JARVIS_CITY", "New York", "User")
}

Write-Host "`n== Setup complete! ==" -ForegroundColor Green
Write-Host "Run Jarvis with:  python jarvis.py" -ForegroundColor Cyan
Write-Host "(Restart your terminal first so the env vars take effect)" -ForegroundColor Yellow
