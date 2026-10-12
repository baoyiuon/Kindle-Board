# High-Speed Auto Watcher for LanguageBreak Step 14
$source = Join-Path $PSScriptRoot "LanguageBreak"
$target = "H:\"

Write-Host "Auto watcher started, monitoring H:\ every 100ms..." -ForegroundColor Cyan
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$copied = $false

while ($sw.Elapsed.TotalMinutes -lt 15) {
    if (Test-Path $target) {
        try {
            Write-Host "Drive H:\ detected! Injecting payload files..." -ForegroundColor Green
            Copy-Item -Path "$source\*" -Destination $target -Recurse -Force
            [System.IO.File]::WriteAllText("$target\.injected_timestamp", (Get-Date).ToString("o"))
            Write-Host "Payload injected successfully in $($sw.ElapsedMilliseconds) ms!" -ForegroundColor Green
            try { [Console]::Beep(1200, 300) } catch {}
            $copied = $true
            break
        } catch {
            Write-Host "Copy retry: $_" -ForegroundColor Yellow
        }
    }
    Start-Sleep -Milliseconds 100
}

if (-not $copied) {
    Write-Host "Watcher timed out." -ForegroundColor Red
}
