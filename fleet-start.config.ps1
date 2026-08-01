# Per-repo fleet start config for filesystem-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'filesystem-mcp'
    BackendPort  = 10742
    FrontendPort = 10743
    HealthPath   = '/api/health'
    WebRoot      = 'D:\Dev\repos\filesystem-mcp\webapp'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'filesystem_mcp.server:app'
        SyncExtras    = @()
        Env           = @{ WEB_PORT = '10742' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
