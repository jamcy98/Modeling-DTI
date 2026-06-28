$py  = "C:\Users\Jamila\anaconda3\python.exe"
$wd  = "C:\Users\Jamila\Modeling-DTI"
Set-Location $wd

$seeds = @(1, 2, 3, 4, 5)
$total = $seeds.Count
$i = 0

foreach ($seed in $seeds) {
    $i++
    Write-Host ""
    Write-Host "== Run $i/$total : cross luo_17 -> yamanishi_e | seed $seed =="
    & $py cross_dataset_eval.py --seed $seed
    if (-not $?) {
        Write-Host "FAILED: seed $seed"
    }
}

Write-Host ""
Write-Host "== Cross-dataset evaluation complete. =="
