$py = "C:\Users\Jamila\anaconda3\python.exe"
$wd = "C:\Users\Jamila\Modeling-DTI"
Set-Location $wd

$splits_gsrf = @("random", "cold_drug", "cold_target", "cold_pair")
$splits_dtkgin = @("random", "cold_drug", "cold_target", "cold_pair")
$seeds = @(1, 2, 3)

$total = $splits_gsrf.Count * $seeds.Count + $splits_dtkgin.Count * $seeds.Count
$i = 0

Write-Host ""
Write-Host "== GSRF-DTI (luo_17) =="

foreach ($split in $splits_gsrf) {
    foreach ($seed in $seeds) {
        $i++
        Write-Host ""
        Write-Host "== Run $i/$total : GSRF-DTI | luo_17 | $split | seed $seed =="
        & $py baselines/gsrf_dti.py --split $split --seed $seed --epochs 100
        if (-not $?) { Write-Host "FAILED: gsrf_dti $split seed $seed" }
    }
}

Write-Host ""
Write-Host "== DTKGIN (yamanishi_e) =="

foreach ($split in $splits_dtkgin) {
    foreach ($seed in $seeds) {
        $i++
        Write-Host ""
        Write-Host "== Run $i/$total : DTKGIN | yamanishi_e | $split | seed $seed =="
        & $py baselines/dtkgin.py --split $split --seed $seed --epochs 150
        if (-not $?) { Write-Host "FAILED: dtkgin $split seed $seed" }
    }
}

Write-Host ""
Write-Host "== Baseline runs complete. =="
