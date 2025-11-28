# Скрипт для остановки всех запущенных экземпляров бота
Write-Host "Поиск запущенных процессов Python..." -ForegroundColor Yellow

$pythonProcesses = Get-Process python* -ErrorAction SilentlyContinue

if ($pythonProcesses) {
    Write-Host "Найдено процессов Python: $($pythonProcesses.Count)" -ForegroundColor Yellow
    foreach ($proc in $pythonProcesses) {
        Write-Host "Остановка процесса: PID $($proc.Id) - $($proc.ProcessName)" -ForegroundColor Red
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "Все процессы Python остановлены." -ForegroundColor Green
    Start-Sleep -Seconds 2
} else {
    Write-Host "Запущенные процессы Python не найдены." -ForegroundColor Green
}

Write-Host "`nТеперь можно запустить бота: python bot.py" -ForegroundColor Cyan

