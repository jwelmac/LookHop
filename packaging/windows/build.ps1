# Builds dist\LookHop\LookHop.exe and dist\LookHop-<version>-windows-x64.zip
#
#   powershell -ExecutionPolicy Bypass -File packaging\windows\build.ps1
#
# Uses .venv if it exists, otherwise the python on PATH (CI).
$ErrorActionPreference = "Stop"
$Root = Resolve-Path "$PSScriptRoot\..\.."
Set-Location $Root

$Python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
Write-Host "Using $Python"

& $Python -m pip install --quiet -r requirements.txt pyinstaller
if ($LASTEXITCODE) { throw "pip install failed" }

# Bundle the face model so the app works offline from the first run.
& $Python -c "import sys; sys.path.insert(0, '.'); from lookhop import tracker; tracker.MODEL_PATH = tracker.BUNDLED_MODEL; print(tracker.ensure_model())"
if ($LASTEXITCODE) { throw "model download failed" }

& $Python -m PyInstaller --noconfirm --clean --distpath dist --workpath build packaging\windows\LookHop.spec
if ($LASTEXITCODE) { throw "PyInstaller failed" }

# Smoke-test the build: no camera, no windows; writes selftest.txt in the data folder.
$p = Start-Process -FilePath "dist\LookHop\LookHop.exe" -ArgumentList "--selftest" -Wait -PassThru
Get-Content "$env:APPDATA\LookHop\selftest.txt"
if ($p.ExitCode -ne 0) { throw "Selftest failed (exit $($p.ExitCode))" }

$Version = (& $Python -c "import sys; sys.path.insert(0, '.'); import lookhop; print(lookhop.__version__)").Trim()
$Zip = "dist\LookHop-$Version-windows-x64.zip"
if (Test-Path $Zip) { Remove-Item $Zip }
# Antivirus / OneDrive often hold freshly built files for a few seconds.
for ($i = 1; $i -le 6; $i++) {
    try { Compress-Archive -Path "dist\LookHop" -DestinationPath $Zip -ErrorAction Stop; break }
    catch {
        if ($i -eq 6) { throw }
        Write-Host "Files busy, retrying zip ($i)..."
        if (Test-Path $Zip) { Remove-Item $Zip }
        Start-Sleep -Seconds 5
    }
}
$size = [math]::Round((Get-Item $Zip).Length / 1MB, 1)
Write-Host "Built $Zip ($size MB)"
