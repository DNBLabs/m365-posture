<#
.SYNOPSIS
    Creates a self-signed certificate for Entra ID app-only authentication in a homelab.

.DESCRIPTION
    Generates graph-app.pfx (private key) and graph-app.cer (public) under ./certs/.
    Upload the .cer to App registration > Certificates; set GRAPH_CERT_PATH to the PFX
    path for local runs. Uses a passwordless PFX suitable for lab use only.

.NOTES
    Run from PowerShell; requires permission to write to Cert:\CurrentUser\My and ./certs/.
#>

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

$base = Join-Path $repoRoot "certs"
New-Item -ItemType Directory -Force -Path $base | Out-Null

$cert = New-SelfSignedCertificate `
    -Subject "CN=m365-posture-homelab" `
    -CertStoreLocation "Cert:\CurrentUser\My" `
    -KeyExportPolicy Exportable `
    -KeySpec KeyExchange `
    -KeyLength 2048 `
    -HashAlgorithm SHA256 `
    -NotAfter (Get-Date).AddYears(2)

$thumb = $cert.Thumbprint
$pfxPath = Join-Path $base "graph-app.pfx"
$cerPath = Join-Path $base "graph-app.cer"

# Homelab-only: empty SecureString yields an exportable passwordless PFX.
$pwd = New-Object System.Security.SecureString
Export-PfxCertificate `
    -Cert "Cert:\CurrentUser\My\$thumb" `
    -FilePath $pfxPath `
    -Password $pwd | Out-Null

Export-Certificate `
    -Cert "Cert:\CurrentUser\My\$thumb" `
    -FilePath $cerPath | Out-Null

Write-Host "Created:"
Write-Host "  PFX (private): $pfxPath"
Write-Host "  CER (public):  $cerPath"
Write-Host "  Thumbprint:    $thumb"
Write-Host ""
Write-Host "Next: Upload graph-app.cer to Entra app registration > Certificates."
Write-Host "Then set GRAPH_CERT_PATH to the PFX path (after you move it, update the path)."
