# TestHarness_UPDATED.ps1
# Updated PowerShell test harness with GitLogger metrics and new testing scenarios
# Corresponds to the enhanced proxytool.ipynb notebook

$env:GH_TOKEN = ""  # ADD YOUR GITHUB TOKEN HERE

# Create organized output directory
$OutputDir = "results_plots"
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
    Write-Host "Created output directory: $OutputDir"
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PROXYTOOL CLI TEST HARNESS - UPDATED" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# -----------------------------------------------------------------------------
# TEST 1: Basic Comparison (Original)
# -----------------------------------------------------------------------------
Write-Host "`n[TEST 1] Basic comparison: vscode vs react" -ForegroundColor Yellow
python proxytool.py compare `
  --query https://github.com/microsoft/vscode `
  --candidates https://github.com/facebook/react `
  --github-token $env:GH_TOKEN `
  --metrics sentiment,churn,attach,cadence `
  --max-commits 100 `
  --plot "$OutputDir\test1_basic.png" `
  --plot-details `
  --dpi 200

# -----------------------------------------------------------------------------
# TEST 2: With GitLogger Metrics (NEW)
# -----------------------------------------------------------------------------
Write-Host "`n[TEST 2] With GitLogger metrics: vscode vs electron" -ForegroundColor Yellow
python proxytool.py compare `
  --query https://github.com/microsoft/vscode `
  --candidates https://github.com/electron/electron `
  --github-token $env:GH_TOKEN `
  --metrics sentiment,churn,attach,cadence,gitlogger `
  --max-commits 100 `
  --plot "$OutputDir\test2_gitlogger.png" `
  --plot-details `
  --dpi 200

# -----------------------------------------------------------------------------
# TEST 3: Weighted Sentiment (NEW - troubleshooting low scores)
# -----------------------------------------------------------------------------
Write-Host "`n[TEST 3] Weighted sentiment (2.5x): vscode vs electron" -ForegroundColor Yellow
python proxytool.py compare `
  --query https://github.com/microsoft/vscode `
  --candidates https://github.com/electron/electron `
  --github-token $env:GH_TOKEN `
  --metrics sentiment,churn,attach,cadence `
  --weights "sentiment=2.5,churn=1.0,attach=1.0,cadence=1.0" `
  --max-commits 100 `
  --plot "$OutputDir\test3_weighted.png" `
  --plot-details `
  --dpi 200

# -----------------------------------------------------------------------------
# TEST 4: Sentiment Only (NEW - isolate innovation)
# -----------------------------------------------------------------------------
Write-Host "`n[TEST 4] Sentiment-only comparison: vscode vs electron + react" -ForegroundColor Yellow
python proxytool.py compare `
  --query https://github.com/microsoft/vscode `
  --candidates https://github.com/electron/electron https://github.com/facebook/react `
  --github-token $env:GH_TOKEN `
  --metrics sentiment `
  --max-commits 100 `
  --plot "$OutputDir\test4_sentiment_only.png" `
  --plot-details `
  --plot-size 10x5 `
  --dpi 200

# -----------------------------------------------------------------------------
# TEST 5: Larger Sample Size (NEW - 500 commits)
# -----------------------------------------------------------------------------
Write-Host "`n[TEST 5] Larger sample (500 commits): vscode vs electron" -ForegroundColor Yellow
python proxytool.py compare `
  --query https://github.com/microsoft/vscode `
  --candidates https://github.com/electron/electron `
  --github-token $env:GH_TOKEN `
  --metrics sentiment,churn,attach,cadence `
  --max-commits 500 `
  --plot "$OutputDir\test5_500commits.png" `
  --plot-details `
  --dpi 200

# -----------------------------------------------------------------------------
# TEST 6: Multi-Candidate Comparison (NEW - better normalization)
# -----------------------------------------------------------------------------
Write-Host "`n[TEST 6] Multi-candidate (N=4): vscode vs electron+atom+react+django" -ForegroundColor Yellow
python proxytool.py compare `
  --query https://github.com/microsoft/vscode `
  --candidates https://github.com/electron/electron https://github.com/atom/atom https://github.com/facebook/react https://github.com/django/django `
  --github-token $env:GH_TOKEN `
  --metrics sentiment,churn,attach,cadence `
  --weights "sentiment=2.0" `
  --max-commits 150 `
  --plot "$OutputDir\test6_multi_candidate.png" `
  --plot-details `
  --plot-size 12x6 `
  --dpi 300 `
  --topn-features 12

# -----------------------------------------------------------------------------
# TEST 7: ML Framework Cluster (NEW - within-cluster testing)
# -----------------------------------------------------------------------------
Write-Host "`n[TEST 7] ML Cluster: tensorflow vs pytorch + sklearn" -ForegroundColor Yellow
python proxytool.py compare `
  --query https://github.com/tensorflow/tensorflow `
  --candidates https://github.com/pytorch/pytorch https://github.com/scikit-learn/scikit-learn `
  --github-token $env:GH_TOKEN `
  --metrics sentiment,churn,attach,cadence `
  --max-commits 100 `
  --plot "$OutputDir\test7_ml_cluster.png" `
  --plot-details `
  --plot-size 10x5 `
  --dpi 300

# -----------------------------------------------------------------------------
# TEST 8: Web Framework Cluster (NEW)
# -----------------------------------------------------------------------------
Write-Host "`n[TEST 8] Web Cluster: django vs flask" -ForegroundColor Yellow
python proxytool.py compare `
  --query https://github.com/django/django `
  --candidates https://github.com/pallets/flask `
  --github-token $env:GH_TOKEN `
  --metrics sentiment,churn,attach,cadence `
  --max-commits 100 `
  --plot "$OutputDir\test8_web_cluster.png" `
  --plot-details `
  --dpi 300

# -----------------------------------------------------------------------------
# TEST 9: Cross-Cluster Testing (NEW - should show low similarity)
# -----------------------------------------------------------------------------
Write-Host "`n[TEST 9] Cross-cluster: tensorflow (ML) vs django (Web)" -ForegroundColor Yellow
python proxytool.py compare `
  --query https://github.com/tensorflow/tensorflow `
  --candidates https://github.com/django/django `
  --github-token $env:GH_TOKEN `
  --metrics sentiment,churn,attach,cadence `
  --max-commits 100 `
  --plot "$OutputDir\test9_cross_cluster.png" `
  --plot-details `
  --dpi 300

# -----------------------------------------------------------------------------
# TEST 10: All Metrics with All Enhancements (COMPREHENSIVE)
# -----------------------------------------------------------------------------
Write-Host "`n[TEST 10] Comprehensive: All metrics + GitLogger + Weighted" -ForegroundColor Yellow
python proxytool.py compare `
  --query https://github.com/microsoft/vscode `
  --candidates https://github.com/electron/electron https://github.com/facebook/react `
  --github-token $env:GH_TOKEN `
  --metrics sentiment,churn,attach,cadence,gitlogger `
  --weights "sentiment=2.5,gitlogger=1.5" `
  --max-commits 200 `
  --plot "$OutputDir\test10_comprehensive.png" `
  --plot-details `
  --plot-size 10x5 `
  --dpi 300 `
  --topn-features 15

# -----------------------------------------------------------------------------
# RESULTS SUMMARY
# -----------------------------------------------------------------------------
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "TEST HARNESS COMPLETED" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nAll plots saved to: $OutputDir\" -ForegroundColor Green
Write-Host "Generated files:" -ForegroundColor Green
Get-ChildItem "$OutputDir\test*.png" | ForEach-Object {
    Write-Host "  - $($_.Name) ($([math]::Round($_.Length/1KB, 2)) KB)" -ForegroundColor Gray
}

Write-Host "`nCache location:" -ForegroundColor Green
if (Test-Path ".proxytool_cache") {
    $cacheCount = (Get-ChildItem ".proxytool_cache" -Filter "*.json").Count
    Write-Host "  - .proxytool_cache\ ($cacheCount cached repos)" -ForegroundColor Gray
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "TESTING SCENARIOS COVERED:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Basic comparison (original)" -ForegroundColor Green
Write-Host "✓ GitLogger metrics integration" -ForegroundColor Green
Write-Host "✓ Weighted sentiment (troubleshooting)" -ForegroundColor Green
Write-Host "✓ Sentiment-only (isolation test)" -ForegroundColor Green
Write-Host "✓ Larger samples (500 commits)" -ForegroundColor Green
Write-Host "✓ Multi-candidate (N>2 normalization)" -ForegroundColor Green
Write-Host "✓ Within-cluster similarity (ML, Web)" -ForegroundColor Green
Write-Host "✓ Cross-cluster dissimilarity" -ForegroundColor Green
Write-Host "✓ Comprehensive all-features test" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. Review plots in results_plots\" -ForegroundColor Yellow
Write-Host "2. Compare similarity scores across tests" -ForegroundColor Yellow
Write-Host "3. Check feature contribution charts (*__features__*.png)" -ForegroundColor Yellow
Write-Host "4. Run validation experiments in Jupyter for analysis" -ForegroundColor Yellow

# Quick view of first result
Write-Host "`nOpening first test result..." -ForegroundColor Cyan
Start-Process "$OutputDir\test1_basic.png"

Write-Host "`nPress any key to open results folder..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
Invoke-Item $OutputDir
