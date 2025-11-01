#Requires -Version 5.0
$ErrorActionPreference = "Stop"
Write-Host "[gd] Timesheets grouping — applying"
Copy-Item -Force .\timesheets_enhance.css .\timesheets_enhance.css
Copy-Item -Force .\timesheets_enhance.js .\timesheets_enhance.js
if (Test-Path .\timesheets.html) {
  $html = Get-Content .\timesheets.html -Raw
  if ($html -notmatch "timesheets_enhance.js") {
    $html = $html -replace "</head>", "  <link rel=\"stylesheet\" href=\"/timesheets_enhance.css\" />`n</head>"
    $html = $html -replace "</body>", "  <script src=\"/timesheets_enhance.js\"></script>`n</body>"
    Set-Content -Path .\timesheets.html -Value $html -Encoding UTF8
    Write-Host " - tags injected"
  } else {
    Write-Host " - scripts already present"
  }
} else {
  Write-Host " ! timesheets.html not found in current directory"
}
Write-Host "[gd] Done"
