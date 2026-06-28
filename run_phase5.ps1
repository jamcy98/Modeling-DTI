$py = "C:\Users\Jamila\anaconda3\python.exe"
$wd = "C:\Users\Jamila\Modeling-DTI"
Set-Location $wd

$models   = @("hgnn_rnn_dti", "concat_baseline")
$datasets = @("yamanishi_e", "luo_17")
$splits   = @("cold_drug", "cold_target", "cold_pair")

$total = $models.Count * $datasets.Count * $splits.Count
$i = 0

foreach ($model in $models) {
    foreach ($dataset in $datasets) {
        foreach ($split in $splits) {
            $i++
            Write-Host ""
            Write-Host "== Run $i/$total : $model | $dataset | $split =="
            & $py train.py --model $model --dataset $dataset --task dti --split $split
            if (-not $?) {
                Write-Host "FAILED: $model $dataset $split"
            }
        }
    }
}

Write-Host ""
Write-Host "== Phase 5 complete - all splits done. =="
