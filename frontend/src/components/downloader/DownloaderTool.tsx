import React, { useState, useEffect, useRef } from 'react';
import type { AnalyzeResponse, JobResponse, SSEEventData, OutputType } from '../../api/types';
import { api, sanitizeErrorMessage } from '../../api/client';
import { subscribeToJobEvents } from '../../api/sse';
import { appConfig } from '../../config/appConfig';
import { URLInput } from './URLInput';
import { MediaPreview } from './MediaPreview';
import { OutputSelector } from './OutputSelector';
import { QualitySelector } from './QualitySelector';
import { ProgressCard } from './ProgressCard';
import { SuccessCard } from './SuccessCard';
import { GalleryView } from './GalleryView';
import { SkeletonCard } from './SkeletonCard';
import { ErrorAlert } from './ErrorAlert';
import { InterstitialModal } from '../ads/InterstitialModal';

export interface DownloaderToolProps {
  defaultOutputType?: OutputType;
  placeholder?: string;
  initialUrl?: string;
}

export interface FormattedError {
  title: string;
  message: string;
  tip?: string;
}

const formatError = (err: any, fallbackMessage: string = 'An unexpected error occurred.'): FormattedError => {
  if (err && typeof err === 'object') {
    if (err.title && err.message) {
      return {
        title: err.title,
        message: err.message,
        tip: err.tip,
      };
    }
    const sanitized = sanitizeErrorMessage(err.code, err.message || fallbackMessage);
    return {
      title: sanitized.title,
      message: sanitized.message,
      tip: sanitized.tip,
    };
  }
  const sanitized = sanitizeErrorMessage(null, typeof err === 'string' ? err : fallbackMessage);
  return {
    title: sanitized.title,
    message: sanitized.message,
    tip: sanitized.tip,
  };
};

type Step = 'input' | 'analyzing' | 'analyzed' | 'downloading' | 'completed' | 'error';

export const DownloaderTool: React.FC<DownloaderToolProps> = ({
  defaultOutputType = 'mp4',
  placeholder,
  initialUrl = '',
}) => {
  const [url, setUrl] = useState(initialUrl);
  const [step, setStep] = useState<Step>('input');
  const [outputType, setOutputType] = useState<OutputType>(defaultOutputType);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [selectedFormatId, setSelectedFormatId] = useState<string>('');
  const [job, setJob] = useState<JobResponse | null>(null);
  const [progressData, setProgressData] = useState<SSEEventData | null>(null);
  const [error, setError] = useState<FormattedError | null>(null);
  const [showInterstitial, setShowInterstitial] = useState(false);

  const unsubscribeRef = useRef<(() => void) | null>(null);
  const pollIntervalRef = useRef<number | null>(null);
  const isSubmittingRef = useRef<boolean>(false);
  const resultCardRef = useRef<HTMLDivElement>(null);
  const progressCardRef = useRef<HTMLDivElement>(null);
  const successCardRef = useRef<HTMLDivElement>(null);

  // Smooth scroll helper with navbar compensation (75px)
  const scrollToTarget = (target: HTMLElement | null, offset: number = 75) => {
    if (!target) return;
    const elementPosition = target.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.pageYOffset - offset;
    window.scrollTo({
      top: Math.max(0, offsetPosition),
      behavior: 'smooth',
    });
  };

  // Smooth scroll seamlessly to active area on each step transition:
  // 1. On Search / Paste -> auto-slide to Skeleton / Result Card
  // 2. On clicking Download -> auto-slide to Progress Card
  // 3. After Processing -> auto-slide to Completed Success Card
  useEffect(() => {
    let timer: number | undefined;
    if ((step === 'analyzed' || step === 'analyzing') && resultCardRef.current) {
      timer = window.setTimeout(() => {
        scrollToTarget(resultCardRef.current, 75);
      }, 80);
    } else if (step === 'downloading' && progressCardRef.current) {
      timer = window.setTimeout(() => {
        scrollToTarget(progressCardRef.current, 75);
      }, 80);
    } else if (step === 'completed' && successCardRef.current) {
      timer = window.setTimeout(() => {
        scrollToTarget(successCardRef.current, 75);
      }, 80);
    }
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [step]);

  // Sync default output type when prop changes
  useEffect(() => {
    if (defaultOutputType) {
      setOutputType(defaultOutputType);
    }
  }, [defaultOutputType]);

  // Cleanup SSE and polling on unmount
  useEffect(() => {
    return () => {
      if (unsubscribeRef.current) unsubscribeRef.current();
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  // Helper to choose the best initial format ID
  const selectInitialFormat = (formats: any[], type: OutputType, platform?: string) => {
    if (platform === 'instagram') {
      return 'best';
    }
    if (!formats || formats.length === 0) return '';
    if (type === 'mp4') {
      const videoFormats = formats.filter((f) => f.has_video);
      const fmt1080 = videoFormats.find((f) => f.height === 1080);
      if (fmt1080) return fmt1080.format_id;
      const fmt720 = videoFormats.find((f) => f.height === 720);
      if (fmt720) return fmt720.format_id;
      return videoFormats[0]?.format_id || formats[0].format_id;
    } else if (type === 'mp3') {
      const audioFormats = formats.filter((f) => f.has_audio && !f.has_video);
      return audioFormats[0]?.format_id || 'audio_best';
    }
    return formats[0]?.format_id || '';
  };

  // 1. URL Analysis Flow
  const handleAnalyze = async (inputUrl: string) => {
    if (isSubmittingRef.current) return;
    const trimmed = inputUrl.trim();
    if (!trimmed) return;

    isSubmittingRef.current = true;
    setError(null);
    setAnalysis(null);
    setJob(null);
    setProgressData(null);
    setStep('analyzing');

    try {
      const res = await api.analyze({ url: trimmed });
      setAnalysis(res);
      const isInsta = res.platform === 'instagram';
      if (res.is_gallery) {
        setOutputType('zip');
      } else if (res.media_type === 'image') {
        setOutputType('thumbnail');
      } else {
        const effType = isInsta ? 'mp4' : outputType;
        if (isInsta) {
          setOutputType('mp4');
        }
        const initialFmt = selectInitialFormat(res.formats, effType, res.platform);
        setSelectedFormatId(initialFmt);
      }
      setStep('analyzed');
    } catch (err: any) {
      setError(formatError(err, 'Failed to analyze media URL.'));
      setStep('error');
    } finally {
      isSubmittingRef.current = false;
    }
  };

  // 2. Output Type Change
  const handleOutputTypeChange = (type: OutputType) => {
    setOutputType(type);
    if (analysis && analysis.formats) {
      const bestFmt = selectInitialFormat(analysis.formats, type, analysis.platform);
      setSelectedFormatId(bestFmt);
    }
  };

  // 3. Fallback Polling if SSE Fails
  const startFallbackPolling = (jobId: string) => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

    pollIntervalRef.current = window.setInterval(async () => {
      try {
        const currentJob = await api.getJob(jobId);
        setJob(currentJob);
        setProgressData({
          job_id: currentJob.id,
          status: currentJob.status,
          progress: currentJob.progress,
          speed: currentJob.speed,
          eta: currentJob.eta,
          downloaded_bytes: currentJob.downloaded_bytes,
          total_bytes: currentJob.total_bytes,
          download_url: currentJob.download_url,
          error_code: currentJob.error_code,
          error_message: currentJob.error_message,
        });

        if (currentJob.status === 'COMPLETED') {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          setStep('completed');
        } else if (['FAILED', 'CANCELLED', 'EXPIRED'].includes(currentJob.status)) {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          setError(formatError(currentJob.error_code || currentJob.error_message, 'Download processing failed.'));
          setStep('error');
        }
      } catch {
        // keep polling until timeout
      }
    }, 1500);
  };

  // 4. Download Trigger Execution
  const executeDownloadJob = async () => {
    if (!analysis) return;

    if (outputType === 'thumbnail' || analysis.media_type === 'image') {
      // Thumbnail or single image direct download via backend proxy with Content-Disposition: attachment
      const targetUrl = analysis.thumbnail;
      if (targetUrl) {
        const baseTitle = analysis.title ? analysis.title.replace(/[^a-zA-Z0-9_\-]/g, '_').substring(0, 30) : 'photo';
        const downloadUrl = `${api.getBaseUrl()}/api/thumbnail/download?url=${encodeURIComponent(targetUrl)}&title=${encodeURIComponent(baseTitle)}&is_media=true`;
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.setAttribute('download', '');
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }
      return;
    }

    setStep('downloading');
    setError(null);

    const isInstagram = analysis.platform === 'instagram';
    const targetFormat = isInstagram ? 'best' : (selectedFormatId || 'best');

    try {
      const res = await api.createDownload({
        analysis_id: analysis.analysis_id,
        format_id: targetFormat,
        quality: targetFormat,
        output_format: outputType,
      });

      const initialJobData: JobResponse = {
        id: res.job_id,
        status: res.status,
        progress: 0,
      };
      setJob(initialJobData);
      setProgressData({
        job_id: res.job_id,
        status: res.status,
        progress: 0,
      });

      // Start polling immediately alongside SSE to eliminate waiting lag
      startFallbackPolling(res.job_id);

      // Subscribe to realtime SSE events
      const unsubscribe = subscribeToJobEvents({
        jobId: res.job_id,
        onEvent: (data) => {
          setProgressData(data);
        },
        onComplete: () => {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          setStep('completed');
        },
        onTerminal: (terminalStatus, data) => {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          if (terminalStatus === 'FAILED' || terminalStatus === 'EXPIRED') {
            setError(formatError(data.error_code || data.error_message, 'Download processing failed.'));
            setStep('error');
          }
        },
        onError: () => {
          startFallbackPolling(res.job_id);
        },
      });

      unsubscribeRef.current = unsubscribe;
    } catch (err: any) {
      setError(formatError(err, 'Could not initiate download job.'));
      setStep('error');
    }
  };

  // 4b. Gallery ZIP Download Trigger
  const handleDownloadZip = async (selectedIndices: number[]) => {
    if (!analysis) return;
    setStep('downloading');
    setError(null);
    setOutputType('zip');

    try {
      const res = await api.createDownload({
        analysis_id: analysis.analysis_id,
        format_id: 'zip',
        quality: 'zip',
        output_format: 'zip',
        selected_indices: selectedIndices,
      });

      const initialJobData: JobResponse = {
        id: res.job_id,
        status: res.status,
        progress: 0,
      };
      setJob(initialJobData);
      setProgressData({
        job_id: res.job_id,
        status: res.status,
        progress: 0,
      });

      startFallbackPolling(res.job_id);

      const unsubscribe = subscribeToJobEvents({
        jobId: res.job_id,
        onEvent: (data) => {
          setProgressData(data);
        },
        onComplete: () => {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          setStep('completed');
        },
        onTerminal: (terminalStatus, data) => {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          if (terminalStatus === 'FAILED' || terminalStatus === 'EXPIRED') {
            setError(formatError(data.error_code || data.error_message, 'Download processing failed.'));
            setStep('error');
          }
        },
        onError: () => {
          startFallbackPolling(res.job_id);
        },
      });

      unsubscribeRef.current = unsubscribe;
    } catch (err: any) {
      setError(formatError(err, 'Could not initiate ZIP download.'));
      setStep('error');
    }
  };

  // 5. User Click on Main Download CTA Button
  const handleDownloadClick = () => {
    if (outputType === 'thumbnail' || analysis?.media_type === 'image') {
      executeDownloadJob();
      return;
    }

    if (appConfig.enableInterstitial) {
      setShowInterstitial(true);
    } else {
      executeDownloadJob();
    }
  };

  // 6. Reset Form
  const handleReset = () => {
    if (unsubscribeRef.current) unsubscribeRef.current();
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    setUrl('');
    setAnalysis(null);
    setJob(null);
    setProgressData(null);
    setError(null);
    setStep('input');
  };

  const isInstagram = analysis?.platform === 'instagram';

  const getDownloadButtonLabel = () => {
    if (analysis?.media_type === 'image') return 'Download HD Photo';
    if (isInstagram) return 'Download Video';
    if (outputType === 'mp3') return 'Download MP3';
    if (outputType === 'thumbnail') return 'Download Thumbnail';
    // Show friendly label like "Download 1080p Video" instead of raw format ID
    if (selectedFormatId && analysis?.formats) {
      const fmt = analysis.formats.find((f) => f.format_id === selectedFormatId);
      if (fmt?.height) {
        return `Download ${fmt.height}p Video`;
      }
    }
    return 'Download Video';
  };

  return (
    <div className="downloader-wrapper" id="downloader">
      {/* 1. Input Card */}
      <div className="downloader-input-card">
        <URLInput
          url={url}
          onChange={setUrl}
          onSubmit={handleAnalyze}
          loading={step === 'analyzing'}
          placeholder={placeholder}
          error={step === 'error' && !analysis ? error?.message : null}
        />
      </div>

      {/* Global Error Alert */}
      {error && (
        <ErrorAlert
          title={error.title}
          message={error.message}
          tip={error.tip}
          onDismiss={() => setError(null)}
          onRetry={url ? () => handleAnalyze(url) : undefined}
        />
      )}

      {/* 2. Skeleton Loading Card (appears during URL search / analysis) */}
      {step === 'analyzing' && (
        <div ref={resultCardRef} className="downloader-slide-target">
          <SkeletonCard />
        </div>
      )}

      {/* 3. Result Card (appears cleanly below input when analyzed) */}
      {analysis && step !== 'analyzing' && (
        <div className="downloader-result-card" id="resultCard" ref={resultCardRef}>
          {analysis.is_gallery ? (
            step !== 'completed' && (
              <GalleryView
                items={analysis.gallery_items || []}
                title={analysis.title}
                uploader={analysis.uploader}
                onDownloadZip={handleDownloadZip}
                onDownloadSingleVideo={(item) => handleDownloadZip([item.index])}
                disabled={step === 'downloading'}
              />
            )
          ) : (
            <MediaPreview media={analysis} />
          )}

          {step !== 'completed' && !analysis.is_gallery && (
            <>
              {/* For Instagram or single image: Hide format/quality selectors if Instagram or single image */}
              {!isInstagram && analysis.media_type !== 'image' && (
                <>
                  {/* Output Format Selector: MP4 | MP3 | Thumbnail */}
                  <OutputSelector
                    selected={outputType}
                    onChange={handleOutputTypeChange}
                    disabled={step === 'downloading'}
                  />

                  {/* Quality / Resolution Dropdown (only when not thumbnail) */}
                  {outputType !== 'thumbnail' && (
                    <QualitySelector
                      formats={analysis.formats}
                      selectedFormatId={selectedFormatId}
                      onChange={setSelectedFormatId}
                      outputType={outputType}
                      disabled={step === 'downloading'}
                    />
                  )}
                </>
              )}

              {/* Primary Action Button Row */}
              {step !== 'downloading' && (
                <div className="downloader-cta-row">
                  <button
                    type="button"
                    onClick={handleDownloadClick}
                    className="btn-download-primary"
                  >
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                    >
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="7 10 12 15 17 10" />
                      <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                    <span>{getDownloadButtonLabel()}</span>
                  </button>

                  {analysis.thumbnail && outputType !== 'thumbnail' && !isInstagram && analysis.media_type !== 'image' && (
                    <button
                      type="button"
                      onClick={() => handleOutputTypeChange('thumbnail')}
                      className="btn-cover-art-secondary"
                      title="Switch to Cover Art"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                        <circle cx="8.5" cy="8.5" r="1.5" />
                        <polyline points="21 15 16 10 5 21" />
                      </svg>
                      <span>Cover Art</span>
                    </button>
                  )}
                </div>
              )}
            </>
          )}

          {/* Active Download Progress Card */}
          {step === 'downloading' && (
            <div ref={progressCardRef} className="downloader-slide-target">
              <ProgressCard
                job={progressData || job || undefined}
                isInstagram={isInstagram}
                outputFormat={outputType}
              />
            </div>
          )}

          {/* Completed Success Card */}
          {step === 'completed' && (
            <div ref={successCardRef} className="downloader-slide-target">
              <SuccessCard
                title={analysis.title || undefined}
                thumbnail={analysis.thumbnail || undefined}
                fileSize={progressData?.total_bytes || job?.file_size}
                outputFormat={outputType}
                downloadUrl={
                  (progressData?.job_id || job?.id)
                    ? api.getFileDownloadUrl(progressData?.job_id || job?.id || '')
                    : (progressData?.download_url
                        ? (progressData.download_url.startsWith('http')
                            ? progressData.download_url
                            : `${api.getBaseUrl()}${progressData.download_url}`)
                        : '')
                }
                isInstagram={isInstagram}
                onReset={handleReset}
              />
            </div>
          )}
        </div>
      )}

      {/* Interstitial Ad Preparation Modal */}
      <InterstitialModal
        isOpen={showInterstitial}
        onReady={() => {
          setShowInterstitial(false);
          executeDownloadJob();
        }}
        onClose={() => setShowInterstitial(false)}
        seconds={appConfig.interstitialCountdownSeconds}
      />
    </div>
  );
};
