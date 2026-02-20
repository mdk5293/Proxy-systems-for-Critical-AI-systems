$env:GH_TOKEN = ""

# Fast test (100 commits)
#python proxytool.py compare `
#  --query https://github.com/microsoft/vscode `
#  --candidates https://github.com/facebook/react https://github.com/electron/electron `
#  --github-token $env:GH_TOKEN `
#  --metrics sentiment,churn,attach,cadence `
#  --max-commits 100 `
#  --plot .\results.png `
#  --plot-details `
#  --plot-size 10x5 `
#  --dpi 300 `
#  --topn-features 8 `
#  --quiet

## Full run (after cache)
python proxytool.py compare `
  --query https://github.com/microsoft/vscode `
  --candidates https://github.com/facebook/react https://github.com/electron/electron `
  --github-token $env:GH_TOKEN `
  --metrics sentiment,churn,attach,cadence `
  --plot .\results.png `
  --plot-details `
  --plot-size 10x5 `
  --dpi 300 `
  --topn-features 8 `
  --quiet

Get-Location                  # shows the current folder
Resolve-Path .\results.png    # prints the full path if it exists
Get-ChildItem results.png     # lists the file
start .\results.png           # opens it

#Google Scholar
#IEEE LaPlante columns
#https://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=10970190
#https://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=10687342
