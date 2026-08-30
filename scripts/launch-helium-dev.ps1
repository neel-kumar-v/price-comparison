#!/usr/bin/env pwsh
# Launch Helium with CDP on port 9222 (required for agent-browser price scraping).

Write-Host "Searching for Helium installation..." -ForegroundColor Cyan

$heliumExe = $null

# 1. If Helium is currently open, grab its exact running path
$runningProc = Get-Process -Name "helium", "chrome" -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*helium*" } | Select-Object -First 1
if ($runningProc -and $runningProc.Path) {
    $heliumExe = $runningProc.Path
}

# 2. Check Windows Start Menu shortcuts (.lnk files)
if (-not $heliumExe) {
    $shortcutDirs = @(
        "$env:APPDATA\Microsoft\Windows\Start Menu\Programs",
        "$env:ALLUSERSPROFILE\Microsoft\Windows\Start Menu\Programs",
        "$env:USERPROFILE\Desktop"
    )

    $wscript = New-Object -ComObject WScript.Shell
    foreach ($dir in $shortcutDirs) {
        if (Test-Path $dir) {
            $shortcuts = Get-ChildItem -Path $dir -Recurse -Filter "*helium*.lnk" -ErrorAction SilentlyContinue
            foreach ($lnk in $shortcuts) {
                $target = $wscript.CreateShortcut($lnk.FullName).TargetPath
                if ($target -and (Test-Path $target)) {
                    $heliumExe = $target
                    break
                }
            }
        }
        if ($heliumExe) { break }
    }
}

# 3. Check common AppData / local installation directories
if (-not $heliumExe) {
    $searches = @(
        "$env:LOCALAPPDATA\imputnet\*\*.exe",
        "$env:LOCALAPPDATA\helium\*\*.exe",
        "$env:PROGRAMFILES\*\helium*.exe"
    )
    foreach ($pattern in $searches) {
        $found = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) {
            $heliumExe = $found.FullName
            break
        }
    }
}

# Output result
if (-not $heliumExe) {
    Write-Host "`nCould not automatically locate Helium.exe." -ForegroundColor Red
    Write-Host "To find it manually:" -ForegroundColor Yellow
    Write-Host "1. Open Helium normally." -ForegroundColor Gray
    Write-Host "2. Open Task Manager (Ctrl + Shift + Esc) -> expand Helium -> Right-click -> Open file location." -ForegroundColor Gray
    Write-Host "3. Paste that full path into this script." -ForegroundColor Gray
    exit 1
}

Write-Host "Located executable at: $heliumExe" -ForegroundColor Green
Write-Host "Starting Helium with --remote-debugging-port=9222..." -ForegroundColor Cyan

Start-Process -FilePath $heliumExe -ArgumentList "--remote-debugging-port=9222"
Write-Host "Helium is now running with CDP enabled on port 9222." -ForegroundColor DarkGray