[CmdletBinding()]
param(
    [string]$Data = "flow-chart/data.yaml",
    [int]$Epochs = 100,
    [int]$ImageSize = 640,
    [int]$Batch = 8,
    [string]$RunName = "fim-de-semana"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$DataPath = if ([System.IO.Path]::IsPathRooted($Data)) {
    $Data
} else {
    Join-Path $ProjectRoot $Data
}
$RunDirectory = Join-Path $ProjectRoot "runs\flowchart\$RunName"
$Checkpoint = Join-Path $RunDirectory "weights\last.pt"
$LogDirectory = Join-Path $ProjectRoot "logs"
$LogPath = Join-Path $LogDirectory ("treino-{0}.log" -f (Get-Date -Format "yyyy-MM-dd_HH-mm-ss"))

if (-not (Test-Path -LiteralPath $DataPath -PathType Leaf)) {
    throw "Dataset nao encontrado: $DataPath. Crie esse data.yaml antes de iniciar."
}

$Uv = Get-Command uv -ErrorAction SilentlyContinue

Push-Location $ProjectRoot
try {
    $DependenciesReady = $false
    if (Test-Path -LiteralPath $Python -PathType Leaf) {
        & $Python -c "import torch, ultralytics" 2>$null
        $DependenciesReady = $LASTEXITCODE -eq 0
    }

    if ($DependenciesReady) {
        Write-Host "Ambiente YOLO ja esta pronto."
    } else {
        Write-Host "Conferindo o ambiente e instalando o suporte a YOLO..."
        if ($Uv) {
            & $Uv.Source sync --extra ml --extra dev
            $DependenciesReady = $LASTEXITCODE -eq 0
        }
    }

    if (-not $DependenciesReady) {
        Write-Warning "O uv nao concluiu a instalacao; tentando o instalador pip do Python."
        if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
            throw "Python do ambiente virtual nao encontrado: $Python"
        }
        & $Python -m ensurepip --upgrade
        if ($LASTEXITCODE -ne 0) {
            throw "Falha ao habilitar o pip no ambiente virtual."
        }
        & $Python -m pip install --disable-pip-version-check --upgrade -e ".[ml,dev]"
        if ($LASTEXITCODE -ne 0) {
            throw "O uv e o pip falharam ao preparar as dependencias do treinamento."
        }
    }

    if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
        throw "Python do ambiente virtual nao encontrado: $Python"
    }

    New-Item -ItemType Directory -Force -Path $LogDirectory | Out-Null

    if (-not ("WeekendTrainingPower" -as [type])) {
        Add-Type @"
using System;
using System.Runtime.InteropServices;

public static class WeekendTrainingPower
{
    [DllImport("kernel32.dll")]
    public static extern uint SetThreadExecutionState(uint flags);
}
"@
    }

    $ES_CONTINUOUS = [uint32]2147483648
    $ES_SYSTEM_REQUIRED = [uint32]0x00000001
    $PowerState = [WeekendTrainingPower]::SetThreadExecutionState(
        $ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED
    )
    if ($PowerState -eq 0) {
        throw "O Windows recusou o bloqueio temporario da suspensao."
    }

    try {
        $TrainingArgs = @(
            "-u", "treinar.py",
            "--data", $DataPath,
            "--epochs", $Epochs,
            "--imgsz", $ImageSize,
            "--batch", $Batch,
            "--workers", 0,
            "--device", "cpu",
            "--project", (Join-Path $ProjectRoot "runs\flowchart"),
            "--name", $RunName
        )

        if (Test-Path -LiteralPath $Checkpoint -PathType Leaf) {
            Write-Host "Checkpoint encontrado; retomando: $Checkpoint"
            $TrainingArgs += @("--model", $Checkpoint, "--resume")
        } else {
            Write-Host "Iniciando treino novo com yolov8n.pt."
            $TrainingArgs += @("--model", "yolov8n.pt")
        }

        Write-Host "O computador permanecera acordado; a tela pode apagar normalmente."
        Write-Host "Log: $LogPath"
        Write-Host "Bloqueando a sessao em 5 segundos..."
        Start-Sleep -Seconds 5
        rundll32.exe user32.dll,LockWorkStation

        & $Python @TrainingArgs 2>&1 | Tee-Object -FilePath $LogPath
        $TrainingExitCode = $LASTEXITCODE
        if ($TrainingExitCode -ne 0) {
            throw "Treinamento terminou com codigo $TrainingExitCode. Consulte $LogPath"
        }
    }
    finally {
        [WeekendTrainingPower]::SetThreadExecutionState($ES_CONTINUOUS) | Out-Null
    }
}
finally {
    Pop-Location
}
