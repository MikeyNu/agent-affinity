# Windows read-only Affinity by Canva package and process discovery.
# Run via authorized Desktop Commander on Windows, not in an unrelated sandbox.
$ErrorActionPreference = 'Stop'
$result = [ordered]@{
    platform = 'Windows'
    machine = $env:COMPUTERNAME
    packages = @()
    processes = @()
    programDirectories = @()
    status = 'discovery_only'
    guiControlVerified = $false
    nativeScriptingVerified = $false
}
try {
    $result.packages = @(Get-AppxPackage | Where-Object { $_.Name -match 'Affinity' } |
        Select-Object Name, Version, InstallLocation)
} catch {
    $result.packageQueryError = $_.Exception.Message
}
try {
    $result.processes = @(Get-Process | Where-Object { $_.ProcessName -match 'Affinity' } |
        Select-Object ProcessName, Id, Path)
} catch {
    $result.processQueryError = $_.Exception.Message
}
foreach ($path in @('C:\Program Files', 'C:\Program Files (x86)', $env:LOCALAPPDATA)) {
    if ($path -and (Test-Path -LiteralPath $path)) {
        $result.programDirectories += @(Get-ChildItem -LiteralPath $path -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match 'Affinity' } | Select-Object -ExpandProperty FullName)
    }
}
$result | ConvertTo-Json -Depth 5
