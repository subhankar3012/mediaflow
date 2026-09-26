import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from app.config import settings
from app.schemas.format import NormalizedFormat, MediaType, GalleryItem
from app.utils.logger import logger

class YtDlpError(Exception):
    def __init__(self, message: str, code: str = "DOWNLOAD_ERROR"):
        super().__init__(message)
        self.code = code
        self.message = message

class YtDlpService:
    """
    Encapsulates yt-dlp Python API.
    Isolates extraction, normalization, and downloading logic.
    """

    @staticmethod
    def _configure_js_runtime(ydl_opts: Dict[str, Any]):
        """Configures the best available JavaScript runtime for solving YouTube EJS challenges."""
        deno_path = shutil.which("deno")
        node_path = shutil.which("node") or shutil.which("nodejs")
        if not deno_path:
            for cand in ["/usr/local/bin/deno", "/usr/bin/deno"]:
                if os.path.exists(cand):
                    deno_path = cand
                    break
        if not node_path:
            for cand in ["/usr/bin/node", "/usr/local/bin/node", "/usr/bin/nodejs"]:
                if os.path.exists(cand):
                    node_path = cand
                    break
        runtimes: Dict[str, Any] = {}
        if deno_path:
            runtimes["deno"] = {"path": deno_path}
        else:
            runtimes["deno"] = {}
        if node_path:
            runtimes["node"] = {"path": node_path}
        ydl_opts["js_runtimes"] = runtimes

    @staticmethod
    def _sanitize_and_validate_cookies(raw_content: str) -> Optional[str]:
        """
        Sanitizes cookie content to ensure valid Netscape format.
        Handles base64, literal \\n/\\t escapes, and space-to-tab repair.
        Validates with MozillaCookieJar and returns a valid file path or None.
        """
        import base64
        import http.cookiejar

        raw_stripped = raw_content.strip()
        if not raw_stripped:
            return None

        # 1. Decode base64 if needed
        if raw_stripped.startswith("ey") or raw_stripped.startswith("I05ldHNjYXBl") or raw_stripped.startswith("IyBOZXRzY2FwZQ"):
            try:
                decoded = base64.b64decode(raw_stripped).decode("utf-8", errors="ignore")
                if "Netscape" in decoded or ".youtube.com" in decoded:
                    raw_content = decoded
            except Exception:
                pass

        # 2. Unescape literal escaped newlines or tabs
        if r"\n" in raw_content and "\n" not in raw_content:
            raw_content = raw_content.replace(r"\n", "\n")
        if r"\t" in raw_content:
            raw_content = raw_content.replace(r"\t", "\t")

        lines = raw_content.splitlines()
        cleaned_lines = []
        has_header = False

        for line in lines:
            line_s = line.strip()
            if not line_s:
                continue
            if line_s.startswith("#"):
                if "Netscape HTTP Cookie File" in line_s:
                    has_header = True
                cleaned_lines.append(line_s)
                continue

            # If line already has tabs, check token count
            if "\t" in line:
                parts = line.split("\t")
                if len(parts) >= 7:
                    cleaned_lines.append("\t".join(p.strip() for p in parts))
                    continue

            # If line has spaces instead of tabs
            parts = line.split()
            if len(parts) >= 7 and parts[1].upper() in ("TRUE", "FALSE") and parts[3].upper() in ("TRUE", "FALSE"):
                normalized = "\t".join(parts[:6] + [" ".join(parts[6:])])
                cleaned_lines.append(normalized)

        if not has_header:
            cleaned_lines.insert(0, "# Netscape HTTP Cookie File")
            cleaned_lines.insert(1, "# https://curl.haxx.se/rfc/cookie_spec.html")

        cookie_text = "\n".join(cleaned_lines) + "\n"
        cookie_path = os.path.join(tempfile.gettempdir(), "ytdlp_cookies.txt")

        try:
            with open(cookie_path, "w", encoding="utf-8") as f:
                f.write(cookie_text)

            # Validate with MozillaCookieJar
            jar = http.cookiejar.MozillaCookieJar(cookie_path)
            jar.load(ignore_discard=True, ignore_expires=True)
            if len(jar) > 0:
                logger.info(f"Loaded and validated {len(jar)} cookies.")
                return cookie_path
            else:
                logger.warning("Cookie file parsed with 0 valid cookies.")
                return None
        except Exception as e:
            logger.warning(f"Failed to validate cookie file: {e}")
            return None

    _cached_cookie_url: Optional[str] = None
    _cached_cookie_path: Optional[str] = None
    _cached_cookie_fetch_time: float = 0.0

    @classmethod
    def _fetch_cookies_from_url(cls, url: str) -> Optional[str]:
        """Fetches remote cookies from a secret URL (Gist/Pastebin/S3) with 10-minute caching."""
        import time
        now = time.time()
        if cls._cached_cookie_path and cls._cached_cookie_url == url and (now - cls._cached_cookie_fetch_time < 600):
            if os.path.exists(cls._cached_cookie_path):
                return cls._cached_cookie_path

        try:
            import urllib.request
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode("utf-8", errors="ignore")
            path = cls._sanitize_and_validate_cookies(content)
            if path:
                cls._cached_cookie_url = url
                cls._cached_cookie_path = path
                cls._cached_cookie_fetch_time = now
                logger.info(f"Successfully fetched and validated cookies from YTDLP_COOKIES_URL: {url[:30]}...")
                return path
        except Exception as e:
            logger.warning(f"Failed to fetch cookies from YTDLP_COOKIES_URL: {e}")

        return cls._cached_cookie_path if (cls._cached_cookie_path and os.path.exists(cls._cached_cookie_path)) else None

    @classmethod
    def _get_cookiefile(cls) -> Optional[str]:
        """Resolves active cookies file from environment variable, explicit path, or default location."""
        # 1. Plaintext or base64 cookies provided via YTDLP_COOKIES environment variable
        if getattr(settings, "YTDLP_COOKIES", None) and settings.YTDLP_COOKIES.strip():
            path = cls._sanitize_and_validate_cookies(settings.YTDLP_COOKIES)
            if path:
                return path

        # 1.5 Remote URL for cookies (e.g. Secret GitHub Gist raw URL)
        if getattr(settings, "YTDLP_COOKIES_URL", None) and settings.YTDLP_COOKIES_URL.strip():
            path = cls._fetch_cookies_from_url(settings.YTDLP_COOKIES_URL.strip())
            if path:
                return path

        # 2. Explicit path specified via YTDLP_COOKIES_PATH
        if getattr(settings, "YTDLP_COOKIES_PATH", None) and settings.YTDLP_COOKIES_PATH:
            if os.path.exists(settings.YTDLP_COOKIES_PATH):
                return settings.YTDLP_COOKIES_PATH

        # 3. Default fallback paths
        default_paths = [
            os.path.join(os.getcwd(), "cookies.txt"),
            os.path.join(os.path.dirname(__file__), "..", "..", "cookies.txt"),
            "/tmp/downloader/cookies.txt",
        ]
        for p in default_paths:
            if os.path.exists(p) and os.path.getsize(p) > 0:
                return p

        return None

    @classmethod
    def _has_authenticated_youtube_cookies(cls) -> bool:
        """Checks if the cookies file contains actual logged-in YouTube session cookies (not guest tokens)."""
        cookiefile = cls._get_cookiefile()
        if not cookiefile or not os.path.exists(cookiefile):
            return False
        try:
            with open(cookiefile, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if "youtube.com" not in content.lower():
                return False
            # Valid signed-in account tokens
            auth_tokens = ["LOGIN_INFO", "SAPISID", "SSID", "HSID", "__Secure-3PSID", "__Secure-1PSID"]
            return any(tok in content for tok in auth_tokens)
        except Exception:
            return False

    @classmethod
    def get_cookies_status(cls) -> Dict[str, Any]:
        """Returns structured status of loaded cookies for health inspections."""
        cookiefile = cls._get_cookiefile()
        if not cookiefile:
            return {
                "loaded": False,
                "count": 0,
                "valid": False,
                "has_youtube": False,
                "has_youtube_authenticated": False,
                "has_instagram": False,
            }
        try:
            import http.cookiejar
            jar = http.cookiejar.MozillaCookieJar(cookiefile)
            jar.load(ignore_discard=True, ignore_expires=True)
            count = len(jar)
            return {
                "loaded": True,
                "count": count,
                "valid": count > 0,
                "has_youtube": cls._has_domain_cookies("youtube.com"),
                "has_youtube_authenticated": cls._has_authenticated_youtube_cookies(),
                "has_instagram": cls._has_domain_cookies("instagram.com"),
            }
        except Exception:
            return {
                "loaded": True,
                "count": 0,
                "valid": False,
                "has_youtube": cls._has_domain_cookies("youtube.com"),
                "has_youtube_authenticated": False,
                "has_instagram": cls._has_domain_cookies("instagram.com"),
            }

    @classmethod
    def _has_domain_cookies(cls, domain: str) -> bool:
        """Checks if the active cookies file contains cookies for a specific domain."""
        cookiefile = cls._get_cookiefile()
        if not cookiefile or not os.path.exists(cookiefile):
            return False
        try:
            with open(cookiefile, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return domain.lower() in content.lower()
        except Exception:
            return False

    @staticmethod
    def _format_bytes(size: Optional[int]) -> str:
        if not size or size <= 0:
            return "0 B"
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    @staticmethod
    def _format_speed(speed_bytes: Optional[float]) -> Optional[str]:
        if not speed_bytes or speed_bytes <= 0:
            return None
        return f"{YtDlpService._format_bytes(int(speed_bytes))}/s"

    @staticmethod
    def _format_eta(seconds: Optional[int]) -> Optional[str]:
        if seconds is None or seconds < 0:
            return None
        mins, secs = divmod(int(seconds), 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    @staticmethod
    def _select_best_thumbnail(info: Dict[str, Any]) -> Optional[str]:
        """
        Ranks available thumbnails to select the highest-quality appropriate thumbnail.
        Prioritizes (width * height), then preference score.
        """
        thumbnails = info.get("thumbnails")
        if not thumbnails:
            return info.get("thumbnail")

        def thumb_key(t: Dict[str, Any]):
            w = t.get("width") or 0
            h = t.get("height") or 0
            pref = t.get("preference") or 0
            url = t.get("url") or ""
            is_compat = 1 if (url.endswith(".jpg") or url.endswith(".jpeg") or url.endswith(".png")) else 0
            return (w * h, pref, is_compat)

        sorted_thumbs = sorted(thumbnails, key=thumb_key, reverse=True)
        for t in sorted_thumbs:
            u = t.get("url")
            if u and u.startswith("http"):
                return u
        return info.get("thumbnail")

    def normalize_format(self, raw_fmt: Dict[str, Any]) -> Optional[NormalizedFormat]:
        """Converts a raw yt-dlp format dictionary into a clean NormalizedFormat."""
        format_id = str(raw_fmt.get("format_id", ""))
        if not format_id:
            return None

        vcodec = raw_fmt.get("vcodec")
        acodec = raw_fmt.get("acodec")
        ext = raw_fmt.get("ext", "mp4")

        has_video = bool(vcodec and vcodec.lower() != "none")
        has_audio = bool(acodec and acodec.lower() != "none")

        if not has_video and not has_audio:
            return None

        if has_video and has_audio:
            media_type: MediaType = "video+audio"
        elif has_video:
            media_type = "video"
        else:
            media_type = "audio"

        width = raw_fmt.get("width")
        height = raw_fmt.get("height")
        fps = raw_fmt.get("fps")
        tbr = raw_fmt.get("tbr") or raw_fmt.get("vbr") or raw_fmt.get("abr")
        filesize = raw_fmt.get("filesize")
        filesize_approx = raw_fmt.get("filesize_approx")
        format_note = raw_fmt.get("format_note") or raw_fmt.get("resolution")

        return NormalizedFormat(
            format_id=format_id,
            type=media_type,
            container=ext,
            width=int(width) if width else None,
            height=int(height) if height else None,
            fps=float(fps) if fps else None,
            vcodec=vcodec if vcodec != "none" else None,
            acodec=acodec if acodec != "none" else None,
            bitrate=float(tbr) if tbr else None,
            has_audio=has_audio,
            has_video=has_video,
            filesize=filesize,
            filesize_approx=filesize_approx,
            format_note=str(format_note) if format_note else None
        )

    def _build_extract_opts(self, use_cookies: bool = True, is_youtube: bool = False) -> Dict[str, Any]:
        """Builds extraction options. Configures JS runtime and player client for solving YouTube challenges."""
        opts: Dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": False,
            "socket_timeout": 25,
            "no_color": True,
            "ignore_no_formats_error": True,
            "ignoreerrors": True,
        }

        # For YouTube:
        # - Unauthenticated: visionos player client extracts ALL resolution tiers without PO-token blockage
        # - Authenticated: use authed web clients (web_embedded, tv_downgraded, web)
        if is_youtube:
            if use_cookies:
                opts["extractor_args"] = {
                    "youtube": {
                        "player_client": ["web_embedded", "tv_downgraded", "web"]
                    }
                }
            else:
                opts["extractor_args"] = {
                    "youtube": {
                        "player_client": ["visionos"]
                    }
                }

        # Always configure JS runtime so yt-dlp can solve challenges on Linux/Docker
        self._configure_js_runtime(opts)

        if use_cookies:
            cookiefile = self._get_cookiefile()
            if cookiefile:
                opts["cookiefile"] = cookiefile

        # Proxy support
        if getattr(settings, "YTDLP_PROXY", None) and settings.YTDLP_PROXY.strip():
            opts["proxy"] = settings.YTDLP_PROXY.strip()

        return opts

    def extract_metadata(self, url: str) -> Dict[str, Any]:
        """
        Extracts metadata and formats without downloading media.
        Synchronous method intended to run within an executor.
        Supports single videos, audio, single photos, and multi-item carousels / stories.
        """
        import yt_dlp

        is_youtube = ("youtube.com" in url.lower() or "youtu.be" in url.lower())
        has_cookies = bool(self._get_cookiefile())
        has_auth_yt = self._has_authenticated_youtube_cookies()

        # For YouTube: public videos extract cleanly with Node/Deno JS solvers WITHOUT cookies.
        # Only use cookies on YouTube if genuine authenticated youtube.com cookies exist.
        if is_youtube:
            strategies = [False, True] if (has_cookies and has_auth_yt) else [False]
        else:
            strategies = [True, False] if has_cookies else [False]

        last_error = None
        best_result: Optional[Dict[str, Any]] = None
        best_video_count: int = 0

        for use_cookies in strategies:
            try:
                ydl_opts = self._build_extract_opts(use_cookies=use_cookies, is_youtube=is_youtube)
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if not info:
                        last_error = YtDlpError(f"Could not extract info for {url}", code="EXTRACTION_FAILED")
                        continue

                    # Check if this is a playlist / multi-item carousel / story
                    is_playlist = info.get("_type") == "playlist" and "entries" in info
                    raw_entries = [e for e in info.get("entries", []) if e] if is_playlist else []

                    # 1. Multi-item Carousel / Story Gallery
                    if is_playlist and len(raw_entries) > 1:
                        gallery_items: List[GalleryItem] = []
                        for idx, e in enumerate(raw_entries):
                            thumbs = e.get("thumbnails") or []
                            full_res_thumbs = [
                                t["url"] for t in thumbs
                                if t.get("url") and "s640x640" not in t["url"] and "s150x150" not in t["url"] and "s320x320" not in t["url"]
                            ]
                            best_img = full_res_thumbs[0] if full_res_thumbs else (e.get("thumbnail") or (thumbs[-1]["url"] if thumbs else None))
                            preview_img = e.get("thumbnail") or (thumbs[-1]["url"] if thumbs else best_img)

                            e_formats = e.get("formats") or []
                            e_norm_formats: List[NormalizedFormat] = []
                            for raw_fmt in e_formats:
                                norm = self.normalize_format(raw_fmt)
                                if norm:
                                    e_norm_formats.append(norm)

                            is_item_video = bool(e_norm_formats) or bool(e.get("video_versions")) or bool(e.get("duration") and e.get("duration") > 0)
                            item_type = "video" if is_item_video else "image"

                            gallery_items.append(GalleryItem(
                                index=idx + 1,
                                id=str(e.get("id") or f"item_{idx + 1}"),
                                type=item_type,
                                thumbnail=preview_img,
                                display_url=best_img if item_type == "image" else (e_norm_formats[0].format_id if e_norm_formats else None),
                                width=e.get("width"),
                                height=e.get("height"),
                                duration=int(e.get("duration", 0)) if e.get("duration") else None,
                                formats=e_norm_formats
                            ))

                        zip_format = NormalizedFormat(
                            format_id="zip",
                            type="gallery",
                            container="zip",
                            format_note=f"ZIP Archive ({len(gallery_items)} items)",
                            quality=f"All {len(gallery_items)} Files",
                            downloadable=True
                        )

                        return {
                            "source_url": url,
                            "title": info.get("title") or "Instagram Post",
                            "thumbnail": gallery_items[0].thumbnail if gallery_items else self._select_best_thumbnail(info),
                            "duration": None,
                            "uploader": info.get("uploader") or info.get("channel") or info.get("uploader_id"),
                            "raw_formats": [],
                            "formats": [zip_format],
                            "is_gallery": True,
                            "gallery_items": gallery_items,
                            "media_type": "gallery",
                        }

                    # 2. Single item (either single post or playlist of 1)
                    if is_playlist and raw_entries:
                        info = raw_entries[0]

                    raw_formats = info.get("formats", [])
                    normalized_formats: List[NormalizedFormat] = []
                    seen_format_ids = set()

                    for raw_fmt in raw_formats:
                        norm = self.normalize_format(raw_fmt)
                        if norm and norm.format_id not in seen_format_ids:
                            seen_format_ids.add(norm.format_id)
                            normalized_formats.append(norm)

                    best_thumb = self._select_best_thumbnail(info)

                    # If 0 playable formats extracted, check if this is an image/photo post (Instagram only)!
                    # YouTube NEVER has standalone photo posts; YouTube must never return media_type="image".
                    if not normalized_formats and not is_youtube:
                        thumbs = info.get("thumbnails") or []
                        full_res_thumbs = [
                            t["url"] for t in thumbs
                            if t.get("url") and "s640x640" not in t["url"] and "s150x150" not in t["url"] and "s320x320" not in t["url"]
                        ]
                        best_img = full_res_thumbs[0] if full_res_thumbs else (best_thumb or (thumbs[-1]["url"] if thumbs else None))

                        if best_img:
                            photo_format = NormalizedFormat(
                                format_id="photo_original",
                                type="image",
                                container="jpg",
                                quality="Original Photo",
                                format_note="High-Resolution Photo",
                                downloadable=True
                            )
                            return {
                                "source_url": url,
                                "title": info.get("title") or "Photo",
                                "thumbnail": best_thumb or best_img,
                                "duration": None,
                                "uploader": info.get("uploader") or info.get("channel") or info.get("uploader_id"),
                                "raw_formats": [],
                                "formats": [photo_format],
                                "is_gallery": False,
                                "gallery_items": [],
                                "media_type": "image",
                                "display_url": best_img
                            }

                        logger.info(f"No playable formats or images extracted for {url} with use_cookies={use_cookies}")
                        last_error = YtDlpError("Requested format is not available.", code="FORMAT_NOT_FOUND")
                        continue

                    # Sort formats: video+audio first, then highest resolution, then highest bitrate
                    normalized_formats.sort(
                        key=lambda f: (
                            1 if f.type == "video+audio" else (2 if f.type == "video" else 3),
                            -(f.height or 0),
                            -(f.bitrate or 0)
                        )
                    )

                    candidate_result = {
                        "source_url": url,
                        "title": info.get("title") or "Untitled Media",
                        "thumbnail": best_thumb,
                        "duration": int(info.get("duration", 0)) if info.get("duration") else None,
                        "uploader": info.get("uploader") or info.get("channel") or info.get("uploader_id"),
                        "raw_formats": raw_formats,
                        "formats": normalized_formats,
                        "is_gallery": False,
                        "gallery_items": [],
                        "media_type": "video",
                    }

                    video_count = sum(1 for f in normalized_formats if f.has_video)
                    if video_count > best_video_count or not best_result:
                        best_result = candidate_result
                        best_video_count = video_count

                    # If extraction only yielded <= 1 video format (e.g. fallback 360p or 0 video formats) and alternate strategy exists, try it to obtain full resolutions
                    if (video_count <= 1 or not normalized_formats) and use_cookies != strategies[-1]:
                        logger.info(f"Extraction with use_cookies={use_cookies} only yielded {video_count} video formats. Trying alternate strategy for full resolutions...")
                        continue

                    return candidate_result
            except yt_dlp.utils.DownloadError as e:
                err_str = str(e)
                last_error = e
                if use_cookies != strategies[-1]:
                    logger.info(f"Extraction attempt with use_cookies={use_cookies} failed ({err_str}), falling back to alternate strategy...")
                    continue

                if best_result:
                    logger.info(f"Subsequent extraction failed ({err_str}), returning best previously extracted result ({best_video_count} video formats).")
                    return best_result

                if ("Private video" in err_str or "Sign in" in err_str) and "confirm you're not a bot" not in err_str and "bot" not in err_str.lower():
                    raise YtDlpError("Media is private or requires authentication.", code="AUTHENTICATION_REQUIRED")
                elif "Video unavailable" in err_str:
                    raise YtDlpError("Media is unavailable or was removed.", code="MEDIA_UNAVAILABLE")
                elif "Geo-restricted" in err_str:
                    raise YtDlpError("Media is restricted in this region.", code="GEO_RESTRICTED")
                else:
                    raise YtDlpError(f"Extraction error: {err_str}", code="DOWNLOAD_ERROR")
            except Exception as e:
                if isinstance(e, YtDlpError):
                    if best_result:
                        return best_result
                    raise
                last_error = e
                if use_cookies != strategies[-1]:
                    continue
                if best_result:
                    logger.info(f"Subsequent extraction threw {e}, returning best previously extracted result ({best_video_count} video formats).")
                    return best_result
                logger.exception("Unexpected error during yt-dlp metadata extraction")
                raise YtDlpError(f"Unexpected extraction failure: {str(e)}", code="INTERNAL_ERROR")

        if best_result:
            logger.info(f"Returning best available extraction result ({best_video_count} video formats) after all strategies evaluated.")
            return best_result

        if last_error:
            if isinstance(last_error, YtDlpError):
                raise last_error
            err_str = str(last_error)
            if ("Private video" in err_str or "Sign in" in err_str) and "confirm you're not a bot" not in err_str and "bot" not in err_str.lower():
                raise YtDlpError("Media is private or requires authentication.", code="AUTHENTICATION_REQUIRED")
            raise YtDlpError(f"Extraction error: {err_str}", code="DOWNLOAD_ERROR")
        raise YtDlpError("Could not retrieve media info.", code="EXTRACTION_FAILED")

    async def extract_metadata_async(self, url: str) -> Dict[str, Any]:
        """Asynchronous wrapper for extract_metadata."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.extract_metadata, url)

    def _build_download_opts(
        self,
        format_spec: str,
        output_template: str,
        progress_hook: Callable[[Dict[str, Any]], None],
        use_cookies: bool = True,
        is_youtube: bool = False
    ) -> Dict[str, Any]:
        """Builds download options for yt-dlp."""
        opts: Dict[str, Any] = {
            "format": format_spec,
            "outtmpl": output_template,
            "progress_hooks": [progress_hook],
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 30,
            "retries": 10,
            "fragment_retries": 10,
            "continuedl": True,
            "no_color": True,
            "nopostoverwrites": True,
            "buffersize": 1024 * 1024,
            "http_chunk_size": 5 * 1024 * 1024,
        }
        # Always configure JS runtime
        self._configure_js_runtime(opts)

        # For YouTube:
        # - Unauthenticated: visionos player client streams native HLS (m3u8) without 403 Forbidden
        # - Authenticated: use authed web clients (web_embedded, tv_downgraded, web)
        if is_youtube:
            if use_cookies:
                opts["extractor_args"] = {
                    "youtube": {
                        "player_client": ["web_embedded", "tv_downgraded", "web"]
                    }
                }
            else:
                opts["extractor_args"] = {
                    "youtube": {
                        "player_client": ["visionos"]
                    }
                }

        if use_cookies:
            cookiefile = self._get_cookiefile()
            if cookiefile:
                opts["cookiefile"] = cookiefile

        # Proxy support
        if getattr(settings, "YTDLP_PROXY", None) and settings.YTDLP_PROXY.strip():
            opts["proxy"] = settings.YTDLP_PROXY.strip()

        return opts

    def download_media(
        self,
        url: str,
        format_spec: str,
        output_template: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        cancellation_event: Optional[Any] = None
    ) -> str:
        """
        Downloads the specified format using yt-dlp.
        Synchronous execution inside worker thread/executor with active cancellation support.
        Includes automatic retry with alternate strategy if initial attempt fails.
        """
        import yt_dlp

        def _hook(d: Dict[str, Any]):
            if cancellation_event and cancellation_event.is_set():
                raise yt_dlp.utils.DownloadCancelled("Download cancelled by user or timeout")

            if not progress_callback:
                return

            status = d.get("status")
            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes") or 0
                speed = d.get("speed")
                eta = d.get("eta")

                pct = (downloaded / total * 100.0) if total > 0 else 0.0

                progress_callback({
                    "status": "downloading",
                    "progress": round(min(pct, 99.9), 1),
                    "downloaded_bytes": downloaded,
                    "total_bytes": total,
                    "speed": self._format_speed(speed),
                    "eta": self._format_eta(eta),
                })
            elif status == "finished":
                total = d.get("total_bytes") or d.get("downloaded_bytes") or 0
                progress_callback({
                    "status": "finished",
                    "progress": 100.0,
                    "downloaded_bytes": total,
                    "total_bytes": total,
                    "speed": None,
                    "eta": "00:00",
                })

        is_youtube = ("youtube.com" in url.lower() or "youtu.be" in url.lower())
        has_cookies = bool(self._get_cookiefile())
        has_auth_yt = self._has_authenticated_youtube_cookies()
        if is_youtube:
            # For YouTube: Try unauthenticated visionos + m3u8 FIRST (immune to datacenter bot blocks and session rotation).
            # If unauthenticated fails (e.g. age-restricted or private video), fallback to authenticated cookies.
            strategies = [False, True] if (has_cookies and has_auth_yt) else [False]
        else:
            strategies = [True, False] if has_cookies else [False]
        last_error = None

        for use_cookies in strategies:
            if cancellation_event and cancellation_event.is_set():
                raise YtDlpError("Download was cancelled.", code="CANCELLED")
            try:
                ydl_opts = self._build_download_opts(format_spec, output_template, _hook, use_cookies=use_cookies, is_youtube=is_youtube)
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if cancellation_event and cancellation_event.is_set():
                        raise YtDlpError("Download was cancelled.", code="CANCELLED")
                    downloaded_file = ydl.prepare_filename(info)
                    return downloaded_file
            except yt_dlp.utils.DownloadCancelled:
                raise YtDlpError("Download was cancelled.", code="CANCELLED")
            except yt_dlp.utils.DownloadError as e:
                if cancellation_event and cancellation_event.is_set():
                    raise YtDlpError("Download was cancelled.", code="CANCELLED")
                last_error = e
                err_str = str(e)
                if use_cookies != strategies[-1]:
                    logger.warning(f"Download attempt (use_cookies={use_cookies}) failed with '{err_str}', retrying with alternate strategy...")
                    continue
                raise YtDlpError(f"Download failed: {err_str}", code="DOWNLOAD_FAILED")
            except Exception as e:
                if isinstance(e, YtDlpError):
                    raise
                if cancellation_event and cancellation_event.is_set():
                    raise YtDlpError("Download was cancelled.", code="CANCELLED")
                last_error = e
                if use_cookies != strategies[-1]:
                    continue
                raise YtDlpError(f"Unexpected download error: {str(e)}", code="INTERNAL_ERROR")

        raise YtDlpError(f"Download failed: {str(last_error)}", code="DOWNLOAD_FAILED")

    async def download_media_async(
        self,
        url: str,
        format_spec: str,
        output_template: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        cancellation_event: Optional[Any] = None
    ) -> str:
        """Asynchronous wrapper for download_media."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self.download_media,
            url,
            format_spec,
            output_template,
            progress_callback,
            cancellation_event
        )

ytdlp_service = YtDlpService()
