[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$DriveLetter,
    [ValidateSet('step1_payload', 'step2_hotfix', 'step3_dashboard')]
    [string]$Action = 'step1_payload'
)

$toolsDir = $PSScriptRoot
$payloadDir = Join-Path $toolsDir "LanguageBreak"
$hotfixFile = Join-Path $toolsDir "Update_hotfix_languagebreak-zh-Hans-CN.bin"
$clientDir = Join-Path (Split-Path -Parent $PSScriptRoot) "client"

# Find Kindle Drive if not specified
if (-not $DriveLetter) {
    $volumes = Get-Volume | Where-Object { $_.DriveType -eq 'Removable' -or ($_.FileSystemLabel -match 'Kindle' -or (Test-Path "$($_.DriveLetter):\documents")) }
    if ($volumes) {
        $DriveLetter = $volumes[0].DriveLetter + ":"
    } else {
        # Prompt or fallback
        $DriveLetter = Read-Host "请输入 Kindle 在电脑上显示的盘符 (例如 E: 或 F:)"
        if ($DriveLetter -notmatch ':$') { $DriveLetter += ":" }
    }
}

if (-not (Test-Path $DriveLetter)) {
    Write-Error "找不到盘符 $DriveLetter，请确认 Kindle 已通过数据线连接到电脑！"
    exit 1
}

Write-Host "检测到 Kindle 盘符: $DriveLetter" -ForegroundColor Green

if ($Action -eq 'step1_payload') {
    Write-Host "正在写入 LanguageBreak 越狱漏洞引导文件到 $DriveLetter ..." -ForegroundColor Cyan
    Copy-Item -Path "$payloadDir\*" -Destination $DriveLetter -Recurse -Force
    Write-Host " [成功] 漏洞文件已写入！请按照指引在 Kindle 屏幕上继续操作。" -ForegroundColor Green
}
elseif ($Action -eq 'step2_hotfix') {
    Write-Host "正在写入防升级与固化补丁 Hotfix 到 $DriveLetter 根目录..." -ForegroundColor Cyan
    Copy-Item -Path $hotfixFile -Destination (Join-Path $DriveLetter "Update_hotfix_languagebreak-zh-Hans-CN.bin") -Force
    Write-Host " [成功] Hotfix 补丁已写入！请在 Kindle 设置中点击 '更新您的 Kindle'。" -ForegroundColor Green
}
elseif ($Action -eq 'step3_dashboard') {
    Write-Host "正在安装 Kindle 看板系统脚本与 KUAL 插件到 $DriveLetter ..." -ForegroundColor Cyan
    Copy-Item -Path "$clientDir\*" -Destination $DriveLetter -Recurse -Force
    Write-Host " [成功] 看板系统已部署完毕！" -ForegroundColor Green
}
