# 408 真题数据下载脚本
# 用法: powershell -File download_408.ps1 [-Years 2009,2026] [-Token "xxx"]
# 下载: 1) 各年题目元数据 API -> data\raw\{year}.api.json
#       2) 三类静态页 -> html\{questions|answers|analysis}\{year}\{n}.html
#       3) 共享样式与知识点树
param(
    [int[]]$Years = @(2009..2026),
    [string]$Token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJsb2dpblR5cGUiOiJsb2dpbiIsImxvZ2luSWQiOiJ6dF91c2VyOjIxMTI3NjM0NTA3OTA1MzUxNjkiLCJyblN0ciI6Ik05SlFlSUdvS3JheWJFbUlEY2hPOVh1b1VYanlzS2ZKIiwiY2xpZW50aWQiOiI4MTgwMWRiZDdkM2U0YmY0NmRiOGY0OWUzYWQ2MzNjNyIsInVzZXJJZCI6MjExMjc2MzQ1MDc5MDUzNTE2OSwidXNlck5hbWUiOiI2MjU2NDk5NzhAcXEuY29tIn0.VLO2t1LrTjg-03y9SFZe4VE2N9Uqt253d-74B4QOW6E",
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$Base = 'https://www.408os.cn'
$DataRaw = Join-Path $Root 'data\raw'
$HtmlDir = Join-Path $Root 'html'
New-Item -ItemType Directory -Force -Path $DataRaw | Out-Null
foreach ($d in @('questions','answers','analysis')) {
    New-Item -ItemType Directory -Force -Path (Join-Path $HtmlDir $d) | Out-Null
}

function Invoke-Download {
    param([string]$Url, [string]$OutFile, [hashtable]$Headers = @{})
    if ((Test-Path $OutFile) -and (Get-Item $OutFile).Length -gt 200) { return $true }  # 已存在且非空则跳过（增量）
    $tmp = "$OutFile.tmp"
    for ($i = 1; $i -le 3; $i++) {
        $args = @('curl.exe','-s','--max-time','30','-o', $tmp, '-w', '%{http_code}')
        foreach ($k in $Headers.Keys) { $args += @('-H', "$k`: $($Headers[$k])") }
        $args += $Url
        $code = & $args[0] $args[1..($args.Length-1)]
        if ($code -eq '200' -and (Test-Path $tmp) -and (Get-Item $tmp).Length -gt 100) {
            Move-Item $tmp $OutFile -Force
            Start-Sleep -Milliseconds 200
            return $true
        }
        Start-Sleep -Milliseconds (500 * $i)
    }
    if (Test-Path $tmp) { Remove-Item $tmp -Force }
    return $false
}

# ---- 1. 共享资源 ----
$cssDir = Join-Path $HtmlDir 'css'
New-Item -ItemType Directory -Force -Path $cssDir | Out-Null
Invoke-Download "$Base/css/style.css" (Join-Path $cssDir 'style.css') | Out-Null
Invoke-Download "$Base/assets/knowledge-B2Ol7M-Z.js" (Join-Path $DataRaw 'knowledge.js') | Out-Null
Write-Host "[OK] css + knowledge.js"

# ---- 2. 元数据 API + 静态页清单 ----
$manifest = @()
foreach ($y in $Years) {
    $apiFile = Join-Path $DataRaw "$y.api.json"
    $ok = Invoke-Download "$Base/api/zt/question/list-with-details?year=$y&questionType=all" $apiFile @{Authorization = "Bearer $Token"}
    if (-not $ok) { Write-Host "[FAIL] API $y"; continue }
    $json = Get-Content $apiFile -Raw -Encoding UTF8 | ConvertFrom-Json
    $qs = $json.data | ForEach-Object { $_.question }
    Write-Host ("[OK] API {0}: {1} 题" -f $y, $qs.Count)
    foreach ($q in $qs) {
        $n = $q.questionIndex
        $manifest += [pscustomobject]@{
            year = $y; index = $n
            questions = "$Base/static/questions/$y/$n.html"
            answers   = "$Base/static/answers/$y/$n.html"
            analysis  = "$Base/static/analysis/$y/$n.html"
        }
    }
}
$manifest | ConvertTo-Json -Depth 3 | Set-Content (Join-Path $DataRaw 'manifest.json') -Encoding UTF8
Write-Host ("清单共 {0} 题" -f $manifest.Count)

# ---- 3. 下载三类静态页（并行，2 线程温和模式，防限流）----
$fail = New-Object System.Collections.Generic.List[string]
$jobs = @()
foreach ($m in $manifest) {
    foreach ($type in @('questions','answers','analysis')) {
        $url = $m.$type
        $out = Join-Path $HtmlDir "$type\$($m.year)\$($m.index).html"
        if ((Test-Path $out) -and (Get-Item $out).Length -gt 200) { continue }
        $jobs += [pscustomobject]@{ url = $url; out = $out }
    }
}
Write-Host ("待下载 {0} 个页面，2 线程并行..." -f $jobs.Count)
$done = 0
$jobs | ForEach-Object -Parallel {
    $j = $_
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $j.out) | Out-Null
    $tmp = "$($j.out).tmp"
    for ($i = 1; $i -le 3; $i++) {
        $code = curl.exe -s --max-time 30 -o $tmp -w '%{http_code}' $j.url
        if ($code -eq '200' -and (Test-Path $tmp) -and (Get-Item $tmp).Length -gt 100) {
            Move-Item $tmp $j.out -Force
            Start-Sleep -Milliseconds 300
            break
        }
        if ($code -eq '000') { Start-Sleep -Seconds 30 }  # 被限流则长等
        Start-Sleep -Milliseconds (500 * $i)
    }
    if (Test-Path $tmp) { Remove-Item $tmp -Force }
    if (-not (Test-Path $j.out) -or (Get-Item $j.out).Length -le 200) { "$($j.url)" }
} -ThrottleLimit 2 | ForEach-Object {
    $done++
    if ($done % 50 -eq 0) { Write-Host ("  进度 {0}/{1}" -f $done, $jobs.Count) }
    $fail.Add($_)
}

# ---- 4. 补抓一轮 ----
if ($fail.Count -gt 0) {
    Write-Host ("首轮失败 {0} 个，补抓..." -f $fail.Count)
    $fail2 = New-Object System.Collections.Generic.List[string]
    foreach ($url in $fail) {
        $rel = $url -replace [regex]::Escape("$Base/static/"), ''
        $parts = $rel -split '/'
        $out = Join-Path $HtmlDir "$($parts[0])\$($parts[1])\$($parts[2])"
        if (-not (Invoke-Download $url $out)) { $fail2.Add($url) }
    }
    $fail = $fail2
}

if ($fail.Count -gt 0) { Write-Host "[最终失败]"; $fail | ForEach-Object { "  $_" } }
else { Write-Host "[DONE] 全部下载成功" }

# ---- 5. 完整性扫描 ----
$empty = Get-ChildItem -Recurse (Join-Path $HtmlDir 'questions'), (Join-Path $HtmlDir 'answers'), (Join-Path $HtmlDir 'analysis') -Filter *.html | Where-Object { $_.Length -lt 200 }
Write-Host ("文件统计: questions={0} answers={1} analysis={2} 空文件={3}" -f `
    (Get-ChildItem -Recurse (Join-Path $HtmlDir 'questions') -Filter *.html).Count, `
    (Get-ChildItem -Recurse (Join-Path $HtmlDir 'answers') -Filter *.html).Count, `
    (Get-ChildItem -Recurse (Join-Path $HtmlDir 'analysis') -Filter *.html).Count, `
    $empty.Count)
