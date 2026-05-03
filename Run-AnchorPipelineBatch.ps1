<#
.SYNOPSIS
  Batch runner for anchor + match generation across topics/languages.

.DESCRIPTION
  For each topic/language query, this script:
    1) runs Get-AnchorCandidates.ps1
    2) reads recommended_anchors_top.csv
    3) selects anchors to match:
         - TopAnchorsPerQuery <= 0: use ALL rows in recommended_anchors_top.csv
         - TopAnchorsPerQuery > 0: use only the first N rows (cap for faster runs)
    4) runs Get-AnchorMatches.ps1 for each selected anchor
    5) writes a batch summary CSV under the batch output root

  Note: a repo-root 30_Matches.csv (if present) is NOT updated by this batch runner.
  Per-anchor outputs always live under runs/.../<owner>-<repo>/30_Matches.csv.

  Output layout:
    runs/<date>-batch/
      <topic>-<language>/
        anchor_candidates.csv
        recommended_anchors_top.csv
        ...
        <owner>-<repo>/
          30_Matches.csv
          ranked_matches.csv
          ...

.EXAMPLE
  ./Run-AnchorPipelineBatch.ps1 `
    -Topics @("mlops","nlp","computer-vision","llm") `
    -Languages @("python","typescript") `
    -TopAnchorsPerQuery 0 `
    -SkipExisting
#>

[CmdletBinding()]
param(
    [string[]]$Topics = @("mlops", "nlp", "computer-vision", "llm"), # "devops", "data-science", "reinforcement", "ai", "robotics", "autonomous-driving", "medical-ai", "financial-risk", "industrial-robotics", "recommender-systems", "security", "database", "web-development", "mobile-development", "game-development", "cloud-computing", "network-security", "data-engineering", "data-analysis", "data-warehousing", "data-pipelines", "data-orchestration", "data-integration", "data-modeling"),
    [string[]]$Languages = @("python", "javascript", "java"),
    # Optional expansion: "go", "rust", "c", "c++", "csharp", "php", "ruby", "swift", "kotlin", "scala", "haskell", "erlang", "elixir", "ocaml", "clojure", "groovy"
    [string]$RunRoot = "./runs",
    [string]$BatchLabel = "",
    [int]$AnchorQueryMinimumStars = 1000,
    [int]$AnchorSearchLimit = 50,
    [int]$AnchorTopK = 20,
    [int]$TopAnchorsPerQuery = 0,
    [int]$MatchMinimumScore = 900,
    [int]$MatchMinimumStars = 50,
    [int]$MatchTopK = 30,
    [int]$MatchMaxSearchPerQuery = 50,
    [switch]$AllowFallbackFill = $true,
    [switch]$AllowSameOwner,
    [switch]$AllowForks,
    [switch]$AllowArchived,
    [switch]$SkipExisting
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Get-SafeName {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return "unknown" }
    $safe = $Text.ToLowerInvariant() -replace '[^a-z0-9._-]+', '-'
    $safe = $safe.Trim('-')
    if ([string]::IsNullOrWhiteSpace($safe)) { return "unknown" }
    return $safe
}

Require-Command -Name "gh"
Require-Command -Name "pwsh"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$anchorScript = Join-Path $scriptDir "Get-AnchorCandidates.ps1"
$matchScript = Join-Path $scriptDir "Get-AnchorMatches.ps1"

if (-not (Test-Path $anchorScript)) { throw "Missing script: $anchorScript" }
if (-not (Test-Path $matchScript)) { throw "Missing script: $matchScript" }

$stamp = Get-Date -Format "yyyy-MM-dd"
$suffix = if ($BatchLabel) { "-" + (Get-SafeName -Text $BatchLabel) } else { "" }
$batchRoot = Join-Path $RunRoot ("{0}-batch{1}" -f $stamp, $suffix)
New-Item -ItemType Directory -Path $batchRoot -Force | Out-Null

$summary = [System.Collections.Generic.List[object]]::new()

foreach ($topic in @($Topics | Where-Object { $_ -and $_.Trim() })) {
    foreach ($language in @($Languages | Where-Object { $_ -and $_.Trim() })) {
        $topicSafe = Get-SafeName -Text $topic
        $langSafe = Get-SafeName -Text $language
        $queryDir = Join-Path $batchRoot ("{0}-{1}" -f $topicSafe, $langSafe)
        New-Item -ItemType Directory -Path $queryDir -Force | Out-Null

        $seedQuery = "topic:{0} language:{1} stars:>={2}" -f $topic, $language, $AnchorQueryMinimumStars
        Write-Host ""
        Write-Host ("=== Anchor candidates: {0} / {1} ===" -f $topic, $language) -ForegroundColor Cyan
        Write-Host ("SeedQuery: {0}" -f $seedQuery) -ForegroundColor Gray

        & $anchorScript `
            -SeedQuery $seedQuery `
            -OutputDir $queryDir `
            -SearchLimit $AnchorSearchLimit `
            -TopK $AnchorTopK `
            -MinimumStars $AnchorQueryMinimumStars `
            -AllowForks:$AllowForks `
            -AllowArchived:$AllowArchived

        $recommendedPath = Join-Path $queryDir "recommended_anchors_top.csv"
        if (-not (Test-Path $recommendedPath)) {
            Write-Warning "No recommended anchors file for query: $seedQuery"
            continue
        }

        $recommendedRows = @(Import-Csv -Path $recommendedPath)
        if ($TopAnchorsPerQuery -le 0) {
            $anchors = $recommendedRows
        }
        else {
            $anchors = @($recommendedRows | Select-Object -First $TopAnchorsPerQuery)
        }
        if (@($anchors).Count -eq 0) {
            Write-Warning "No anchors found for query: $seedQuery"
            continue
        }

        foreach ($anchor in $anchors) {
            $anchorRepo = [string]$anchor.RepoName
            if ([string]::IsNullOrWhiteSpace($anchorRepo)) { continue }

            $anchorSafe = Get-SafeName -Text ($anchorRepo -replace '/', '-')
            $anchorDir = Join-Path $queryDir $anchorSafe
            $finalCsvPath = Join-Path $anchorDir "30_Matches.csv"

            if ($SkipExisting -and (Test-Path $finalCsvPath)) {
                Write-Host ("Skipping existing: {0}" -f $anchorRepo) -ForegroundColor Yellow
            }
            else {
                New-Item -ItemType Directory -Path $anchorDir -Force | Out-Null
                Write-Host ("Running matches for anchor: {0}" -f $anchorRepo) -ForegroundColor Green

                & $matchScript `
                    -AnchorRepo $anchorRepo `
                    -OutputDir $anchorDir `
                    -TopK $MatchTopK `
                    -MaxSearchPerQuery $MatchMaxSearchPerQuery `
                    -MinimumStars $MatchMinimumStars `
                    -MinimumScore $MatchMinimumScore `
                    -AllowFallbackFill:$AllowFallbackFill `
                    -AllowSameOwner:$AllowSameOwner `
                    -AllowForks:$AllowForks `
                    -AllowArchived:$AllowArchived
            }

            $qualifiedCount = 0
            $finalCount = 0
            $rankedPath = Join-Path $anchorDir "ranked_matches.csv"
            if (Test-Path $rankedPath) {
                $rankedRows = @(Import-Csv -Path $rankedPath)
                $qualifiedCount = @($rankedRows | Where-Object { "$($_.Qualified)" -eq "True" }).Count
            }
            if (Test-Path $finalCsvPath) {
                $finalCount = @(Import-Csv -Path $finalCsvPath).Count
            }

            $summary.Add([PSCustomObject]@{
                Topic          = $topic
                Language       = $language
                SeedQuery      = $seedQuery
                AnchorRepo     = $anchorRepo
                AnchorRank     = $anchor.Rank
                AnchorScore    = $anchor.Score
                AnchorOutput   = $anchorDir
                FinalMatches   = $finalCount
                QualifiedCount = $qualifiedCount
                FinalCsv       = $finalCsvPath
                RankedCsv      = $rankedPath
            }) | Out-Null
        }
    }
}

$summaryCsv = Join-Path $batchRoot "batch_summary.csv"
$summaryJson = Join-Path $batchRoot "batch_summary.json"

$summary | Export-Csv -Path $summaryCsv -NoTypeInformation -Encoding UTF8
$summary | ConvertTo-Json -Depth 8 | Set-Content -Path $summaryJson -Encoding UTF8

Write-Host ""
Write-Host "Batch complete." -ForegroundColor Cyan
Write-Host ("Root: {0}" -f (Resolve-Path $batchRoot)) -ForegroundColor Green
Write-Host ("Summary CSV: {0}" -f $summaryCsv) -ForegroundColor Green
Write-Host ("Summary JSON: {0}" -f $summaryJson) -ForegroundColor Green
