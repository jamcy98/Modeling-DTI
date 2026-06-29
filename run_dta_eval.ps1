$py      = "C:\Users\Jamila\anaconda3\python.exe"
$wd      = "C:\Users\Jamila\Modeling-DTI"
Set-Location $wd
$env:PYTHONUNBUFFERED = "1"

# DTA evaluation: random split only (standard benchmark for DAVIS/KIBA).
# Cold splits omitted — 118k KIBA pairs makes all-split evaluation impractical on CPU.

$datasets = @("davis", "kiba")
$seeds    = @(1, 2, 3, 4, 5)

$total = $datasets.Count * $seeds.Count
$i = 0

foreach ($seed in $seeds) {
    foreach ($dataset in $datasets) {
        $i++
        Write-Host ""
        Write-Host "== Run $i/$total : hgnn_rnn_dti | $dataset | dta | random | seed $seed =="
        & $py train.py --model hgnn_rnn_dti --dataset $dataset --task dta --split random --seed $seed --batch_size 256
        if (-not $?) {
            Write-Host "FAILED: $dataset seed $seed"
        }
    }
}

Write-Host ""
Write-Host "== DTA evaluation (davis + kiba, random split) complete. =="
