# Codex Docker bootstrap

This profile-wide Windows tool installs argument-preserving `docker.exe` and
`docker-compose.exe` launchers. Engine-dependent commands start Docker Desktop
on demand, wait for the engine, and then invoke Docker's real executable by a
trusted absolute path. Docker is never stopped automatically.

Install from the repository root:

```powershell
uv tool install --force .\tools\codex-docker-bootstrap
```

Readiness check:

```powershell
ensure-docker-desktop --json
```

Rollback:

```powershell
uv tool uninstall codex-docker-bootstrap
```
