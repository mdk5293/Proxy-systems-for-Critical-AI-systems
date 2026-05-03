```pwsh
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "& './Run-AnchorPipelineBatch.ps1' -Topics @('nlp') -Languages @('java') -TopAnchorsPerQuery 0 -SkipExisting -BatchLabel 'verify-nlp-java-all'"
```