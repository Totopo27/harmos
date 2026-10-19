# Max Live Verifier Loop Reference

## Verification Loop Architecture

The live verification workflow guarantees that compiled externals and generated patchers execute cleanly in a real Max runtime environment:

```
[Generate / Build Artifact]
         │
         ▼
[Deploy to Packages/<suite>/externals]
         │
         ▼
[Launch Max.exe with test patcher via PowerShell]
         │
         ▼
[Focus Window & Execute capturar.ps1 screenshot]
         │
         ▼
[Audit Max Console Output & Visual Render]
     ┌───┴───┐
  PASS      FAIL
     │       │
     │       ▼
     │   [Extract exact error message]
     │       │
     │       ▼
     │   [Feedback to Generator / Validator]
     │       │
     │   [Retry Loop]
     ▼
[Final Clean Report]
```

## Failure Diagnosis & Recovery

- **Red text in Max Console**: Look for unresolved external dependencies, missing C++ runtime libraries, or signal loop deadlocks.
- **Visual Artifacts**: Inspect UI bounding boxes for truncated labels, clipped slider handles, or magenta/red object outline errors.
- **Log Path**: Check `%APPDATA%\Cycling '74\Max X\Logs\Max.log` when GUI capture is obstructed.
