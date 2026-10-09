; Kill UI + backend before install/uninstall (backend locks resources/*.exe).
; Fleet registration: defines + canonical mcp-clients.nsh (AI-tool installer page).
!define MCP_REG_NAME "filesystem-mcp"             ; key written into AI client configs
!define MCP_REG_EXE  "filesystem-mcp-backend.exe" ; stdio-capable exe under $INSTDIR\resources\
!include "mcp-clients.nsh"
!macro KillFilesystemMcpFleetProcesses
  DetailPrint "Stopping filesystem-mcp processes..."
  ExecWait 'taskkill /F /IM filesystem-mcp-backend.exe /T' $0
  ExecWait 'taskkill /F /IM filesystem-mcp-native.exe /T' $0
  !if "${INSTALLMODE}" == "currentUser"
    nsis_tauri_utils::KillProcessCurrentUser "filesystem-mcp-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcessCurrentUser "filesystem-mcp-native.exe"
    Pop $0
  !else
    nsis_tauri_utils::KillProcess "filesystem-mcp-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcess "filesystem-mcp-native.exe"
    Pop $0
  !endif
  Sleep 2000
!macroend

!macro NSIS_HOOK_PREINSTALL
  !insertmacro KillFilesystemMcpFleetProcesses
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro KillFilesystemMcpFleetProcesses
  !insertmacro McpClientsUnregister
!macroend

!macro NSIS_HOOK_POSTINSTALL
  !insertmacro McpClientsRegister
!macroend
