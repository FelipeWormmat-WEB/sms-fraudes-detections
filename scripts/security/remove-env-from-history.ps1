[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

function Fail {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    Write-Error $Message
    exit 1
}

$repoRoot = (& git rev-parse --show-toplevel 2>$null)
if (-not $repoRoot) {
    Fail "Execute este script dentro de um repositorio Git."
}

Set-Location -LiteralPath $repoRoot

$trackedEnvPaths = @(
    ".env",
    "frontend/.env",
    "llm-service/.env"
)

$historyHitCount = (& git rev-list --all --count -- $trackedEnvPaths 2>$null)
if (-not $historyHitCount -or $historyHitCount -eq "0") {
    Write-Host "Nenhum commit com arquivos .env rastreados foi encontrado no historico. Nada para limpar."
    exit 0
}

$workingTreeStatus = (& git status --porcelain=v1)
if ($workingTreeStatus) {
    Write-Warning "O repositorio esta com alteracoes locais."
    Write-Host "Para proteger seu trabalho atual, a limpeza do historico foi bloqueada."
    Write-Host "Commit, stash ou mova as mudancas para uma branch segura antes de rodar este script."
    exit 1
}

& git filter-repo --version *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Warning "git-filter-repo nao esta instalado neste ambiente."
    Write-Host "Instale a ferramenta e rode novamente este script."
    Write-Host "Referencia: https://github.com/newren/git-filter-repo"
    exit 1
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupBranch = "backup/pre-env-history-cleanup-$timestamp"
$backupTag = "backup/pre-env-history-cleanup-$timestamp"

Write-Host "Foi encontrado '.env' em $historyHitCount commit(s)."
Write-Host "Arquivos que serao removidos do historico:"
foreach ($path in $trackedEnvPaths) {
    Write-Host "  - $path"
}
Write-Host "Backup local que sera criado antes da limpeza:"
Write-Host "  branch: $backupBranch"
Write-Host "  tag:    $backupTag"
Write-Host ""

$confirmation = Read-Host "Reescrever o historico local para remover os arquivos .env rastreados de todos os commits? [y/N]"
if ($confirmation -notmatch '^(?i:y|yes)$') {
    Write-Host "Operacao cancelada. Nenhuma alteracao foi feita."
    exit 0
}

& git branch $backupBranch
if ($LASTEXITCODE -ne 0) {
    Fail "Nao foi possivel criar a branch de backup '$backupBranch'."
}

& git tag $backupTag
if ($LASTEXITCODE -ne 0) {
    Fail "Nao foi possivel criar a tag de backup '$backupTag'."
}

& git filter-repo --path .env --path frontend/.env --path llm-service/.env --invert-paths --force
if ($LASTEXITCODE -ne 0) {
    Fail "A limpeza do historico falhou. Use os backups criados para recuperar o estado anterior."
}

Write-Host ""
Write-Host "Historico local reescrito com sucesso."
Write-Host "Backups criados:"
Write-Host "  $backupBranch"
Write-Host "  $backupTag"
Write-Host ""
Write-Host "Proximos passos obrigatorios:"
Write-Host "1. Rotacione todas as secrets que ja estiveram nos arquivos .env (API keys, database, tokens)."
Write-Host "2. Revise o historico reescrito localmente antes de publicar."
Write-Host "3. So depois disso, force-push conscientemente:"
Write-Host "   git push origin --force --all"
Write-Host "   git push origin --force --tags"
Write-Host "4. Avise qualquer colaborador para re-clonar ou resetar as branches apos a limpeza."
