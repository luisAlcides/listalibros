<#
.SYNOPSIS
  Obtiene un token (si hace falta) y crea un libro vía POST /api/books/.

.EXAMPLE
  .\add-book-from-outside.ps1 -BaseUrl "http://127.0.0.1:8000" -Username "demo" -Password "demo" `
    -Title "El nombre del viento" -Author "Patrick Rothfuss" -TotalPages 662

.EXAMPLE
  $env:BOOKTRACKER_TOKEN = "abc123..."
  .\add-book-from-outside.ps1 -BaseUrl "https://tu-app.railway.app" -Title "..." -Author "..." -TotalPages 100
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $BaseUrl,

    [string] $Username,
    [string] $Password,

    [string] $Token = $env:BOOKTRACKER_TOKEN,

    [Parameter(Mandatory = $true)]
    [string] $Title,

    [Parameter(Mandatory = $true)]
    [string] $Author,

    [Parameter(Mandatory = $true)]
    [int] $TotalPages,

    [Nullable[int]] $CategoryId = $null,
    [string] $Status = "PENDING",
    [string] $CoverUrl = ""
)

$BaseUrl = $BaseUrl.TrimEnd('/')

function Get-ApiToken {
    param([string] $User, [string] $Pass)
    $body = (@{ username = $User; password = $Pass } | ConvertTo-Json)
    $r = Invoke-RestMethod -Uri "$BaseUrl/api/auth/token/" -Method Post -Body $body `
        -ContentType "application/json; charset=utf-8" -ErrorAction Stop
    if (-not $r.token) { throw "La API no devolvió token." }
    return $r.token
}

if (-not $Token) {
    if (-not $Username -or -not $Password) {
        throw "Indica -Token, o define `$env:BOOKTRACKER_TOKEN, o pasa -Username y -Password para obtener token."
    }
    $Token = Get-ApiToken -User $Username -Pass $Password
    Write-Host "Token obtenido (guárdalo en `$env:BOOKTRACKER_TOKEN si quieres reutilizarlo)." -ForegroundColor DarkGray
}

$payload = [ordered]@{
    title        = $Title
    author       = $Author
    total_pages  = $TotalPages
    status       = $Status
}
if ($null -ne $CategoryId) { $payload.category = $CategoryId }
if ($CoverUrl) { $payload.cover_url = $CoverUrl }

$headers = @{ Authorization = "Token $Token" }
$json = $payload | ConvertTo-Json

$created = Invoke-RestMethod -Uri "$BaseUrl/api/books/" -Method Post -Body $json `
    -Headers $headers -ContentType "application/json; charset=utf-8" -ErrorAction Stop

Write-Host "Libro creado: id=$($created.id) — $($created.title)" -ForegroundColor Green
$created
