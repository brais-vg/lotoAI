param()
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Write-Error "Docker no está instalado o en PATH"; exit 1
}

Write-Host "Construyendo y levantando perfiles core+app..."
docker compose -f infra/docker/docker-compose.yml --profile core --profile app up -d --build
Write-Host "Servicios levantados. Web: http://localhost:3000, Gateway: http://localhost:8088"
