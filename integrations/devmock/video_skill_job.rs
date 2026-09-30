//! Host the bundled video job tools in writable app data on all desktop targets.

use serde::Serialize;
use serde_json::{json, Value};
use std::{
    fs::{self, File},
    io::{BufRead, BufReader, Write},
    path::{Path, PathBuf},
    process::{Child, Command, Stdio},
    sync::{
        atomic::{AtomicBool, AtomicU32, AtomicU64, Ordering},
        Arc,
    },
    thread,
    time::{Duration, Instant, SystemTime, UNIX_EPOCH},
};
use tauri::{ipc::Channel, path::BaseDirectory, AppHandle, Manager};

#[derive(Default)]
pub struct SkillJobState {
    running: AtomicBool,
    cancel: AtomicBool,
    next_id: AtomicU64,
    percent: Arc<AtomicU32>,
}

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SkillJobProgress {
    phase: String,
    percent: u32,
    message: String,
    artifact: Option<String>,
}

fn report(
    channel: &Channel<SkillJobProgress>,
    phase: &str,
    percent: u32,
    message: impl Into<String>,
    artifact: Option<&Path>,
) {
    let _ = channel.send(SkillJobProgress {
        phase: phase.into(),
        percent,
        message: message.into(),
        artifact: artifact.map(|path| path.to_string_lossy().into_owned()),
    });
}

fn checked_cancel(state: &SkillJobState) -> Result<(), String> {
    if state.cancel.load(Ordering::SeqCst) {
        Err("Video job cancelled".into())
    } else {
        Ok(())
    }
}

fn configure_process(command: &mut Command) {
    command.stdin(Stdio::null());
    #[cfg(unix)]
    {
        use std::os::unix::process::CommandExt;
        command.process_group(0);
    }
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        command.creation_flags(0x08000000); // CREATE_NO_WINDOW
    }
}

fn stop_process(child: &mut Child) {
    #[cfg(windows)]
    {
        let mut command = Command::new("taskkill.exe");
        configure_process(&mut command);
        let _ = command
            .args(["/T", "/F", "/PID", &child.id().to_string()])
            .status();
        let _ = child.kill();
    }
    #[cfg(unix)]
    {
        // The Python runner handles SIGTERM and stops its renderer process group.
        unsafe {
            libc::kill(-(child.id() as i32), libc::SIGTERM);
        }
        let deadline = Instant::now() + Duration::from_secs(10);
        while Instant::now() < deadline {
            if child.try_wait().ok().flatten().is_some() {
                return;
            }
            thread::sleep(Duration::from_millis(100));
        }
        unsafe {
            libc::kill(-(child.id() as i32), libc::SIGKILL);
        }
        let _ = child.kill();
    }
    let _ = child.wait();
}

fn phase_percent(value: &Value) -> u32 {
    match value["phase"].as_str().unwrap_or("command") {
        "import" => 8,
        "validate" => 15,
        "visuals" => 20,
        "render" => {
            if value.get("durationSec").is_some() {
                70
            } else {
                25
            }
        }
        "assemble" => 72,
        "audio" => 78,
        "subtitles" | "transcribe" => 88,
        "complete" => {
            if value.get("reviewRequired").is_some() {
                98
            } else {
                80
            }
        }
        _ => 5,
    }
}

fn execute(
    command: &mut Command,
    directory: &Path,
    label: &str,
    channel: &Channel<SkillJobProgress>,
    state: &SkillJobState,
) -> Result<PathBuf, String> {
    checked_cancel(state)?;
    configure_process(command);
    let stdout_path = directory.join(format!("{label}.stdout.log"));
    let stderr_path = directory.join(format!("{label}.stderr.log"));
    let stdout = File::create(&stdout_path).map_err(|e| e.to_string())?;
    let mut stderr_log = File::create(stderr_path).map_err(|e| e.to_string())?;
    command.stdout(Stdio::from(stdout)).stderr(Stdio::piped());
    let mut child = command
        .spawn()
        .map_err(|e| format!("Could not start {label}: {e}"))?;
    let stderr = child
        .stderr
        .take()
        .ok_or("Could not capture job progress")?;
    let progress_channel = channel.clone();
    let progress_percent = state.percent.clone();
    let reader = thread::spawn(move || {
        let mut percent = progress_percent.load(Ordering::Relaxed).max(2);
        for line in BufReader::new(stderr).lines() {
            let Ok(line) = line else {
                break;
            };
            let _ = writeln!(stderr_log, "{line}");
            let value = serde_json::from_str::<Value>(&line).ok();
            if let Some(value) = value {
                percent = percent.max(phase_percent(&value));
                progress_percent.store(percent, Ordering::Relaxed);
                let _ = progress_channel.send(SkillJobProgress {
                    phase: value["phase"].as_str().unwrap_or("command").into(),
                    percent,
                    message: value["message"].as_str().unwrap_or(&line).into(),
                    artifact: value["artifact"]
                        .as_str()
                        .filter(|path| Path::new(path).exists())
                        .map(str::to_owned),
                });
            } else if !line.trim().is_empty() {
                report(&progress_channel, "command", percent, line, None);
            }
        }
    });
    let mut last_update = Instant::now();
    let result = loop {
        if state.cancel.load(Ordering::SeqCst) {
            stop_process(&mut child);
            break Err("Video job cancelled".into());
        }
        match child.try_wait() {
            Ok(Some(status)) if status.success() => break Ok(stdout_path.clone()),
            Ok(Some(status)) => {
                let detail = fs::read(&stdout_path)
                    .ok()
                    .and_then(|bytes| serde_json::from_slice::<Value>(&bytes).ok())
                    .and_then(|value| value["error"].as_str().map(str::to_owned))
                    .unwrap_or_default();
                break Err(format!(
                    "{label} failed ({status}): {detail}; logs: {}",
                    directory.display()
                ));
            }
            Err(error) => {
                stop_process(&mut child);
                break Err(error.to_string());
            }
            Ok(None) => {
                if last_update.elapsed() >= Duration::from_secs(10) {
                    report(
                        channel,
                        "command",
                        state.percent.load(Ordering::Relaxed),
                        format!("Still running {label}"),
                        None,
                    );
                    last_update = Instant::now();
                }
                thread::sleep(Duration::from_millis(100));
            }
        }
    };
    let _ = reader.join();
    result
}

fn ensure_uv(
    data: &Path,
    job: &Path,
    channel: &Channel<SkillJobProgress>,
    state: &SkillJobState,
) -> Result<PathBuf, String> {
    let name = if cfg!(windows) { "uv.exe" } else { "uv" };
    let tools = data.join("video-runtime/python-tools");
    fs::create_dir_all(&tools).map_err(|e| e.to_string())?;
    let target = tools.join(name);
    for candidate in [Some(target.clone()), crate::ffmpeg::which(name)]
        .into_iter()
        .flatten()
    {
        let mut command = Command::new(&candidate);
        configure_process(&mut command);
        if command
            .arg("--version")
            .output()
            .is_ok_and(|output| output.status.success())
        {
            return Ok(candidate);
        }
    }
    checked_cancel(state)?;
    report(
        channel,
        "setup",
        1,
        "Installing private Python manager",
        None,
    );
    let extension = if cfg!(windows) { "ps1" } else { "sh" };
    let installer = tools.join(format!("uv-install.{extension}"));
    let client = reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(60))
        .build()
        .map_err(|e| e.to_string())?;
    let bytes = client
        .get(format!("https://astral.sh/uv/install.{extension}"))
        .send()
        .and_then(reqwest::blocking::Response::error_for_status)
        .map_err(|e| format!("Could not download the Python manager: {e}"))?
        .bytes()
        .map_err(|e| e.to_string())?;
    checked_cancel(state)?;
    fs::write(&installer, bytes).map_err(|e| e.to_string())?;
    let mut command;
    if cfg!(windows) {
        command = Command::new("powershell.exe");
        command
            .args(["-NoProfile", "-ExecutionPolicy", "Bypass", "-File"])
            .arg(&installer);
    } else {
        command = Command::new("sh");
        command.arg(&installer);
    }
    command
        .env("UV_INSTALL_DIR", &tools)
        .env("UV_NO_MODIFY_PATH", "1");
    execute(&mut command, job, "python-manager-install", channel, state)?;
    if !target.is_file() {
        return Err("Python manager installation did not verify".into());
    }
    Ok(target)
}

fn run(
    app: &AppHandle,
    request: Value,
    channel: &Channel<SkillJobProgress>,
) -> Result<Value, String> {
    if !request.is_object() || !request["scenes"].is_array() {
        return Err("Video request needs a storyboard".into());
    }
    let data = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let state = app.state::<SkillJobState>();
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|e| e.to_string())?
        .as_millis();
    let sequence = state.next_id.fetch_add(1, Ordering::SeqCst);
    let job = data
        .join("projects")
        .join(format!("video-skill-{timestamp}-{sequence}"));
    fs::create_dir_all(&job).map_err(|e| e.to_string())?;
    report(channel, "import", 0, "Created video workspace", Some(&job));
    let runner = app
        .path()
        .resolve(
            "video-tools/run_desktop_video_job.py",
            BaseDirectory::Resource,
        )
        .map_err(|e| e.to_string())?;
    if !runner.is_file() {
        return Err("Bundled video job tools are missing".into());
    }
    let payload = job.join("desktop-request.json");
    fs::write(
        &payload,
        serde_json::to_vec(
            &json!({"schemaVersion":1,"request":request,"runtimeDir":data.join("video-runtime")}),
        )
        .map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;
    let uv = ensure_uv(&data, &job, channel, &state)?;
    checked_cancel(&state)?;
    report(
        channel,
        "setup",
        2,
        "Preparing Python 3.12 and video tools",
        None,
    );
    let mut command = Command::new(uv);
    command
        .current_dir(&job)
        .args(["run", "--no-project", "--python", "3.12", "python"])
        .arg(runner)
        .arg(&payload)
        .arg("--workspace")
        .arg(job.join("project"))
        .env("UV_PYTHON_INSTALL_DIR", data.join("video-runtime/python"))
        .env("UV_CACHE_DIR", data.join("video-runtime/uv-cache"))
        .env("PYTHONIOENCODING", "utf-8")
        .env("PYTHONUTF8", "1")
        .env("PYTHONDONTWRITEBYTECODE", "1");
    let path = std::env::var_os("PATH").unwrap_or_default();
    let media_directories = [
        crate::ffmpeg::find(&data),
        crate::ffmpeg::find_ffprobe(&data),
    ]
    .into_iter()
    .flatten()
    .filter_map(|(binary, _)| binary.parent().map(Path::to_path_buf))
    .collect::<Vec<_>>();
    if let Ok(path) = std::env::join_paths(
        media_directories
            .into_iter()
            .chain(std::env::split_paths(&path)),
    ) {
        command.env("PATH", path);
    }
    let stdout = execute(&mut command, &job, "video-job", channel, &state)?;
    let result: Value = serde_json::from_slice(&fs::read(stdout).map_err(|e| e.to_string())?)
        .map_err(|e| {
            format!(
                "Video runner returned invalid JSON: {e}; logs: {}",
                job.display()
            )
        })?;
    if result["ready"] != true {
        return Err(result["error"]
            .as_str()
            .unwrap_or("Video job did not finish")
            .into());
    }
    report(
        channel,
        "complete",
        100,
        if result["reviewRequired"] == true {
            "Video project ready for caption review"
        } else {
            "Video project verified"
        },
        result["video"].as_str().map(Path::new),
    );
    Ok(result)
}

#[tauri::command(async)]
pub async fn video_skill_render(
    app: AppHandle,
    request: Value,
    on_progress: Channel<SkillJobProgress>,
) -> Result<Value, String> {
    let state = app.state::<SkillJobState>();
    if state
        .running
        .compare_exchange(false, true, Ordering::SeqCst, Ordering::SeqCst)
        .is_err()
    {
        return Err("Another video skill job is running".into());
    }
    state.cancel.store(false, Ordering::SeqCst);
    state.percent.store(0, Ordering::Relaxed);
    let worker = app.clone();
    let result =
        tauri::async_runtime::spawn_blocking(move || run(&worker, request, &on_progress)).await;
    app.state::<SkillJobState>()
        .running
        .store(false, Ordering::SeqCst);
    result.map_err(|e| e.to_string())?
}

#[tauri::command]
pub fn video_skill_cancel(state: tauri::State<'_, SkillJobState>) {
    state.cancel.store(true, Ordering::SeqCst);
}
