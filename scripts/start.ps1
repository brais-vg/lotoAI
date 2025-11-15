param()
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

docker compose -f infra/docker/docker-compose.yml --profile core --profile app up -d
