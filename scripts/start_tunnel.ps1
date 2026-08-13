# =============================================================================
# start_tunnel.ps1 — Cloudflare Quick Tunnel 자동 시작 + 로그 파일 기반 URL 감지 및 갱신
# =============================================================================

# 스크립트 실행 위치 기준으로 무조건 부모 폴더(프로젝트 루트)로 작업 디렉토리를 강제 고정합니다.
# 이로써 한글 폴더명 인코딩 문제 및 작업 디렉토리 이탈 문제를 100% 원천 예방합니다.
if ($PSScriptRoot) {
    Set-Location "$PSScriptRoot\.."
}

$EnvProd   = ".\frontend\.env.production"
$CFExe     = ".\cloudflared.exe"
$LogFile   = "$env:TEMP\cf_tunnel.log"

# 기존 로그 파일 삭제
if (Test-Path $LogFile) {
    Remove-Item $LogFile -Force -ErrorAction SilentlyContinue
}

Write-Host "[Tunnel] Cloudflare Quick Tunnel 시작 중..." -ForegroundColor Cyan

# cloudflared 실행 (stderr를 임시 로그 파일로 리다이렉트)
$Arguments = @("tunnel", "--url", "http://localhost:8000")
$Proc = Start-Process -FilePath $CFExe -ArgumentList $Arguments -RedirectStandardError $LogFile -NoNewWindow -PassThru

$tunnelUrl = $null
$urlPattern = 'https://[a-z0-9\-]+\.trycloudflare\.com'
$timeout = [System.DateTime]::Now.AddSeconds(20)

Write-Host "[Tunnel] URL 감지 대기 중 (최대 20초)..." -ForegroundColor Yellow

# 로그 파일에서 trycloudflare URL이 검출될 때까지 폴링
while ($Proc -and -not $Proc.HasExited -and [System.DateTime]::Now -lt $timeout) {
    if (Test-Path $LogFile) {
        $content = Get-Content $LogFile -ErrorAction SilentlyContinue
        $match = ($content | Select-String $urlPattern)
        if ($match) {
            # 첫 번째 매칭되는 URL 추출
            if ($match.Line -match $urlPattern) {
                $tunnelUrl = $Matches[0]
                break
            }
        }
    }
    Start-Sleep -Seconds 1
}

if ($tunnelUrl) {
    $apiUrl = "$tunnelUrl/api"
    Write-Host "`n[Tunnel] ✅ 터널 URL 감지 성공: $apiUrl" -ForegroundColor Green

    # .env.production 파일 쓰기 (기존 내용 덮어씀)
    Set-Content -Path $EnvProd -Value "NEXT_PUBLIC_API_URL=$apiUrl" -Encoding UTF8
    Write-Host "[Tunnel] .env.production 업데이트 완료" -ForegroundColor Green

    Write-Host "`n  ┌─────────────────────────────────────────────────────────┐"
    Write-Host "  │  🌐 외부 접속 API URL:                                   │"
    Write-Host "  │  $apiUrl"
    Write-Host "  └─────────────────────────────────────────────────────────┘`n"
} else {
    Write-Host "[Tunnel] ⚠️ URL 감지 실패 또는 cloudflared 실행 실패." -ForegroundColor Red
}

# 터널 프로세스가 활성 상태인 동안 실시간으로 로그를 화면에 출력하며 유지
Write-Host "[Tunnel] 터널 로그 모니터링 중... (종료하려면 이 창을 닫거나 Ctrl+C)" -ForegroundColor Gray
$lastLineCount = 0
while ($Proc -and -not $Proc.HasExited) {
    if (Test-Path $LogFile) {
        $content = Get-Content $LogFile -ErrorAction SilentlyContinue
        $lineCount = $content.Count
        if ($lineCount -gt $lastLineCount) {
            $content[$lastLineCount..($lineCount-1)] | ForEach-Object {
                Write-Host "[cfLog] $_" -ForegroundColor DarkGray
            }
            $lastLineCount = $lineCount
        }
    }
    Start-Sleep -Milliseconds 500
}

Write-Host "[Tunnel] 터널 프로세스가 종료되었습니다." -ForegroundColor Red
