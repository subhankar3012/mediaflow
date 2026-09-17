# Windows Task Scheduler Registration for Media Downloader Supabase Keep-Alive
# Run this script in PowerShell to schedule an hourly health check.

$ErrorActionPreference = "Stop"

$TaskName = "MediaDownloader_SupabaseKeepAlive"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Split-Path -Parent $ScriptDir
$PythonExe = Join-Path $BackendDir ".venv\Scripts\python.exe"
$KeepAliveScript = Join-Path $ScriptDir "keep_alive.py"

if (-not (Test-Path $PythonExe)) {
    $PythonExe = (Get-Command python).Source
}

Write-Host "Configuring Scheduled Task: $TaskName"
Write-Host "Python Executable: $PythonExe"
Write-Host "Script: $KeepAliveScript"

# Define the action: run keep_alive.py --once
$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "`"$KeepAliveScript`" --once" `
    -WorkingDirectory $BackendDir

# Define the trigger: Repeat once every hour indefinitely
$Trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Hours 1)

# Settings: prevent overlapping runs, kill if exceeds 5 minutes
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

# Register or update task
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Hourly keep-alive ping to Media Downloader Engine health check to keep Supabase Free Plan active."

Write-Host "Successfully registered scheduled task '$TaskName'."
Write-Host "Schedule: Exactly once every 1 hour"
Write-Host "To test manually: Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "To check status:  Get-ScheduledTask -TaskName '$TaskName'"
Write-Host "To view log:      Get-Content `"$BackendDir\logs\keep_alive.log`" -Tail 10"
