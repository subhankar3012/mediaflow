import asyncio
import os
import shutil
import threading
import time
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any, List
import httpx
from app.config import settings
from app.schemas.job import JobStatus
from app.services.job_service import job_service
from app.services.storage_service import storage_service
from app.services.ytdlp_service import ytdlp_service, YtDlpError
from app.services.ffmpeg_service import ffmpeg_service, FFmpegError, MediaValidationError
from app.platforms import get_platform_handler
from app.security.rate_limiter import rate_limiter
from app.services.resource_monitor import job_cost_estimator, JobCostEstimate, JobResourceClass
from app.services.concurrency_manager import concurrency_manager
from app.workers.queue import job_queue
from app.utils.logger import logger, log_job

class DownloadWorker:
    """
    Adaptive Multi-Task Background Worker.
    Dynamically admits and executes concurrent media download, transcoding,
    and validation tasks based on real-time server resource availability.
    Supports atomic job cancellation (yt-dlp + FFmpeg process termination).
    """

    def __init__(self):
        self._running = False
        self._dispatcher_task: Optional[asyncio.Task] = None
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._cancellation_events: Dict[str, threading.Event] = {}
        self._job_costs: Dict[str, JobCostEstimate] = {}
        self._lock = threading.Lock()

    def start(self) -> None:
        self._running = True
        self._dispatcher_task = asyncio.create_task(self._dispatcher_loop())
        asyncio.create_task(self._recover_queued_jobs())
        logger.info("DownloadWorker started adaptive multi-task dispatcher loop.")

    async def _recover_queued_jobs(self) -> None:
        """Recovers any jobs left in QUEUED state when the server/container restarts."""
        try:
            await asyncio.sleep(2.0)
            from app.database import repository
            if hasattr(repository, "client") and repository.client:
                res = repository.client.table("download_jobs").select("id").eq("status", "QUEUED").limit(20).execute()
                if res.data:
                    logger.info(f"Recovering {len(res.data)} orphaned QUEUED job(s) from database...")
                    for row in res.data:
                        await job_queue.enqueue(row["id"])
        except Exception as e:
            logger.warning(f"Failed to recover queued jobs: {e}")

    def stop(self) -> None:
        self._running = False
        if self._dispatcher_task:
            self._dispatcher_task.cancel()

        # Cancel and abort all in-flight jobs
        with self._lock:
            for job_id, event in list(self._cancellation_events.items()):
                event.set()
                ffmpeg_service.kill_job_process(job_id)
            for job_id, task in list(self._active_tasks.items()):
                task.cancel()

        logger.info("DownloadWorker stopped and cleaned up active tasks.")

    async def cancel_job(self, job_id: str) -> bool:
        """
        Actively cancels an in-flight job:
        1. Sets threading.Event to abort yt-dlp download hooks
        2. Kills any running FFmpeg child process
        3. Cancels the active worker asyncio Task
        4. Cleans the temporary disk directory
        5. Releases the concurrency reservation
        6. Updates the database status to CANCELLED
        """
        log_job(job_id, "Initiating active job cancellation")

        # 1. Trigger cancellation event for yt-dlp
        with self._lock:
            event = self._cancellation_events.get(job_id)
            if event:
                event.set()

        # 2. Terminate running FFmpeg subprocess
        ffmpeg_service.kill_job_process(job_id)

        # 3. Cancel asyncio task
        with self._lock:
            task = self._active_tasks.get(job_id)
            if task and not task.done():
                task.cancel()

        # 4. Clean storage
        storage_service.delete_job_dir(job_id)

        # 5. Release concurrency reservation
        concurrency_manager.release(job_id, success=False)
        if not task:
            job = await job_service.get_job(job_id)
            if job and job.get("session_id"):
                rate_limiter.release_job_slot(job["session_id"])

        # 6. Update database status
        await job_service.update_status(
            job_id=job_id,
            new_status=JobStatus.CANCELLED,
            error_message="Job was cancelled."
        )
        log_job(job_id, "Job cancellation completed successfully.")
        return True

    async def _dispatcher_loop(self) -> None:
        """
        Central dispatcher loop. Dequeues jobs and admits them dynamically
        based on real-time hardware capacity.
        """
        while self._running:
            try:
                job_id = await job_queue.dequeue()
                job = await job_service.get_job(job_id)
                if not job:
                    job_queue.task_done()
                    continue

                if job.get("status") in (JobStatus.CANCELLED.value, JobStatus.EXPIRED.value):
                    job_queue.task_done()
                    continue

                # Estimate job cost from analysis or job format metadata
                cost = await self._calculate_job_cost(job)
                session_id = job.get("session_id", "default")

                # Dynamic admission retry loop: if server is temporarily saturated, wait and retry
                admitted = False
                admission_attempts = 0
                max_admission_attempts = 60  # Wait up to 60s for resources to clear

                while self._running and not admitted and admission_attempts < max_admission_attempts:
                    # Check if job was cancelled while waiting in queue
                    current_job = await job_service.get_job(job_id)
                    if not current_job or current_job.get("status") == JobStatus.CANCELLED.value:
                        break

                    admitted, reason = concurrency_manager.try_reserve(job_id, session_id, cost)
                    if admitted:
                        break

                    admission_attempts += 1
                    await asyncio.sleep(1.0)

                if not admitted:
                    log_job(job_id, f"Job rejected by admission controller: {reason}", level="warning")
                    await job_service.update_status(
                        job_id=job_id,
                        new_status=JobStatus.FAILED,
                        error_code="SERVICE_BUSY",
                        error_message="The server is experiencing high traffic. Please try again in a moment."
                    )
                    rate_limiter.release_job_slot(session_id)
                    job_queue.task_done()
                    continue

                # Spawn worker task for admitted job
                cancel_event = threading.Event()
                with self._lock:
                    self._cancellation_events[job_id] = cancel_event
                    self._job_costs[job_id] = cost

                task = asyncio.create_task(self.process_job(job_id, cost, cancel_event))
                with self._lock:
                    self._active_tasks[job_id] = task

                task.add_done_callback(lambda t, j=job_id: self._cleanup_completed_task(j))
                job_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Unexpected error in dispatcher loop: {e}")
                await asyncio.sleep(1.0)

    def _cleanup_completed_task(self, job_id: str) -> None:
        with self._lock:
            self._active_tasks.pop(job_id, None)
            self._cancellation_events.pop(job_id, None)
            self._job_costs.pop(job_id, None)

    async def _calculate_job_cost(self, job: Dict[str, Any]) -> JobCostEstimate:
        format_info: Dict[str, Any] = {}
        duration = None

        analysis_id = job.get("analysis_id")
        if analysis_id:
            analysis = await job_service.get_analysis(analysis_id)
            if analysis:
                duration = analysis.get("duration")
                req_fmt = job.get("requested_format")
                for fmt in analysis.get("normalized_formats", []):
                    f_id = fmt.get("format_id") if isinstance(fmt, dict) else getattr(fmt, "format_id", "")
                    if str(f_id) == str(req_fmt):
                        format_info = fmt if isinstance(fmt, dict) else fmt.model_dump()
                        break

        output_format = job.get("output_format") or "mp4"
        return job_cost_estimator.estimate_cost(format_info, output_format, duration)

    async def _process_gallery_zip(
        self,
        job: Dict[str, Any],
        output_dir: Path,
        cancel_event: threading.Event
    ) -> Path:
        """Packages selected items from a carousel/gallery post into a compressed ZIP archive."""
        job_id = job["id"]
        analysis_id = job.get("analysis_id")
        analysis = await job_service.get_analysis(analysis_id) if analysis_id else None
        gallery_items = []
        if analysis:
            gallery_items = analysis.get("gallery_items") or []

        # Parse requested indices if any (e.g. zip:1,2,3 or zip:all)
        req_fmt = job.get("requested_format") or ""
        target_indices = None
        if req_fmt.startswith("zip:") and req_fmt != "zip:all":
            idx_str = req_fmt.split(":", 1)[1]
            parsed_indices = [int(x) for x in idx_str.split(",") if x.strip().isdigit()]
            if parsed_indices:
                target_indices = set(parsed_indices)

        # Filter items
        items_to_download = [
            it for it in gallery_items
            if target_indices is None or it.get("index") in target_indices
        ]
        if not items_to_download and gallery_items:
            items_to_download = gallery_items

        if not items_to_download:
            raise YtDlpError("No gallery items found to package.", code="GALLERY_EMPTY")

        final_output_path = output_dir / "final.zip"
        total_items = len(items_to_download)
        log_job(job_id, f"Packaging {total_items} gallery item(s) into ZIP...")

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            with zipfile.ZipFile(final_output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for pos, item in enumerate(items_to_download):
                    if cancel_event.is_set():
                        raise asyncio.CancelledError()

                    item_idx = item.get("index", pos + 1)
                    item_type = item.get("type", "image")
                    media_url = item.get("display_url") or item.get("thumbnail")

                    if not media_url:
                        continue

                    if media_url.startswith("http"):
                        try:
                            resp = await client.get(media_url)
                            if resp.status_code == 200:
                                content = resp.content
                                c_type = resp.headers.get("content-type", "")
                                ext = "webp" if "webp" in c_type else ("png" if "png" in c_type else "jpg")
                                if item_type == "video":
                                    ext = "mp4"
                                zf.writestr(f"item_{item_idx:02d}.{ext}", content)
                        except Exception as e:
                            logger.warning(f"Failed to fetch item {item_idx} ({media_url}): {e}")

                    # Broadcast progress
                    pct = round(((pos + 1) / total_items) * 100.0, 1)
                    await job_service.update_progress(
                        job_id=job_id,
                        progress=min(pct, 99.9),
                        downloaded_bytes=final_output_path.stat().st_size if final_output_path.exists() else 0,
                        total_bytes=None,
                        speed=None,
                        eta=None
                    )

        if not final_output_path.exists() or not zipfile.is_zipfile(final_output_path):
            raise YtDlpError("Failed to generate valid ZIP archive.", code="ZIP_CREATION_FAILED")

        return final_output_path

    async def process_job(self, job_id: str, cost: JobCostEstimate, cancel_event: threading.Event) -> None:
        log_job(job_id, f"Worker started processing (Class: {cost.resource_class.value})")
        job = await job_service.get_job(job_id)
        if not job:
            concurrency_manager.release(job_id, success=False)
            return

        session_id = job.get("session_id", "default")
        source_url = job["source_url"]
        requested_format = job.get("requested_format") or "best"
        target_ext = (job.get("output_format") or "mp4").lower().strip(".")

        dirs = storage_service.create_job_dirs(job_id)
        source_dir = dirs["source"]
        working_dir = dirs["working"]
        output_dir = dirs["output"]

        loop = asyncio.get_running_loop()
        success = False

        # Class-specific timeout guardrails
        timeout_seconds = (
            settings.MAX_JOB_DURATION_SECONDS if cost.resource_class in (JobResourceClass.HEAVY, JobResourceClass.VERY_HEAVY)
            else min(settings.MAX_JOB_DURATION_SECONDS, 600)
        )

        try:
            # 1. Update status to PROCESSING
            await job_service.update_status(job_id, JobStatus.PROCESSING)

            # 2. Check cancellation
            if cancel_event.is_set():
                raise asyncio.CancelledError()

            # Handle gallery ZIP jobs directly
            if target_ext == "zip" or requested_format.startswith("zip"):
                final_output_path = await self._process_gallery_zip(job, output_dir, cancel_event)
                file_size = final_output_path.stat().st_size
                shutil.rmtree(source_dir, ignore_errors=True)
                shutil.rmtree(working_dir, ignore_errors=True)
                rel_key = str(final_output_path.relative_to(settings.temp_storage_dir))
                await job_service.update_status(
                    job_id=job_id,
                    new_status=JobStatus.COMPLETED,
                    file_size=file_size,
                    temporary_file_key=rel_key
                )
                log_job(job_id, f"Successfully created gallery ZIP! Size: {file_size} bytes")
                success = True
                return

            # 3. Resolve platform handler & build format spec
            handler = get_platform_handler(source_url)
            is_audio_only = cost.is_audio_only
            if handler:
                format_spec = handler.build_format_spec(
                    format_id=requested_format,
                    output_format=target_ext,
                    audio_only=is_audio_only
                )
            else:
                format_spec = requested_format

            log_job(job_id, f"Downloading format spec: {format_spec}")

            # 4. Define progress callback
            def progress_callback(data: Dict[str, Any]) -> None:
                asyncio.run_coroutine_threadsafe(
                    job_service.update_progress(
                        job_id=job_id,
                        progress=data.get("progress", 0.0),
                        downloaded_bytes=data.get("downloaded_bytes"),
                        total_bytes=data.get("total_bytes"),
                        speed=data.get("speed"),
                        eta=data.get("eta"),
                    ),
                    loop
                )

            # 5. Download media using YtDlpService into isolated source/ directory
            output_template = str(source_dir / "stream_%(autonumber)02d.%(ext)s")

            await asyncio.wait_for(
                ytdlp_service.download_media_async(
                    url=source_url,
                    format_spec=format_spec,
                    output_template=output_template,
                    progress_callback=progress_callback,
                    cancellation_event=cancel_event
                ),
                timeout=timeout_seconds
            )

            if cancel_event.is_set():
                raise asyncio.CancelledError()

            # 6. Inspect downloaded files in source/ (filter out incomplete part files)
            downloaded_files = [
                f for f in source_dir.iterdir()
                if f.is_file() and f.stat().st_size > 0 and not f.name.endswith(".part") and not f.name.endswith(".ytdl")
            ]
            if not downloaded_files:
                raise YtDlpError("No downloaded files were found in temporary directory.", code="EMPTY_DOWNLOAD")

            log_job(job_id, f"Downloaded {len(downloaded_files)} file(s): {[f.name for f in downloaded_files]}")

            final_output_path = output_dir / f"final.{target_ext}"

            # 7. Post-processing with FFmpegService
            if is_audio_only:
                input_file = downloaded_files[0]
                await ffmpeg_service.extract_audio(
                    input_path=input_file,
                    output_path=final_output_path,
                    audio_format=target_ext,
                    job_id=job_id
                )
            else:
                # Dynamically discover which downloaded file contains video and audio streams
                video_file = None
                audio_file = None
                v_codec = None
                a_codec = None

                for f in downloaded_files:
                    try:
                        p = await ffmpeg_service.probe(f)
                        streams = p.get("streams", [])
                        f_v = next((s.get("codec_name") for s in streams if s.get("codec_type") == "video"), None)
                        f_a = next((s.get("codec_name") for s in streams if s.get("codec_type") == "audio"), None)
                        if f_v and not video_file:
                            video_file = f
                            v_codec = f_v
                            if f_a and not a_codec:
                                a_codec = f_a
                        elif f_a and not audio_file and f != video_file:
                            audio_file = f
                            a_codec = f_a
                    except Exception as e:
                        logger.warning(f"Failed to probe file {f}: {e}")

                if not video_file:
                    video_file = downloaded_files[0]

                log_job(
                    job_id,
                    f"Processing streams: Video={video_file.name} ({v_codec}), "
                    f"Audio={audio_file.name if audio_file else ('embedded' if a_codec else 'none')} ({a_codec})"
                )

                await ffmpeg_service.transcode_to_compatible_mp4(
                    video_path=video_file,
                    audio_path=audio_file,
                    output_path=final_output_path,
                    video_codec=v_codec,
                    audio_codec=a_codec,
                    job_id=job_id
                )

            if cancel_event.is_set():
                raise asyncio.CancelledError()

            # 8. Strict FFprobe validation before marking COMPLETED
            validation_info = await ffmpeg_service.validate_media_file(
                file_path=final_output_path,
                is_audio_only=is_audio_only,
                expected_container=target_ext
            )
            log_job(
                job_id,
                f"Validation passed: {validation_info.get('video_codec')}/{validation_info.get('audio_codec')} "
                f"({validation_info.get('width')}x{validation_info.get('height')}, {validation_info.get('duration')}s)"
            )

            file_size = final_output_path.stat().st_size
            if file_size > settings.MAX_OUTPUT_SIZE_BYTES:
                raise ValueError(
                    f"Generated file size ({file_size} bytes) exceeds the maximum allowed limit "
                    f"of {settings.MAX_OUTPUT_SIZE_BYTES} bytes."
                )

            # 9. Clean up intermediate source/ and working/ directories, keeping only output/
            shutil.rmtree(source_dir, ignore_errors=True)
            shutil.rmtree(working_dir, ignore_errors=True)

            # 10. Mark job as COMPLETED
            rel_key = str(final_output_path.relative_to(settings.temp_storage_dir))
            await job_service.update_status(
                job_id=job_id,
                new_status=JobStatus.COMPLETED,
                file_size=file_size,
                temporary_file_key=rel_key
            )
            log_job(job_id, f"Successfully completed! Size: {file_size} bytes")
            success = True

        except asyncio.CancelledError:
            log_job(job_id, "Job processing was cancelled.", level="warning")
            await job_service.update_status(
                job_id=job_id,
                new_status=JobStatus.CANCELLED,
                error_message="Job was cancelled."
            )
            storage_service.delete_job_dir(job_id)

        except asyncio.TimeoutError:
            err_msg = f"Job exceeded maximum processing duration of {timeout_seconds} seconds."
            log_job(job_id, err_msg, level="error")
            await job_service.update_status(
                job_id=job_id,
                new_status=JobStatus.FAILED,
                error_code="TIMEOUT",
                error_message=err_msg
            )
            storage_service.delete_job_dir(job_id)

        except (YtDlpError, FFmpegError, MediaValidationError, Exception) as e:
            code = getattr(e, "code", "PROCESSING_FAILED")
            msg = getattr(e, "message", str(e))
            log_job(job_id, f"Job failed ({code}): {msg}", level="error")
            await job_service.update_status(
                job_id=job_id,
                new_status=JobStatus.FAILED,
                error_code=code,
                error_message=msg
            )
            storage_service.delete_job_dir(job_id)

        finally:
            import gc
            ffmpeg_service.kill_job_process(job_id)
            concurrency_manager.release(job_id, success=success)
            rate_limiter.release_job_slot(session_id)
            gc.collect()

download_worker = DownloadWorker()
