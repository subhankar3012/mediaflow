import shutil
import subprocess
from typing import Dict, Any

def get_ytdlp_version() -> str:
    try:
        import yt_dlp.version
        return getattr(yt_dlp.version, "__version__", getattr(yt_dlp, "__version__", "unknown"))
    except ImportError:
        return "not installed"

def get_binary_version(binary_name: str) -> str:
    path = shutil.which(binary_name)
    if not path:
        return "not found"
    try:
        flag = "-version" if binary_name in ("ffmpeg", "ffprobe") else "--version"
        res = subprocess.run([path, flag], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            first_line = res.stdout.splitlines()[0] if res.stdout else "available"
            return first_line.strip()
        return "error checking version"
    except Exception as e:
        return f"error: {str(e)}"

def check_system_binaries() -> Dict[str, Any]:
    return {
        "ytdlp": get_ytdlp_version(),
        "ffmpeg": get_binary_version("ffmpeg"),
        "ffprobe": get_binary_version("ffprobe"),
        "node": shutil.which("node") or shutil.which("nodejs") or "not found",
        "node_version": get_binary_version("node") if shutil.which("node") else "not found",
        "deno": shutil.which("deno") or "not found",
        "deno_version": get_binary_version("deno") if shutil.which("deno") else "not found",
    }
