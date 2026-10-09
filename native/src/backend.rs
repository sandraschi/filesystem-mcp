use std::fs::{self, OpenOptions};
use std::io::{Read, Write};
use std::net::{SocketAddr, TcpStream, ToSocketAddrs};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::str::FromStr;
use std::sync::Mutex;
use std::thread;
use std::time::Duration;

use tauri::path::BaseDirectory;
use tauri::{AppHandle, Emitter, Manager};

pub struct BackendProcess(pub Mutex<Option<Child>>);

// -- PER-REPO: Customize these constants --
const BACKEND_NAME: &str = "filesystem-mcp-backend.exe";
const BACKEND_PORT: u16 = 10742;
const BACKEND_TAG: &str = "filesystem-mcp-backend-x86_64-pc-windows-msvc.exe";
const HEALTH_PATH: &str = "/health";
const ENV_PORT: &str = "FILESYSTEM_PORT";
const ENV_HOST: &str = "FILESYSTEM_HOST";
const ENV_TAURI: &str = "FILESYSTEM_MCP_TAURI";

fn dev_backend_path() -> Option<PathBuf> {
    if !cfg!(debug_assertions) {
        return None;
    }
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("binaries")
        .join(BACKEND_TAG);
    path.exists().then_some(path)
}

fn log_line(app: &AppHandle, message: &str) {
    eprintln!("[backend] {message}");
    if let Ok(dir) = app.path().app_log_dir() {
        let _ = fs::create_dir_all(&dir);
        let log_path = dir.join("backend-spawn.log");
        if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(log_path) {
            let _ = writeln!(file, "{message}");
        }
    }
}

fn resolve_bundled_backend(app: &AppHandle) -> Result<PathBuf, String> {
    let mut tried = Vec::new();

    // resources/ FIRST: an orphaned flat copy at the install root must never win.
    let resources_path = format!("resources/{BACKEND_NAME}");
    if let Ok(path) = app.path().resolve(&resources_path, BaseDirectory::Resource) {
        tried.push(path.display().to_string());
        if path.exists() {
            return Ok(path);
        }
    }

    if let Ok(dir) = app.path().executable_dir() {
        let path = dir.join("resources").join(BACKEND_NAME);
        tried.push(path.display().to_string());
        if path.exists() {
            return Ok(path);
        }
    }

    if let Ok(path) = app.path().resolve(BACKEND_NAME, BaseDirectory::Resource) {
        tried.push(path.display().to_string());
        if path.exists() {
            return Ok(path);
        }
    }

    Err(format!("bundled backend missing from resources (tried: {})", tried.join("; ")))
}

fn install_dir_from_backend(path: &PathBuf) -> PathBuf {
    if let Some(parent) = path.parent() {
        if parent
            .file_name()
            .is_some_and(|name| name.eq_ignore_ascii_case("resources"))
        {
            if let Some(install_dir) = parent.parent() {
                return install_dir.to_path_buf();
            }
        }
        return parent.to_path_buf();
    }
    PathBuf::from(".")
}

pub fn materialize_backend(app: &AppHandle) -> Result<PathBuf, String> {
    if let Some(dev_path) = dev_backend_path() {
        log_line(app, &format!("using dev backend: {}", dev_path.display()));
        return Ok(dev_path);
    }

    let bundled = resolve_bundled_backend(app)?;
    log_line(app, &format!("using bundled backend: {}", bundled.display()));
    // Strip Windows extended-length prefix
    let s = bundled.to_string_lossy().to_string();
    let clean = s.strip_prefix("\\\\?\\").map(PathBuf::from).unwrap_or(bundled.clone());
    Ok(clean)
}

/// True only if the port holder answers the app's real health endpoint with 200
/// (liveness is not health: a zombie can accept TCP, a stuck init can 500).
fn port_holder_is_responsive(port: u16) -> bool {
    let addr = match ("127.0.0.1", port).to_socket_addrs() {
        Ok(mut addrs) => match addrs.next() {
            Some(addr) => addr,
            None => return false,
        },
        Err(_) => return false,
    };
    let mut stream = match TcpStream::connect_timeout(&addr, Duration::from_millis(500)) {
        Ok(s) => s,
        Err(_) => return false,
    };
    let _ = stream.set_read_timeout(Some(Duration::from_millis(1500)));
    let _ = stream.set_write_timeout(Some(Duration::from_millis(500)));
    let request = format!("GET {HEALTH_PATH} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nConnection: close\r\n\r\n");
    if stream.write_all(request.as_bytes()).is_err() {
        return false;
    }
    let mut buf = [0u8; 64];
    let n = match stream.read(&mut buf) {
        Ok(n) if n > 0 => n,
        _ => return false,
    };
    String::from_utf8_lossy(&buf[..n]).split_whitespace().nth(1) == Some("200")
}

fn free_port(_port: u16) {
    // Image-scoped kill only. A blind port-PID kill murders unrelated holders
    // (Docker wslrelay, NSSM services) - TAURI_PRODUCTION_PITFALLS sec 15.
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        let _ = Command::new("taskkill.exe")
            .args(["/F", "/IM", BACKEND_NAME, "/T"])
            .creation_flags(0x0800_0000) // CREATE_NO_WINDOW
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status();
        thread::sleep(Duration::from_millis(600));
    }
}

fn stop_managed_child(state: &BackendProcess) {
    if let Some(mut child) = state.0.lock().unwrap().take() {
        let _ = child.kill();
        let _ = child.wait();
    }
}

pub fn spawn_backend(app: AppHandle, state: &BackendProcess) -> Result<String, String> {
    stop_managed_child(state);

    // Attach to an already-healthy backend (e.g. the dev stack) instead of killing it.
    if port_holder_is_responsive(BACKEND_PORT) {
        log_line(
            &app,
            &format!("port {BACKEND_PORT} already serving and responsive - attaching instead of spawning"),
        );
        let _ = app.emit("backend-status", "ready");
        return Ok(format!("Attached to existing backend on port {BACKEND_PORT}"));
    }

    free_port(BACKEND_PORT);

    let backend_path = materialize_backend(&app)?;
    let workdir = app
        .path()
        .executable_dir()
        .ok()
        .unwrap_or_else(|| install_dir_from_backend(&backend_path));

    log_line(
        &app,
        &format!("spawning {} (cwd {}) on port 10742",
            backend_path.display(), workdir.display()),
    );

    let mut command = Command::new(&backend_path);
    command
        .current_dir(&workdir)
        .env(ENV_PORT, BACKEND_PORT.to_string())
        .env(ENV_HOST, "127.0.0.1")
        .env(ENV_TAURI, "1")
        .stdout(Stdio::null())
        .stderr(Stdio::null());

    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x0800_0000;
        command.creation_flags(CREATE_NO_WINDOW);
    }

    let child = command
        .spawn()
        .map_err(|e| format!("Failed to spawn {}: {e}", backend_path.display()))?;

    state.0.lock().unwrap().replace(child);

    let addr = SocketAddr::from_str(&format!("127.0.0.1:{BACKEND_PORT}")).unwrap();
    let app_health = app.clone();
    thread::spawn(move || {
        for attempt in 0..30 {
            thread::sleep(Duration::from_secs(2));
            match TcpStream::connect_timeout(&addr, Duration::from_secs(2)) {
                Ok(_) => {
                    log_line(&app_health, &format!("Backend health check PASSED on port {BACKEND_PORT} (attempt {})", attempt + 1));
                    let _ = app_health.emit("backend-status", "ready");
                    return;
                }
                Err(e) => {
                    log_line(&app_health, &format!("Backend health check: {e} (attempt {})", attempt + 1));
                }
            }
        }
        log_line(&app_health, &format!("Backend health check FAILED — not listening on port {BACKEND_PORT} after 30 attempts"));
        let _ = app_health.emit("backend-status", "error: backend not reachable");
    });

    Ok(format!("Backend starting on port 10742"))
}
