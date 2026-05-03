<#
.SYNOPSIS
  Find and rank repositories that are likely to be good anchor repos for later matching.

.DESCRIPTION
  Uses GitHub's REST search API through `gh api` to:
    1) retrieve repositories from one or more seed queries
    2) normalize and merge the candidate pool
    3) score repositories as potential anchors using metadata quality heuristics
    4) write ranked anchor-candidate outputs

.PARAMETER SeedQuery
  Main GitHub repository search query, e.g.:
    "topic:machine-learning language:python stars:>=1000"

.PARAMETER ExtraQueries
  Optional additional GitHub search queries.

.PARAMETER OutputDir
  Directory for output files. Defaults to current directory.

.PARAMETER SearchLimit
  Number of results to retrieve per query. Defaults to 50.

.PARAMETER TopK
  Number of recommended anchors to write to the top-list outputs. Defaults to 20.

.PARAMETER MinimumStars
  Minimum stars for repos to be considered. Defaults to 100.

.PARAMETER AllowForks
  Allow fork repositories. Default is false.

.PARAMETER AllowArchived
  Allow archived repositories. Default is false.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SeedQuery,

    [string[]]$ExtraQueries = @(),

    [string]$OutputDir = ".",

    [int]$SearchLimit = 50,

    [int]$TopK = 20,

    [int]$MinimumStars = 100,

    [switch]$AllowForks,

    [switch]$AllowArchived
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Get-Json {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return $null }
    return $Text | ConvertFrom-Json
}

function Invoke-GhApi {
    param(
        [string]$Path,
        [hashtable]$Fields = @{}
    )

    $args = @("api", "-X", "GET", $Path)
    foreach ($key in $Fields.Keys) {
        $args += @("-f", "$key=$($Fields[$key])")
    }

    $raw = & gh @args 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "gh api failed for path '$Path': $raw"
    }

    return Get-Json -Text $raw
}

function Search-Repositories {
    param(
        [string]$Query,
        [int]$PerPage = 50
    )

    Write-Host "Searching: $Query" -ForegroundColor Gray
    $resp = Invoke-GhApi -Path "search/repositories" -Fields @{
        q        = $Query
        sort     = "stars"
        order    = "desc"
        per_page = $PerPage
    }

    $items = @($resp.items)
    Write-Host "  Found $(@($items).Count) repositories." -ForegroundColor Green
    return $items
}

function Get-RepoDetails {
    param([string]$FullName)

    $repo = Invoke-GhApi -Path ("repos/{0}" -f $FullName)
    return [PSCustomObject]@{
        FullName    = [string]$repo.full_name
        Name        = [string]$repo.name
        Url         = [string]$repo.html_url
        Description = [string]$repo.description
        Topics      = @($repo.topics)
        Language    = [string]$repo.language
        Stars       = [int]$repo.stargazers_count
        Fork        = [bool]$repo.fork
        Archived    = [bool]$repo.archived
        CreatedAt   = [datetime]$repo.created_at
        UpdatedAt   = [datetime]$repo.updated_at
        Owner       = [string]$repo.owner.login
        Homepage    = [string]$repo.homepage
        License     = if ($repo.license) { [string]$repo.license.spdx_id } else { "" }
    }
}

function Get-TextTokens {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) { return @() }

    $stop = @(
        "the","and","for","with","from","into","using","based","tool","repo","repository",
        "project","system","software","application","framework","library","package","code",
        "python","javascript","typescript","java","rust","csharp","cpp","go","php","ruby",
        "an","a","to","of","in","on","at","by","or","is","are","this","that","it","be"
    ) | ForEach-Object { $_.ToLowerInvariant() }

    $parts = ($Text.ToLowerInvariant() -replace '[^a-z0-9\-\+ ]', ' ') -split '\s+'
    $parts = $parts | Where-Object { $_ -and $_.Length -ge 3 -and ($stop -notcontains $_) }
    return @($parts | Select-Object -Unique)
}

function Test-JunkRepo {
    param([object]$Repo)

    $text = ("{0} {1} {2}" -f [string]$Repo.FullName, [string]$Repo.Name, [string]$Repo.Description).ToLowerInvariant()
    $junkPatterns = @(
        "awesome", "tutorial", "boilerplate", "template", "starter",
        "snippets", "sandbox", "notes", "roadmap", "interview", "cheatsheet",
        "curated-list", "book", "course", "examples", "playground", "demo"
    )

    foreach ($p in $junkPatterns) {
        if ($text -like "*$p*") { return $true }
    }
    return $false
}

function Get-Subdomain {
    param(
        [string]$Description,
        [string[]]$Topics,
        [string]$Language
    )

    $text = ((@($Topics) -join " ") + " " + [string]$Description + " " + [string]$Language).ToLowerInvariant()

    $rules = [ordered]@{
        "llm"             = @("llm","gpt","transformer","instruction","rag","prompt","chatbot","language-model")
        "deep-learning"   = @("deep-learning","neural","cnn","rnn","torch","tensorflow","keras")
        "computer-vision" = @("computer-vision","image","vision","detection","segmentation","ocr","opencv")
        "nlp"             = @("nlp","natural-language","tokenization","embedding","summarization","translation")
        "mlops"           = @("mlops","pipeline","orchestration","serving","deployment","tracking","experiment")
        "editor"          = @("editor","ide","code-editor","text-editor","syntax-highlighting","lsp","language-server")
        "data-science"    = @("data-science","notebook","analysis","feature-engineering","pandas","sklearn")
        "reinforcement"   = @("reinforcement","rl","policy","agent","gym")
    }

    foreach ($key in $rules.Keys) {
        foreach ($needle in $rules[$key]) {
            if ($text -like "*$needle*") { return $key }
        }
    }

    return ""
}

function Score-AnchorCandidate {
    param([object]$Repo)

    $junk = Test-JunkRepo -Repo $Repo
    $topics = @($Repo.Topics)
    $desc = [string]$Repo.Description
    $lang = [string]$Repo.Language
    $name = [string]$Repo.Name

    $topicRichness = [math]::Min(1.0, [double](@($topics).Count) / 6.0)

    $descTokens = Get-TextTokens -Text $desc
    $nameTokens = Get-TextTokens -Text ($name -replace '[-_]', ' ')

    $descQuality = 0.0
    if (-not [string]::IsNullOrWhiteSpace($desc)) {
        $len = $desc.Trim().Length
        if ($len -ge 30 -and $len -le 240) { $descQuality = 1.0 }
        elseif ($len -ge 15) { $descQuality = 0.6 }
        else { $descQuality = 0.2 }
    }

    $languagePresence = if ($lang) { 1.0 } else { 0.0 }

    $starsScore = 0.0
    if ($Repo.Stars -gt 0) {
        $starsScore = [math]::Min(1.0, [math]::Log10([double]($Repo.Stars + 1)) / 5.0)
    }

    $updatedDays = [math]::Abs(((Get-Date) - $Repo.UpdatedAt).TotalDays)
    $recencyScore =
        if     ($updatedDays -le 30)  { 1.0 }
        elseif ($updatedDays -le 90)  { 0.9 }
        elseif ($updatedDays -le 180) { 0.75 }
        elseif ($updatedDays -le 365) { 0.55 }
        elseif ($updatedDays -le 730) { 0.35 }
        else                          { 0.15 }

    $ageDays = [math]::Abs(((Get-Date) - $Repo.CreatedAt).TotalDays)
    $longevityScore =
        if     ($ageDays -ge 3650) { 1.0 }
        elseif ($ageDays -ge 1825) { 0.8 }
        elseif ($ageDays -ge 730)  { 0.6 }
        elseif ($ageDays -ge 365)  { 0.4 }
        else                       { 0.2 }

    $signalClarity = [math]::Min(1.0, ([double]((@($descTokens).Count) + (@($nameTokens).Count) + (@($topics).Count)) / 12.0))

    $subdomain = Get-Subdomain -Description $desc -Topics $topics -Language $lang
    $subdomainScore = if ($subdomain) { 1.0 } else { 0.0 }

    $penalty = 0.0
    if ($junk) { $penalty += 600.0 }
    if ($Repo.Fork) { $penalty += 250.0 }
    if ($Repo.Archived) { $penalty += 250.0 }

    $score =
        (450.0 * $topicRichness) +
        (325.0 * $descQuality) +
        (125.0 * $languagePresence) +
        (275.0 * $starsScore) +
        (225.0 * $recencyScore) +
        (225.0 * $longevityScore) +
        (275.0 * $signalClarity) +
        (150.0 * $subdomainScore) -
        $penalty

    return [PSCustomObject]@{
        TopicRichness   = [math]::Round($topicRichness, 4)
        DescriptionQ    = [math]::Round($descQuality, 4)
        LanguagePresent = [math]::Round($languagePresence, 4)
        StarsScore      = [math]::Round($starsScore, 4)
        RecencyScore    = [math]::Round($recencyScore, 4)
        LongevityScore  = [math]::Round($longevityScore, 4)
        SignalClarity   = [math]::Round($signalClarity, 4)
        Subdomain       = $subdomain
        SubdomainScore  = [math]::Round($subdomainScore, 4)
        JunkPenalty     = $penalty
        IsJunk          = $junk
        Score           = [math]::Round($score, 2)
    }
}

Require-Command -Name "gh"

$OutputDir = [System.IO.Path]::GetFullPath($OutputDir)
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

$queries = @($SeedQuery)
if ($ExtraQueries) {
    $queries += @($ExtraQueries)
}
$queries = @($queries | Where-Object { $_ -and $_.Trim() } | Select-Object -Unique)

if (@($queries).Count -eq 0) {
    throw "No search queries were provided."
}

$candidateMap = @{}

foreach ($query in $queries) {
    $results = Search-Repositories -Query $query -PerPage $SearchLimit

    foreach ($repo in $results) {
        $fullName = [string]$repo.full_name
        if (-not $fullName) { continue }
        if (-not $AllowForks -and [bool]$repo.fork) { continue }
        if (-not $AllowArchived -and [bool]$repo.archived) { continue }
        if ([int]$repo.stargazers_count -lt $MinimumStars) { continue }

        if ($candidateMap.ContainsKey($fullName)) {
            continue
        }

        $candidateMap[$fullName] = [PSCustomObject]@{
            FullName    = [string]$repo.full_name
            Name        = [string]$repo.name
            Url         = [string]$repo.html_url
            Description = [string]$repo.description
            Topics      = @()
            Language    = [string]$repo.language
            Stars       = [int]$repo.stargazers_count
            Fork        = [bool]$repo.fork
            Archived    = [bool]$repo.archived
            CreatedAt   = [datetime]$repo.created_at
            UpdatedAt   = [datetime]$repo.updated_at
            Owner       = [string]$repo.owner.login
            Homepage    = ""
            License     = ""
            SourceQuery = $query
        }
    }
}

$candidates = @($candidateMap.Values)

$enriched = [System.Collections.Generic.List[object]]::new()
foreach ($cand in $candidates) {
    try {
        $d = Get-RepoDetails -FullName $cand.FullName
        $cand.Topics = @($d.Topics)
        $cand.Language = if ($d.Language) { $d.Language } else { $cand.Language }
        $cand.Stars = if ($d.Stars -gt 0) { $d.Stars } else { $cand.Stars }
        $cand.CreatedAt = $d.CreatedAt
        $cand.UpdatedAt = $d.UpdatedAt
        $cand.Fork = $d.Fork
        $cand.Archived = $d.Archived
        $cand.Description = if ($d.Description) { $d.Description } else { $cand.Description }
        $cand.Homepage = $d.Homepage
        $cand.License = $d.License
    }
    catch {
        # keep the partial candidate if enrichment fails
    }

    $enriched.Add($cand) | Out-Null
}

$scored = foreach ($cand in $enriched) {
    $parts = Score-AnchorCandidate -Repo $cand
    [PSCustomObject]@{
        Rank             = 0
        RepoName         = $cand.FullName
        RepoUrl          = $cand.Url
        Owner            = $cand.Owner
        Language         = $cand.Language
        Stars            = $cand.Stars
        CreatedAt        = $cand.CreatedAt
        UpdatedAt        = $cand.UpdatedAt
        Topics           = (@($cand.Topics) -join ';')
        Subdomain        = $parts.Subdomain
        Score            = $parts.Score
        TopicRichness    = $parts.TopicRichness
        DescriptionQ     = $parts.DescriptionQ
        LanguagePresent  = $parts.LanguagePresent
        StarsScore       = $parts.StarsScore
        RecencyScore     = $parts.RecencyScore
        LongevityScore   = $parts.LongevityScore
        SignalClarity    = $parts.SignalClarity
        SubdomainScore   = $parts.SubdomainScore
        JunkPenalty      = $parts.JunkPenalty
        IsJunk           = $parts.IsJunk
        SourceQuery      = $cand.SourceQuery
        Description      = $cand.Description
    }
}

$scored = @($scored | Sort-Object -Property @{Expression='Score';Descending=$true}, @{Expression='Stars';Descending=$true}, @{Expression='RepoName';Descending=$false})

$rank = 1
foreach ($item in $scored) {
    $item.Rank = $rank
    $rank++
}

$top = @($scored | Select-Object -First $TopK)

$allCsv = Join-Path $OutputDir "anchor_candidates.csv"
$allJson = Join-Path $OutputDir "anchor_candidates.json"
$topCsv = Join-Path $OutputDir "recommended_anchors_top.csv"
$topJson = Join-Path $OutputDir "recommended_anchors_top.json"

$scored | Export-Csv -Path $allCsv -NoTypeInformation -Encoding UTF8
$scored | ConvertTo-Json -Depth 8 | Set-Content -Path $allJson -Encoding UTF8
$top | Export-Csv -Path $topCsv -NoTypeInformation -Encoding UTF8
$top | ConvertTo-Json -Depth 8 | Set-Content -Path $topJson -Encoding UTF8

Write-Host ""
Write-Host "Wrote:" -ForegroundColor Cyan
Write-Host "  - $allCsv"
Write-Host "  - $allJson"
Write-Host "  - $topCsv"
Write-Host "  - $topJson"
Write-Host ""
Write-Host "Candidate count: $(@($scored).Count)" -ForegroundColor Green
Write-Host "Top anchors written: $(@($top).Count)" -ForegroundColor Green
