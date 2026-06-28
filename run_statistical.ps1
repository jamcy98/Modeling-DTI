$py      = "C:\Users\Jamila\anaconda3\python.exe"
$wd      = "C:\Users\Jamila\Modeling-DTI"
Set-Location $wd

$models   = @("hgnn_rnn_dti", "concat_baseline")
$datasets = @("yamanishi_e", "luo_17")
$splits   = @("random", "cold_drug", "cold_target", "cold_pair")
$seeds    = @(1, 2, 3, 4, 5)

$total = $models.Count * $datasets.Count * $splits.Count * $seeds.Count
$i = 0

foreach ($seed in $seeds) {
    foreach ($model in $models) {
        foreach ($dataset in $datasets) {
            foreach ($split in $splits) {
                $i++
                Write-Host ""
                Write-Host "== Run $i/$total : $model | $dataset | $split | seed $seed =="
                & $py train.py --model $model --dataset $dataset --task dti --split $split --seed $seed
                if (-not $?) {
                    Write-Host "FAILED: $model $dataset $split seed $seed"
                }
            }
        }
    }
}

Write-Host ""
Write-Host "== Statistical testing runs complete. =="
