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
    details: Option<Value>,
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
        details: None,
    });
}

fn checked_cancel(state: &SkillJobState) -> Result<(), String> {
    if state.cancel.load(Ordering::SeqCst) {
        Err("Video job cancelled".into())
    } else {
        Ok(())
    }
}

pub(crate) fn configure_process(command: &mut Command) {
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

pub(crate) fn stop_process(child: &mut Child) {
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
        "source" => {
            let count = value["sceneCount"].as_u64().unwrap_or(1).max(1);
            let completed = value["completedScenes"].as_u64().unwrap_or(0).min(count);
            20 + (40 * completed / count) as u32
        }
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
                    details: Some(value.clone()),
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

fn generate_image(
    app: &AppHandle,
    request: Value,
    key: String,
    channel: &Channel<SkillJobProgress>,
) -> Result<Value, String> {
    use base64::Engine;
    if key.trim().is_empty() {
        return Err("Enter an OpenAI image key or unlock the saved OpenAI credential".into());
    }
    let data = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let state = app.state::<SkillJobState>();
    // Serialize only public request fields; credentials are never written.
    let safe = json!({"model":request["model"],"prompt":request["prompt"],"size":request["size"],"quality":request["quality"]});
    use sha2::{Digest, Sha256};
    let identity = format!(
        "{:x}",
        Sha256::digest(serde_json::to_vec(&safe).map_err(|e| e.to_string())?)
    );
    let job = data.join("asset-jobs").join(format!("image-{identity}"));
    fs::create_dir_all(&job).map_err(|e| e.to_string())?;
    let payload = job.join("image-request.json");
    fs::write(
        &payload,
        serde_json::to_vec(&safe).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;
    let uv = ensure_uv(&data, &job, channel, &state)?;
    let runner = app
        .path()
        .resolve(
            "video-tools/generate_image_asset.py",
            BaseDirectory::Resource,
        )
        .map_err(|e| e.to_string())?;
    let mut command = Command::new(uv);
    command
        .args(["run", "--no-project", "--python", "3.12", "python"])
        .arg(runner)
        .arg(payload)
        .arg("--out")
        .arg(job.join("output"))
        .env("UV_PYTHON_INSTALL_DIR", data.join("video-runtime/python"))
        .env("UV_CACHE_DIR", data.join("video-runtime/uv-cache"))
        .env("PYTHONUTF8", "1")
        .env("PYTHONIOENCODING", "utf-8")
        .env("PYTHONDONTWRITEBYTECODE", "1")
        .env("OPENAI_API_KEY", key);
    let stdout = execute(&mut command, &job, "image-generation", channel, &state)?;
    checked_cancel(&state)?;
    let mut result: Value = serde_json::from_slice(&fs::read(stdout).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;
    if result["ready"] != true {
        return Err("Image generation did not complete".into());
    }
    let image = job.join("output/image.png");
    let metadata = fs::metadata(&image).map_err(|e| e.to_string())?;
    if metadata.len() > 22_000_000 {
        return Err("Generated image exceeds the upload limit".into());
    }
    let bytes = fs::read(image).map_err(|e| e.to_string())?;
    result["dataBase64"] = json!(base64::engine::general_purpose::STANDARD.encode(bytes));
    Ok(result)
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
        .env("SKILL_BANK_AVATAR_HOME", data.join("avatar"))
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

// This fallback keeps first-use hardware detection network-free on hosts
// without Python. Accepted installation may then provision private Python.
fn native_avatar_offer(app: &AppHandle, allow_restricted: bool) -> Result<Value, String> {
    use sha2::{Digest, Sha256};
    fn canonical(value: &Value) -> String {
        match value {
            Value::Object(map) => {
                let mut keys: Vec<_> = map.keys().collect();
                keys.sort();
                format!(
                    "{{{}}}",
                    keys.iter()
                        .map(|key| format!(
                            "{}:{}",
                            serde_json::to_string(key).unwrap(),
                            canonical(&map[*key])
                        ))
                        .collect::<Vec<_>>()
                        .join(",")
                )
            }
            Value::Array(items) => format!(
                "[{}]",
                items.iter().map(canonical).collect::<Vec<_>>().join(",")
            ),
            _ => serde_json::to_string(value).unwrap(),
        }
    }
    fn inspect(binary: &str, args: &[&str]) -> Option<String> {
        let mut command = Command::new(binary);
        configure_process(&mut command);
        command
            .args(args)
            .stdout(Stdio::piped())
            .stderr(Stdio::null());
        let mut child = command.spawn().ok()?;
        let deadline = Instant::now() + Duration::from_secs(10);
        loop {
            match child.try_wait() {
                Ok(Some(status)) if status.success() => {
                    return child
                        .wait_with_output()
                        .ok()
                        .and_then(|output| String::from_utf8(output.stdout).ok())
                }
                Ok(Some(_)) => return None,
                Ok(None) if Instant::now() < deadline => thread::sleep(Duration::from_millis(50)),
                _ => {
                    stop_process(&mut child);
                    return None;
                }
            }
        }
    }
    let file = app
        .path()
        .resolve("video-tools/avatar_models.json", BaseDirectory::Resource)
        .map_err(|e| e.to_string())?;
    let config: Value = serde_json::from_slice(&fs::read(file).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;
    let os = if cfg!(target_os = "windows") {
        "Windows"
    } else if cfg!(target_os = "macos") {
        "Darwin"
    } else {
        "Linux"
    };
    let arch = if cfg!(target_arch = "x86_64") {
        "x64"
    } else if cfg!(target_arch = "aarch64") {
        "arm64"
    } else {
        std::env::consts::ARCH
    };
    let mut accel = json!({"kind":"cpu", "name":null, "memoryBytes":0, "source":"native"});
    if os == "Darwin" && arch == "arm64" {
        if let Some(bytes) = inspect("/usr/sbin/sysctl", &["-n", "hw.memsize"])
            .and_then(|text| text.trim().parse::<u64>().ok())
        {
            accel = json!({"kind":"mps","name":"Apple Silicon","memoryBytes":bytes,"source":"sysctl:hw.memsize"});
        }
    } else if os == "Linux" || os == "Windows" {
        if let Some(output) = inspect(
            "nvidia-smi",
            &[
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader,nounits",
            ],
        ) {
            for (index, line) in output.lines().enumerate() {
                let parts: Vec<_> = line.rsplitn(3, ',').map(str::trim).collect();
                if parts.len() == 3 {
                    if let Ok(mib) = parts[1].parse::<u64>() {
                        let bytes = mib.saturating_mul(1048576);
                        if bytes > accel["memoryBytes"].as_u64().unwrap_or(0) {
                            accel = json!({"kind":"cuda","name":parts[2],"memoryBytes":bytes,"source":"nvidia-smi","driverVersion":parts[0],"deviceIndex":index});
                        }
                    }
                }
            }
        }
        if accel["kind"] == "cpu" && os == "Linux" && Path::new("/dev/kfd").exists() {
            accel["kind"] = json!("rocm");
        }
    }
    let kind = accel["kind"].as_str().unwrap_or("cpu");
    let memory = accel["memoryBytes"].as_u64().unwrap_or(0);
    let threshold = config["thresholds"][format!("{kind}Bytes")].as_u64();
    let mac_supported = os != "Darwin"
        || inspect("/usr/bin/sw_vers", &["-productVersion"])
            .and_then(|text| text.trim().split('.').next()?.parse::<u32>().ok())
            .is_some_and(|major| major >= 14);
    let platform_ok = (((os == "Windows" || os == "Linux") && arch == "x64")
        || (os == "Darwin" && arch == "arm64"))
        && mac_supported;
    let mut candidates = Vec::new();
    if platform_ok && threshold.is_some_and(|minimum| memory >= minimum) {
        for row in config["backends"]
            .as_array()
            .ok_or("Invalid presenter manifest")?
        {
            let minimum = row["minAccelMemoryBytes"]
                .as_u64()
                .or_else(|| row["minAccelMemoryBytes"][kind].as_u64())
                .unwrap_or(u64::MAX);
            if (row["licenseClass"] != "permissive"
                && !(allow_restricted && row["licenseClass"] == "restricted"))
                || memory < minimum
                || !row["accel"]
                    .as_array()
                    .is_some_and(|values| values.contains(&json!(kind)))
            {
                continue;
            }
            let mut offer = row.clone();
            offer["consentToken"] =
                json!(format!("{:x}", Sha256::digest(canonical(row).as_bytes())));
            offer["dependencyDownloads"] = json!("Private Python and inference packages are additional downloads within the disk allowance");
            candidates.push(offer);
        }
    }
    candidates.sort_by_key(|row| {
        (
            row["id"] != config["defaults"][kind],
            std::cmp::Reverse(row["qualityTier"].as_u64().unwrap_or(0)),
            row["downloadBytes"].as_u64().unwrap_or(0),
        )
    });
    let reason = if !platform_ok {
        format!("unsupported-platform:{os}/{arch}")
    } else if threshold.is_none() {
        format!("unsupported-accelerator:{kind}")
    } else if memory < threshold.unwrap() {
        format!("insufficient-memory:{kind}")
    } else if candidates.is_empty() {
        format!("no-compatible-backend:{kind}")
    } else {
        "eligible".into()
    };
    Ok(
        json!({"ready":false,"route":"avatar-video","installedBackends":[],"missing":["python"],"capability":{"os":os,"arch":arch,"eligible":!candidates.is_empty(),"reason":reason,"thresholdBytes":threshold,"accelerator":accel},"consent":{"phase":"consent-required","candidates":candidates}}),
    )
}

fn avatar_operation(
    app: &AppHandle,
    channel: &Channel<SkillJobProgress>,
    backend: Option<String>,
    token: Option<String>,
    allow_restricted: bool,
) -> Result<Value, String> {
    let data = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let state = app.state::<SkillJobState>();
    let runner = app
        .path()
        .resolve("video-tools/avatar_ensure.py", BaseDirectory::Resource)
        .map_err(|e| e.to_string())?;
    let mut candidates: Vec<(PathBuf, Vec<String>)> = Vec::new();
    // Reuse an installed private interpreter, then inspect system interpreters.
    // A hardware check must never bootstrap uv, Python, packages, or models.
    for root in [
        data.join("video-runtime/python"),
        data.join("avatar/python"),
    ] {
        if let Ok(entries) = fs::read_dir(root) {
            for entry in entries.flatten() {
                for suffix in ["bin/python3", "python.exe"] {
                    let python = entry.path().join(suffix);
                    if python.is_file() {
                        candidates.push((python, Vec::new()));
                    }
                }
            }
        }
    }
    #[cfg(windows)]
    candidates.push((PathBuf::from("py.exe"), vec!["-3".into()]));
    candidates.push((PathBuf::from("python3"), Vec::new()));
    candidates.push((PathBuf::from("python"), Vec::new()));
    let mut selected = None;
    for (binary, prefix) in candidates {
        checked_cancel(&state)?;
        let mut command = Command::new(&binary);
        configure_process(&mut command);
        command
            .args(&prefix)
            .args([
                "-c",
                "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)",
            ])
            .stdout(Stdio::null())
            .stderr(Stdio::null());
        if let Ok(mut child) = command.spawn() {
            let deadline = Instant::now() + Duration::from_secs(5);
            loop {
                match child.try_wait() {
                    Ok(Some(status)) => {
                        if status.success() {
                            selected = Some((binary.clone(), prefix.clone()));
                        }
                        break;
                    }
                    Ok(None) if Instant::now() < deadline => {
                        thread::sleep(Duration::from_millis(50))
                    }
                    _ => {
                        stop_process(&mut child);
                        break;
                    }
                }
            }
        }
        if selected.is_some() {
            break;
        }
    }
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|e| e.to_string())?
        .as_millis();
    let directory = data.join("avatar-probes").join(format!("{timestamp}"));
    fs::create_dir_all(&directory).map_err(|e| e.to_string())?;
    let (binary, prefix) = if let Some(selected) = selected {
        selected
    } else if token.is_some() {
        let offer = native_avatar_offer(app, allow_restricted)?;
        let accepted = offer["consent"]["candidates"]
            .as_array()
            .is_some_and(|rows| {
                rows.iter().any(|row| {
                    row["id"].as_str() == backend.as_deref()
                        && row["consentToken"].as_str() == token.as_deref()
                })
            });
        if !accepted {
            return Err("The selected presenter offer changed or is incompatible; check this computer and accept the current offer".into());
        }
        let uv = ensure_uv(&data, &directory, channel, &state)?;
        (
            uv,
            vec![
                "run".into(),
                "--no-project".into(),
                "--python".into(),
                "3.12".into(),
                "python".into(),
            ],
        )
    } else {
        return native_avatar_offer(app, allow_restricted);
    };
    let mut command = Command::new(binary);
    command
        .env("UV_PYTHON_INSTALL_DIR", data.join("video-runtime/python"))
        .env("UV_CACHE_DIR", data.join("video-runtime/uv-cache"));
    command
        .args(prefix)
        .arg(runner)
        .arg("avatar-video")
        .arg("--runtime-dir")
        .arg(data.join("avatar"))
        .env("PYTHONUTF8", "1")
        .env("PYTHONIOENCODING", "utf-8")
        .env("PYTHONDONTWRITEBYTECODE", "1");
    if let Some(backend) = backend {
        command.args(["--backend", &backend]);
    }
    if let Some(token) = token {
        command.args(["--accept", "--consent-token", &token]);
    } else {
        command.arg("--check");
    }
    if allow_restricted {
        command.arg("--allow-restricted");
    }
    let stdout = execute(&mut command, &directory, "avatar-setup", channel, &state)?;
    serde_json::from_slice(&fs::read(stdout).map_err(|e| e.to_string())?).map_err(|e| e.to_string())
}

fn review_captions(
    app: &AppHandle,
    directory: String,
    edits: Option<Value>,
    expected_caption_sha: Option<String>,
    channel: &Channel<SkillJobProgress>,
) -> Result<Value, String> {
    let data = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let projects = data
        .join("projects")
        .canonicalize()
        .map_err(|_| "No video project directory exists yet".to_string())?;
    let project = PathBuf::from(directory)
        .canonicalize()
        .map_err(|e| format!("Could not open the video project: {e}"))?;
    if !project.starts_with(&projects) || !project.is_dir() {
        return Err("Caption review is limited to projects created by this app".into());
    }
    let tool = app
        .path()
        .resolve("video-tools/review_captions.py", BaseDirectory::Resource)
        .map_err(|e| e.to_string())?;
    if !tool.is_file() {
        return Err("Bundled caption review tool is missing".into());
    }
    let work = project.join("logs/caption-review");
    fs::create_dir_all(&work).map_err(|e| e.to_string())?;
    let data_file = if let Some(edits) = edits {
        let expected =
            expected_caption_sha.ok_or("Saving captions requires the version that was opened")?;
        let payload = work.join(format!(
            "draft-{}.json",
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .map_err(|e| e.to_string())?
                .as_micros()
        ));
        fs::write(
            &payload,
            serde_json::to_vec(&edits).map_err(|e| e.to_string())?,
        )
        .map_err(|e| e.to_string())?;
        Some((payload, expected))
    } else {
        if expected_caption_sha.is_some() {
            return Err("Caption version was supplied without edits".into());
        }
        None
    };
    let state = app.state::<SkillJobState>();
    checked_cancel(&state)?;
    let uv = ensure_uv(&data, &work, channel, &state)?;
    let mut command = Command::new(uv);
    command
        .current_dir(&work)
        .args(["run", "--no-project", "--python", "3.12", "python"])
        .arg(tool)
        .arg(&project)
        .env("UV_PYTHON_INSTALL_DIR", data.join("video-runtime/python"))
        .env("SKILL_BANK_AVATAR_HOME", data.join("avatar"))
        .env("UV_CACHE_DIR", data.join("video-runtime/uv-cache"))
        .env("PYTHONIOENCODING", "utf-8")
        .env("PYTHONUTF8", "1")
        .env("PYTHONDONTWRITEBYTECODE", "1");
    if let Some((path, expected)) = data_file.as_ref() {
        command
            .arg("--edits")
            .arg(path)
            .arg("--expected-caption-sha")
            .arg(expected);
    }
    let stdout = execute(&mut command, &work, "caption-review", channel, &state)?;
    if let Some((path, _)) = data_file {
        let _ = fs::remove_file(path);
    }
    let result: Value = serde_json::from_slice(&fs::read(stdout).map_err(|e| e.to_string())?)
        .map_err(|e| format!("Caption review tool returned invalid JSON: {e}"))?;
    if result["ready"] != true {
        return Err(result["error"]
            .as_str()
            .unwrap_or("Caption review did not finish")
            .into());
    }
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

#[tauri::command(async)]
pub async fn video_skill_generate_image(
    app: AppHandle,
    request: Value,
    key: String,
    on_progress: Channel<SkillJobProgress>,
) -> Result<Value, String> {
    let state = app.state::<SkillJobState>();
    if state
        .running
        .compare_exchange(false, true, Ordering::SeqCst, Ordering::SeqCst)
        .is_err()
    {
        return Err("Another video skill operation is running".into());
    }
    state.cancel.store(false, Ordering::SeqCst);
    state.percent.store(0, Ordering::Relaxed);
    let worker = app.clone();
    let result = tauri::async_runtime::spawn_blocking(move || {
        generate_image(&worker, request, key, &on_progress)
    })
    .await;
    app.state::<SkillJobState>()
        .running
        .store(false, Ordering::SeqCst);
    result.map_err(|e| e.to_string())?
}

#[tauri::command(async)]
pub async fn video_skill_avatar_probe(
    app: AppHandle,
    allow_restricted: Option<bool>,
    on_progress: Channel<SkillJobProgress>,
) -> Result<Value, String> {
    let state = app.state::<SkillJobState>();
    if state
        .running
        .compare_exchange(false, true, Ordering::SeqCst, Ordering::SeqCst)
        .is_err()
    {
        return Err("Another video skill operation is running".into());
    }
    state.cancel.store(false, Ordering::SeqCst);
    state.percent.store(0, Ordering::Relaxed);
    let worker = app.clone();
    let result = tauri::async_runtime::spawn_blocking(move || {
        avatar_operation(
            &worker,
            &on_progress,
            None,
            None,
            allow_restricted.unwrap_or(false),
        )
    })
    .await;
    app.state::<SkillJobState>()
        .running
        .store(false, Ordering::SeqCst);
    result.map_err(|e| e.to_string())?
}

#[tauri::command(async)]
pub async fn video_skill_avatar_install(
    app: AppHandle,
    backend: String,
    consent_token: String,
    accept: bool,
    allow_restricted: bool,
    on_progress: Channel<SkillJobProgress>,
) -> Result<Value, String> {
    if !accept || backend.is_empty() || consent_token.is_empty() {
        return Err("Model installation requires explicit acceptance of the displayed licences and downloads".into());
    }
    let state = app.state::<SkillJobState>();
    if state
        .running
        .compare_exchange(false, true, Ordering::SeqCst, Ordering::SeqCst)
        .is_err()
    {
        return Err("Another video skill operation is running".into());
    }
    state.cancel.store(false, Ordering::SeqCst);
    state.percent.store(0, Ordering::Relaxed);
    let worker = app.clone();
    let result = tauri::async_runtime::spawn_blocking(move || {
        avatar_operation(
            &worker,
            &on_progress,
            Some(backend),
            Some(consent_token),
            allow_restricted,
        )
    })
    .await;
    app.state::<SkillJobState>()
        .running
        .store(false, Ordering::SeqCst);
    result.map_err(|e| e.to_string())?
}

#[tauri::command(async)]
pub async fn video_skill_caption_review(
    app: AppHandle,
    directory: String,
    edits: Option<Value>,
    expected_caption_sha: Option<String>,
    on_progress: Channel<SkillJobProgress>,
) -> Result<Value, String> {
    let state = app.state::<SkillJobState>();
    if state
        .running
        .compare_exchange(false, true, Ordering::SeqCst, Ordering::SeqCst)
        .is_err()
    {
        return Err("Another video job is running".into());
    }
    state.cancel.store(false, Ordering::SeqCst);
    state.percent.store(0, Ordering::Relaxed);
    let worker = app.clone();
    let result = tauri::async_runtime::spawn_blocking(move || {
        review_captions(
            &worker,
            directory,
            edits,
            expected_caption_sha,
            &on_progress,
        )
    })
    .await;
    app.state::<SkillJobState>()
        .running
        .store(false, Ordering::SeqCst);
    result.map_err(|e| e.to_string())?
}
