import type { BreadcrumbItem } from '../utils/seoHelpers';

export interface FAQItem {
  question: string;
  answer: string;
}

export interface FeatureItem {
  title: string;
  description: string;
  icon: string;
}

export interface PageSEO {
  path: string;
  title: string;
  metaDescription: string;
  h1: string;
  subtitle: string;
  platform: 'youtube' | 'instagram' | 'x' | 'facebook' | 'pinterest' | 'reddit' | 'all' | string;
  placeholder: string;
  breadcrumbs: BreadcrumbItem[];
  howItWorks: string[];
  specsTitle?: string;
  specsDescription?: string;
  features: FeatureItem[];
  faqs: FAQItem[];
  relatedTools: { label: string; href: string }[];
}

export const SEO_PAGES: Record<string, PageSEO> = {
  '/': {
    path: '/',
    title: 'Free Online Video & Audio Downloader for YouTube & Instagram',
    metaDescription: 'Download YouTube and Instagram videos in high-definition MP4 or extract clear MP3 audio for free without watermarks. Fast, secure, and mobile-friendly with no registration required.',
    h1: 'Free Online Video & Audio Downloader for YouTube & Instagram',
    subtitle: 'Paste any YouTube or Instagram link to download high-speed MP4 video, MP3 audio, or full-resolution thumbnails with high fidelity.',
    platform: 'all',
    placeholder: 'Paste YouTube or Instagram link here (e.g. https://www.youtube.com/watch?v=...)',
    breadcrumbs: [
      { name: 'Home', path: '/' },
    ],
    howItWorks: [
      'Copy the link of the video or post you want to save from YouTube or Instagram.',
      'Paste the URL into the input field above and click "Search" (or let auto-search detect it).',
      'Select your preferred format (MP4, MP3, or Thumbnail), pick your quality, and click Download.'
    ],
    specsTitle: 'Supported Formats & Playback Capabilities',
    specsDescription: 'MediaFlow standardizes streams to H.264 and MP3 formats to ensure instant compatibility across smart TVs, smartphones, cars, and editing workstations.',
    features: [
      {
        title: 'Full HD 1080p & 60 FPS',
        description: 'Download crisp high-definition videos with original frame rates and complete audio tracks intact.',
        icon: 'hd'
      },
      {
        title: 'Instant Audio Extraction',
        description: 'Extract pristine MP3 and M4A audio from music videos, podcasts, and lectures cleanly and quickly.',
        icon: 'music'
      },
      {
        title: 'Free with No Registration',
        description: 'No accounts, no email captures, and no software installations required.',
        icon: 'zap'
      },
      {
        title: 'Automated Privacy Purge',
        description: 'Temporary files are wiped automatically from our cloud servers after 30 minutes to protect your privacy.',
        icon: 'shield'
      }
    ],
    faqs: [
      {
        question: 'Is this video and audio downloader completely free to use?',
        answer: 'Yes! MediaFlow is free to use for personal downloads with no account registration or payment details required.'
      },
      {
        question: 'What video quality options are available?',
        answer: 'Quality options depend on the source upload. MediaFlow supports 1080p Full HD, 720p HD, 480p, and 360p MP4, as well as MP3 audio extraction.'
      },
      {
        question: 'How does MediaFlow ensure sound on 1080p videos?',
        answer: 'YouTube serves 1080p video and audio as separate streams (adaptive DASH). MediaFlow automatically muxes the high-definition video with the highest-bitrate audio track on our cloud engine using FFmpeg before serving your download.'
      },
      {
        question: 'Can I use this tool on iPhone and Android mobile devices?',
        answer: 'Yes. MediaFlow is optimized for mobile browsers including Apple Safari (iOS 13+) and Google Chrome on Android. You can download and save media directly to your Photos or Files app.'
      },
      {
        question: 'Where are downloaded files saved on my device?',
        answer: 'Downloaded files are saved automatically to your device’s default "Downloads" folder, which can be accessed via Windows Explorer, macOS Finder, Files by Google, or the Apple Files app.'
      }
    ],
    relatedTools: [
      { label: 'YouTube Video Downloader', href: '/youtube-video-downloader' },
      { label: 'Instagram Downloader', href: '/instagram-downloader' },
      { label: 'X Video Downloader', href: '/x-video-downloader' },
      { label: 'Facebook Video Downloader', href: '/facebook-video-downloader' },
      { label: 'Pinterest Downloader', href: '/pinterest-downloader' },
      { label: 'Reddit Video Downloader', href: '/reddit-video-downloader' },
    ]
  },

  '/youtube-video-downloader': {
    path: '/youtube-video-downloader',
    title: 'YouTube Video Downloader',
    metaDescription: 'Download YouTube videos in 1080p, 720p, or 360p MP4 and high-bitrate MP3 audio. Free, fast, and no registration required.',
    h1: 'YouTube Video Downloader',
    subtitle: 'Save your favorite YouTube videos and Shorts in high definition MP4 or audio MP3 format effortlessly.',
    platform: 'youtube',
    placeholder: 'Paste YouTube video or Shorts URL (e.g. https://youtu.be/...)',
    breadcrumbs: [
      { name: 'Home', path: '/' },
      { name: 'YouTube Video Downloader', path: '/youtube-video-downloader' },
    ],
    howItWorks: [
      'Open YouTube and copy the URL of the video or Short you wish to download.',
      'Paste the URL into the search box above. MediaFlow automatically analyzes available qualities.',
      'Select your desired MP4 resolution (up to 1080p) or MP3 format and click "Download".'
    ],
    specsTitle: 'YouTube Format Specifications & Video Profiles',
    specsDescription: 'We merge high-definition video and high-bitrate audio into universal MP4 files that play natively on all media players and video editing software.',
    features: [
      {
        title: 'Full HD & 60 FPS Support',
        description: 'Preserve high frame rates and original 1080p resolution with merged audio streams.',
        icon: 'hd'
      },
      {
        title: 'YouTube Shorts Compatible',
        description: 'Easily save vertical YouTube Shorts in their native 1080x1920 high resolution.',
        icon: 'zap'
      },
      {
        title: 'Direct Thumbnail Grabber',
        description: 'Download the official HD cover thumbnail with one click without downloading the whole video.',
        icon: 'image'
      },
      {
        title: 'Fast Cloud Processing',
        description: 'Our backend processes streams with dedicated FFmpeg pipelines in just a few seconds.',
        icon: 'server'
      }
    ],
    faqs: [
      {
        question: 'Can I download YouTube Shorts with this tool?',
        answer: 'Yes, our downloader automatically recognizes and processes standard YouTube videos, YouTube Shorts links, and mobile youtu.be share URLs.'
      },
      {
        question: 'Does downloading preserve video sound on 1080p?',
        answer: 'Yes. Our server automatically merges separate high-definition video and audio tracks using FFmpeg to ensure full audio fidelity on all 1080p downloads.'
      },
      {
        question: 'Can I download age-restricted or private YouTube videos?',
        answer: 'No. To respect platform policies and user privacy, our tool only downloads publicly accessible YouTube videos.'
      },
      {
        question: 'Is it legal to download YouTube videos for personal use?',
        answer: 'Downloading videos for personal, offline viewing or fair-use educational backup is generally accepted. You must not sell, redistribute, or use copyrighted media for commercial purposes without explicit permission.'
      }
    ],
    relatedTools: [
      { label: 'YouTube to MP3 Converter', href: '/youtube-to-mp3' },
      { label: 'YouTube to MP4 Downloader', href: '/youtube-to-mp4' },
      { label: 'Instagram Downloader', href: '/instagram-downloader' },
      { label: 'Frequently Asked Questions', href: '/faq' },
    ]
  },

  '/youtube-to-mp3': {
    path: '/youtube-to-mp3',
    title: 'YouTube to MP3 Converter',
    metaDescription: 'Convert and download YouTube videos to high-bitrate MP3 audio files for free. Fast conversion with crystal-clear audio quality on all devices.',
    h1: 'YouTube to MP3 Converter',
    subtitle: 'Extract crystal-clear MP3 audio from any YouTube music video, podcast, lecture, or interview in seconds.',
    platform: 'youtube',
    placeholder: 'Paste YouTube music video or podcast URL here...',
    breadcrumbs: [
      { name: 'Home', path: '/' },
      { name: 'YouTube Video Downloader', path: '/youtube-video-downloader' },
      { name: 'YouTube to MP3 Converter', path: '/youtube-to-mp3' },
    ],
    howItWorks: [
      'Copy the link of any YouTube video or song you want to convert to MP3.',
      'Paste the link into the box above and allow MediaFlow to analyze the stream.',
      'Select the "MP3" tab and click "Download MP3" to save the soundtrack.'
    ],
    specsTitle: 'Audio Extraction Specifications & Quality Tiers',
    specsDescription: 'We extract audio streams in constant high bitrate MP3 format, ensuring universal playback across smartphones, car audio systems, and digital workstations.',
    features: [
      {
        title: 'High Bitrate Audio',
        description: 'Extract audio with high-fidelity bitrates up to 320kbps equivalent audio fidelity.',
        icon: 'music'
      },
      {
        title: 'Universal MP3 Compatibility',
        description: 'Plays smoothly on all car head units, smartphones, MP3 players, and audio workstations.',
        icon: 'headphones'
      },
      {
        title: 'No Software Installation',
        description: 'All audio conversion and post-processing occurs on our cloud engine without draining your battery.',
        icon: 'cloud'
      },
      {
        title: 'Fast Audio Splitting',
        description: 'Streams are extracted cleanly and remuxed in seconds without quality degradation.',
        icon: 'zap'
      }
    ],
    faqs: [
      {
        question: 'What audio format is produced?',
        answer: 'Audio is provided in standard MP3 format (MPEG-1 Audio Layer III), universally supported across all mobile phones, computers, audio players, and sound systems.'
      },
      {
        question: 'Is there any time limit on audio duration?',
        answer: 'Standard YouTube videos, podcasts, and music lectures up to 10 minutes can be converted seamlessly without timeouts.'
      },
      {
        question: 'Does the converted audio include the video title?',
        answer: 'Yes, the downloaded MP3 file is named cleanly using the original video title, making it easy to organize in your music library.'
      },
      {
        question: 'How do I download YouTube MP3 audio on iPhone?',
        answer: 'Paste the link in Apple Safari, tap "Download MP3", confirm the download prompt, and open the audio file from Safari’s downloads manager into Apple Files or your music player.'
      }
    ],
    relatedTools: [
      { label: 'YouTube Video Downloader', href: '/youtube-video-downloader' },
      { label: 'YouTube to MP4 Downloader', href: '/youtube-to-mp4' },
      { label: 'Instagram Reels Downloader', href: '/instagram-reels-downloader' },
    ]
  },

  '/youtube-to-mp4': {
    path: '/youtube-to-mp4',
    title: 'YouTube to MP4 Converter',
    metaDescription: 'Convert and save YouTube videos as MP4 files in 1080p, 720p, and standard definition. Free, fast and compatible with all media players.',
    h1: 'YouTube to MP4 Converter',
    subtitle: 'Download YouTube videos in universal MP4 format with perfectly synchronized video and audio playback.',
    platform: 'youtube',
    placeholder: 'Paste YouTube video link to download MP4...',
    breadcrumbs: [
      { name: 'Home', path: '/' },
      { name: 'YouTube Video Downloader', path: '/youtube-video-downloader' },
      { name: 'YouTube to MP4 Downloader', path: '/youtube-to-mp4' },
    ],
    howItWorks: [
      'Copy the YouTube video link from your browser address bar or the YouTube mobile app.',
      'Paste the URL into the input field above.',
      'Select your desired MP4 resolution (e.g. 1080p Full HD or 720p HD) and click "Download MP4".'
    ],
    specsTitle: 'MP4 Video Encoding & Compatibility Specifications',
    specsDescription: 'All MP4 videos are delivered in standard H.264 profile with AAC stereo audio for hardware-accelerated playback on all modern GPUs and displays.',
    features: [
      {
        title: 'Clean MP4 Container',
        description: 'Standard H.264 video with AAC audio that plays on any computer, TV, or mobile device.',
        icon: 'video'
      },
      {
        title: 'Multiple Resolution Choices',
        description: 'Choose between 1080p Full HD, 720p HD, 480p, or 360p depending on your bandwidth needs.',
        icon: 'sliders'
      },
      {
        title: 'Instant Download Speeds',
        description: 'Direct high-speed streaming ensures files download at your maximum internet speed.',
        icon: 'zap'
      },
      {
        title: 'Safe & Clean Experience',
        description: 'Zero bloatware, zero intrusive browser extensions, and zero popup traps.',
        icon: 'shield'
      }
    ],
    faqs: [
      {
        question: 'Why choose MP4 format for video downloads?',
        answer: 'MP4 is the global standard video container. It guarantees seamless hardware-accelerated playback on iPhone, Android, Windows, Mac, smart TVs, and video editing suites like Premiere and Final Cut.'
      },
      {
        question: 'Can I choose different video resolutions?',
        answer: 'Yes. After analyzing the video, our tool lists all resolutions offered by the source video, including 1080p, 720p, and 360p MP4.'
      },
      {
        question: 'Will 1080p MP4 videos have sound?',
        answer: 'Yes! MediaFlow automatically combines the high-definition video track with the high-quality AAC audio track on our cloud server so your MP4 video has full, clear sound.'
      }
    ],
    relatedTools: [
      { label: 'YouTube Video Downloader', href: '/youtube-video-downloader' },
      { label: 'YouTube to MP3 Converter', href: '/youtube-to-mp3' },
      { label: 'Instagram Downloader', href: '/instagram-downloader' },
    ]
  },

  '/instagram-downloader': {
    path: '/instagram-downloader',
    title: 'Instagram Video Downloader',
    metaDescription: 'Download Instagram videos, Reels, and photos in high quality. Fast, safe, free, and works on all desktop and mobile browsers.',
    h1: 'Instagram Video Downloader',
    subtitle: 'Save public Instagram videos, Reels, IGTV, and high-resolution photos effortlessly to your device.',
    platform: 'instagram',
    placeholder: 'Paste Instagram post or reel link (e.g. https://www.instagram.com/reel/...)',
    breadcrumbs: [
      { name: 'Home', path: '/' },
      { name: 'Instagram Downloader', path: '/instagram-downloader' },
    ],
    howItWorks: [
      'Open Instagram and copy the share link of the public post, reel, or video.',
      'Paste the link into the box above and tap "Search".',
      'Preview the media, select your format, and tap "Download" to save.'
    ],
    specsTitle: 'Instagram Media Extraction Specifications',
    specsDescription: 'MediaFlow preserves the original Instagram upload fidelity (up to 1080x1920 vertical format) with original audio tracks and zero added watermarks.',
    features: [
      {
        title: 'Reels & Video Posts',
        description: 'Download full-length Instagram Reels and video posts with complete sound.',
        icon: 'film'
      },
      {
        title: 'Original Visual Quality',
        description: 'Save media in the exact original quality uploaded by the creator.',
        icon: 'sparkles'
      },
      {
        title: 'Mobile-Friendly Design',
        description: 'Optimized touch experience specifically designed for smartphones and tablets.',
        icon: 'smartphone'
      },
      {
        title: 'No App Login Required',
        description: 'Download public content without entering your Instagram login or password.',
        icon: 'lock'
      }
    ],
    faqs: [
      {
        question: 'Do I need an Instagram account or login to download?',
        answer: 'No. You do not need to log in or share any Instagram credentials. Only the public link is required to extract and save media.'
      },
      {
        question: 'Can I download private Instagram posts or stories?',
        answer: 'No. To protect user privacy and respect account security, private Instagram accounts and private stories cannot be downloaded.'
      },
      {
        question: 'Where can I find the link to an Instagram post or Reel?',
        answer: 'Tap the three dots (...) or the Share airplane icon on the Instagram post and choose "Copy link".'
      },
      {
        question: 'Does MediaFlow add watermarks to downloaded Instagram videos?',
        answer: 'No! MediaFlow provides clean original video files with zero watermarks, logos, or overlay branding.'
      }
    ],
    relatedTools: [
      { label: 'Instagram Reels Downloader', href: '/instagram-reels-downloader' },
      { label: 'YouTube Video Downloader', href: '/youtube-video-downloader' },
      { label: 'FAQ', href: '/faq' },
    ]
  },

  '/instagram-reels-downloader': {
    path: '/instagram-reels-downloader',
    title: 'Instagram Reels Downloader',
    metaDescription: 'Download Instagram Reels in high definition MP4 with original sound. Fast, easy, and free on iPhone, Android, and PC.',
    h1: 'Instagram Reels Downloader',
    subtitle: 'Save trending Instagram Reels with crystal-clear audio to watch offline or share with friends.',
    platform: 'instagram',
    placeholder: 'Paste Instagram Reel URL here (e.g. https://instagram.com/reel/...)',
    breadcrumbs: [
      { name: 'Home', path: '/' },
      { name: 'Instagram Downloader', path: '/instagram-downloader' },
      { name: 'Instagram Reels Downloader', path: '/instagram-reels-downloader' },
    ],
    howItWorks: [
      'Open the Instagram Reel you want to save and tap "Share" -> "Copy link".',
      'Paste the Reel link into our downloader search bar.',
      'Click "Search", preview the Reel, and click "Download MP4" to save.'
    ],
    specsTitle: 'Instagram Reels Technical Specifications',
    specsDescription: 'Reels are downloaded in native 9:16 vertical MP4 format with complete multi-channel audio tracks preserved.',
    features: [
      {
        title: 'Complete Audio Sync',
        description: 'Full audio track and original voiceover preserved in high bitrate MP4.',
        icon: 'music'
      },
      {
        title: 'Fast Cloud Processing',
        description: 'Short Reels are processed and ready for download within 3 to 5 seconds.',
        icon: 'zap'
      },
      {
        title: 'No Watermark Added',
        description: 'Save the original media file cleanly without any added logos or watermarks.',
        icon: 'check-circle'
      },
      {
        title: 'Direct Downloads',
        description: 'Save personal Reel downloads directly to your device without paywalls or subscriptions.',
        icon: 'download'
      }
    ],
    faqs: [
      {
        question: 'Are downloaded Reels saved with sound?',
        answer: 'Yes! All Reels downloaded through MediaFlow retain their full original audio, background music, and voice tracks.'
      },
      {
        question: 'How do I save an Instagram Reel to my iPhone Photos camera roll?',
        answer: 'Paste the Reel link in Apple Safari, tap "Download MP4", confirm the download, tap the Safari blue download arrow, open the video, and tap the share sheet icon to select "Save Video".'
      },
      {
        question: 'Can I download Reels from private Instagram profiles?',
        answer: 'No. Private profiles require explicit follower permissions, and MediaFlow only processes publicly accessible media to honor creator privacy.'
      }
    ],
    relatedTools: [
      { label: 'Instagram Downloader', href: '/instagram-downloader' },
      { label: 'YouTube Video Downloader', href: '/youtube-video-downloader' },
      { label: 'X Video Downloader', href: '/x-video-downloader' },
    ]
  },

  '/x-video-downloader': {
    path: '/x-video-downloader',
    title: 'X Video Downloader - Download X Videos Online',
    metaDescription: 'Download compatible public X (Twitter) videos and GIFs in high-definition MP4 or extract MP3 audio. Fast, secure, and mobile-friendly with no registration.',
    h1: 'X Video Downloader',
    subtitle: 'Save public videos and clips from X (formerly Twitter) directly to your device with crystal-clear playback and synchronized audio.',
    platform: 'x',
    placeholder: 'Paste X or Twitter post link here (e.g. https://x.com/username/status/...)',
    breadcrumbs: [
      { name: 'Home', path: '/' },
      { name: 'X Video Downloader', path: '/x-video-downloader' },
    ],
    howItWorks: [
      'Copy the link of any public post or clip from X or Twitter.',
      'Paste the URL into MediaFlow and click "Search" to analyze available media streams.',
      'Select your preferred video resolution (1080p, 720p, 480p) or MP3 audio and click Download.'
    ],
    specsTitle: 'Supported X Media Specifications',
    specsDescription: 'MediaFlow extracts compatible public video and audio streams from X and packages them into universal H.264 MP4 or MP3 files.',
    features: [
      {
        title: 'Full HD 1080p & 720p',
        description: 'Download crisp high-definition video clips with original frame rates and complete audio tracks intact.',
        icon: 'hd'
      },
      {
        title: 'Instant Audio Extraction',
        description: 'Extract pristine MP3 audio from interviews, commentary, and music clips shared on X.',
        icon: 'music'
      },
      {
        title: 'Direct Browser Downloads',
        description: 'No apps, third-party software, or browser extensions needed. Works instantly across all devices.',
        icon: 'zap'
      },
      {
        title: 'Privacy Guaranteed',
        description: 'No account registration, no login tokens, and files are automatically purged from temporary storage.',
        icon: 'shield'
      }
    ],
    faqs: [
      {
        question: 'Can I download videos from private X accounts?',
        answer: 'No. MediaFlow strictly respects user privacy and creator permissions. Only compatible public posts can be analyzed and downloaded.'
      },
      {
        question: 'What video resolutions are available for X clips?',
        answer: 'Available resolutions depend on what the original poster uploaded, commonly ranging from 360p up to 1080p Full HD in universal MP4 format.'
      },
      {
        question: 'Do I need to sign in with my Twitter or X account?',
        answer: 'No. MediaFlow never requires your personal credentials, passwords, or account authentication.'
      }
    ],
    relatedTools: [
      { label: 'Instagram Downloader', href: '/instagram-downloader' },
      { label: 'Facebook Video Downloader', href: '/facebook-video-downloader' },
      { label: 'Reddit Video Downloader', href: '/reddit-video-downloader' },
      { label: 'YouTube Video Downloader', href: '/youtube-video-downloader' },
    ]
  },

  '/facebook-video-downloader': {
    path: '/facebook-video-downloader',
    title: 'Facebook Video Downloader - Download Facebook Videos Online',
    metaDescription: 'Download compatible public Facebook videos and Reels in HD MP4 or extract MP3 audio. Free, secure, and fast with no account required.',
    h1: 'Facebook Video Downloader',
    subtitle: 'Save public Facebook videos, Reels, and clips to your device in high-definition MP4 format with crisp audio.',
    platform: 'facebook',
    placeholder: 'Paste Facebook video or Reel link here (e.g. https://www.facebook.com/watch/?v=...)',
    breadcrumbs: [
      { name: 'Home', path: '/' },
      { name: 'Facebook Video Downloader', path: '/facebook-video-downloader' },
    ],
    howItWorks: [
      'Copy the link of any public Facebook video, Reel, or fb.watch post.',
      'Paste the link into the search box above and click "Search".',
      'Choose HD or SD quality and save the standardized MP4 file to your device.'
    ],
    specsTitle: 'Facebook Video Specifications',
    specsDescription: 'Outputs standard MP4 video encoded with H.264 and AAC for seamless playback on any device.',
    features: [
      {
        title: 'HD & SD Stream Selection',
        description: 'Choose between High Definition (720p/1080p) or Standard Definition for bandwidth savings.',
        icon: 'hd'
      },
      {
        title: 'Reels & Short Clips',
        description: 'Full compatibility with public Facebook Reels and mobile fb.watch short links.',
        icon: 'zap'
      },
      {
        title: 'Instant Audio Converter',
        description: 'Extract high-quality MP3 audio from interviews, public speeches, and music performances.',
        icon: 'music'
      },
      {
        title: 'Cross-Device Playback',
        description: 'Universal MP4 files open effortlessly in VLC, QuickTime, Windows Media Player, iOS, and Android.',
        icon: 'check-circle'
      }
    ],
    faqs: [
      {
        question: 'Does MediaFlow support private Facebook videos or closed groups?',
        answer: 'No. Only publicly accessible Facebook videos and Reels can be processed. Private posts, closed groups, and friend-only media are strictly protected.'
      },
      {
        question: 'Are mobile fb.watch links supported?',
        answer: 'Yes! You can paste desktop facebook.com URLs, mobile m.facebook.com links, or fb.watch shortlinks.'
      },
      {
        question: 'Is there any limit on video duration?',
        answer: 'MediaFlow comfortably processes public clips up to 30 minutes in duration efficiently.'
      }
    ],
    relatedTools: [
      { label: 'Instagram Reels Downloader', href: '/instagram-reels-downloader' },
      { label: 'X Video Downloader', href: '/x-video-downloader' },
      { label: 'Pinterest Downloader', href: '/pinterest-downloader' },
      { label: 'YouTube Video Downloader', href: '/youtube-video-downloader' },
    ]
  },

  '/pinterest-downloader': {
    path: '/pinterest-downloader',
    title: 'Pinterest Video & Image Downloader - Download Pinterest Media',
    metaDescription: 'Download compatible public Pinterest video pins and full-resolution photo pins. Fast, free, and works without installing apps.',
    h1: 'Pinterest Downloader',
    subtitle: 'Save high-resolution images, creative ideas, and video pins from Pinterest directly to your device.',
    platform: 'pinterest',
    placeholder: 'Paste Pinterest pin or pin.it link here (e.g. https://www.pinterest.com/pin/...)',
    breadcrumbs: [
      { name: 'Home', path: '/' },
      { name: 'Pinterest Downloader', path: '/pinterest-downloader' },
    ],
    howItWorks: [
      'Copy the URL of a public pin or pin.it link from Pinterest.',
      'Paste the URL into MediaFlow and click "Search" to detect whether it is a video or image.',
      'Click Download to save the original high-resolution photo or MP4 video.'
    ],
    specsTitle: 'Pinterest Media Capabilities',
    specsDescription: 'Automatically identifies whether a pin contains an image or video and delivers the media in original fidelity.',
    features: [
      {
        title: 'Dual Video & Photo Support',
        description: 'Smart detection automatically identifies video pins versus high-resolution still images.',
        icon: 'hd'
      },
      {
        title: 'Original Quality Retention',
        description: 'Preserves the highest resolution available from the creator without downsampling.',
        icon: 'check-circle'
      },
      {
        title: 'Mobile pin.it Shortlinks',
        description: 'Seamlessly resolves short share links generated by the mobile Pinterest app.',
        icon: 'zap'
      },
      {
        title: 'Safe & Watermark-Free',
        description: 'Downloads clean media files without any injected branding or watermarks.',
        icon: 'shield'
      }
    ],
    faqs: [
      {
        question: 'Can I download images as well as videos from Pinterest?',
        answer: 'Yes! If a pin is an image, MediaFlow lets you download the full-resolution photo. If it is a video, you can download the MP4 file.'
      },
      {
        question: 'Do pin.it mobile links work?',
        answer: 'Yes. You can paste mobile pin.it links directly without needing to expand them first.'
      },
      {
        question: 'Can I download secret board pins?',
        answer: 'No. MediaFlow only processes publicly accessible pins to respect user confidentiality.'
      }
    ],
    relatedTools: [
      { label: 'Instagram Downloader', href: '/instagram-downloader' },
      { label: 'Reddit Video Downloader', href: '/reddit-video-downloader' },
      { label: 'Facebook Video Downloader', href: '/facebook-video-downloader' },
      { label: 'YouTube to MP4 Downloader', href: '/youtube-to-mp4' },
    ]
  },

  '/reddit-video-downloader': {
    path: '/reddit-video-downloader',
    title: 'Reddit Video Downloader - Download Reddit Videos Online',
    metaDescription: 'Download Reddit videos with sound in HD MP4. Merges separated audio and video streams automatically for free without watermark.',
    h1: 'Reddit Video Downloader',
    subtitle: 'Download public Reddit videos and clips with synchronized sound in universal MP4 format.',
    platform: 'reddit',
    placeholder: 'Paste Reddit post or v.redd.it link here (e.g. https://www.reddit.com/r/.../comments/...)',
    breadcrumbs: [
      { name: 'Home', path: '/' },
      { name: 'Reddit Video Downloader', path: '/reddit-video-downloader' },
    ],
    howItWorks: [
      'Copy the link of any public Reddit post or v.redd.it clip.',
      'Paste the URL into the search box and click "Search".',
      'Select your preferred resolution and click Download to get the full video with audio.'
    ],
    specsTitle: 'Reddit Audio-Video Synchronization',
    specsDescription: 'Reddit hosts video and audio on separate DASH streams (v.redd.it). MediaFlow merges them with FFmpeg into a single synchronized MP4.',
    features: [
      {
        title: 'Synchronized Sound',
        description: 'Automatically merges separated Reddit video and audio tracks into a complete playable MP4 file.',
        icon: 'music'
      },
      {
        title: 'Multiple Resolutions',
        description: 'Choose from available tiers including 1080p, 720p, 480p, and 360p based on source availability.',
        icon: 'hd'
      },
      {
        title: 'MP3 Audio Extraction',
        description: 'Easily extract pure MP3 audio from podcasts, comedy clips, and interviews shared on Reddit.',
        icon: 'zap'
      },
      {
        title: 'Cross-Reddit Compatibility',
        description: 'Works with desktop Reddit, old.reddit.com, v.redd.it direct streams, and redd.it links.',
        icon: 'check-circle'
      }
    ],
    faqs: [
      {
        question: 'Why do Reddit videos normally download without sound on other sites?',
        answer: 'Reddit stores video and audio tracks separately. MediaFlow merges both streams on the fly using our cloud engine so your downloaded MP4 always has full sound.'
      },
      {
        question: 'Can I download videos from private subreddits?',
        answer: 'No. MediaFlow only accesses compatible public Reddit communities and posts.'
      },
      {
        question: 'Does it support old.reddit.com and redd.it shortlinks?',
        answer: 'Yes! Links from new Reddit, old.reddit.com, v.redd.it, and redd.it are all supported.'
      }
    ],
    relatedTools: [
      { label: 'X Video Downloader', href: '/x-video-downloader' },
      { label: 'YouTube Video Downloader', href: '/youtube-video-downloader' },
      { label: 'Instagram Reels Downloader', href: '/instagram-reels-downloader' },
      { label: 'Pinterest Downloader', href: '/pinterest-downloader' },
    ]
  },

  '/faq': {
    path: '/faq',
    title: 'Frequently Asked Questions',
    metaDescription: 'Get answers to common questions about using MediaFlow to download YouTube and Instagram videos, MP3 audio, file formats, and troubleshooting.',
    h1: 'Frequently Asked Questions',
    subtitle: 'Find comprehensive answers to common questions about downloading video and audio files with MediaFlow.',
    platform: 'all',
    placeholder: 'Paste any video URL to start downloading...',
    breadcrumbs: [
      { name: 'Home', path: '/' },
      { name: 'Frequently Asked Questions', path: '/faq' },
    ],
    howItWorks: [
      'Find the answer to your question below.',
      'If you need to download a video, paste your link in the search bar above.',
      'Contact our support team if your question is not covered in our FAQ.'
    ],
    features: [],
    faqs: [
      {
        question: 'Is MediaFlow completely free to use?',
        answer: 'Yes! MediaFlow is free to use with no hidden subscriptions or fees.'
      },
      {
        question: 'What video quality formats are supported?',
        answer: 'We support MP4 video formats from 360p up to 1080p Full HD, as well as MP3 audio extraction and original JPEG/WebP thumbnail downloads.'
      },
      {
        question: 'Why does 1080p video take slightly longer to prepare than 720p?',
        answer: 'YouTube stores 1080p video and audio as separate streams (adaptive DASH). To deliver an MP4 with full sound, MediaFlow must mux the audio and video streams together on our cloud server using FFmpeg before serving the file.'
      },
      {
        question: 'Why did my download fail or show an error?',
        answer: 'Downloads can fail if the video is private, age-restricted, removed by its owner, or if the source website is temporarily throttling requests. Check that the link is public and works in an incognito browser window.'
      },
      {
        question: 'How long are my prepared files kept on the server?',
        answer: 'To protect user privacy and preserve storage, all prepared media files are automatically purged from our cloud servers after 30 minutes.'
      },
      {
        question: 'Is it legal to download YouTube and Instagram videos?',
        answer: 'Downloading videos for personal, offline viewing or archiving is widely considered fair use. However, you must not commercially redistribute, sell, or claim ownership over copyrighted materials.'
      }
    ],
    relatedTools: [
      { label: 'YouTube Video Downloader', href: '/youtube-video-downloader' },
      { label: 'Instagram Downloader', href: '/instagram-downloader' },
      { label: 'Terms of Service', href: '/terms' },
      { label: 'Privacy Policy', href: '/privacy-policy' },
    ]
  },

  '/about': {
    path: '/about',
    title: 'About MediaFlow',
    metaDescription: 'Learn about MediaFlow, our mission to provide the fastest, cleanest, and most reliable video and audio downloader for the modern web.',
    h1: 'About MediaFlow',
    subtitle: 'A high-performance video and audio extraction engine built for speed, simplicity, and strict user privacy.',
    platform: 'all',
    placeholder: 'Paste any video URL to start downloading...',
    breadcrumbs: [
      { name: 'Home', path: '/' },
      { name: 'About MediaFlow', path: '/about' },
    ],
    howItWorks: [],
    features: [],
    faqs: [],
    relatedTools: [
      { label: 'Home', href: '/' },
      { label: 'Frequently Asked Questions', href: '/faq' },
      { label: 'Contact Support', href: '/contact' },
    ]
  },

  '/contact': {
    path: '/contact',
    title: 'Contact Support',
    metaDescription: 'Get in touch with the MediaFlow team for customer support, feature suggestions, bug reports, or copyright DMCA inquiries.',
    h1: 'Contact & Support',
    subtitle: 'Have a question, feedback, or DMCA inquiry? Our team is here to assist you.',
    platform: 'all',
    placeholder: 'Paste video URL here...',
    breadcrumbs: [
      { name: 'Home', path: '/' },
      { name: 'Contact & Support', path: '/contact' },
    ],
    howItWorks: [],
    features: [],
    faqs: [],
    relatedTools: [
      { label: 'FAQ', href: '/faq' },
      { label: 'Terms of Service', href: '/terms' },
      { label: 'Privacy Policy', href: '/privacy-policy' },
    ]
  },

  '/privacy-policy': {
    path: '/privacy-policy',
    title: 'Privacy Policy',
    metaDescription: 'Read our transparent Privacy Policy. Learn how MediaFlow protects your data and privacy with zero permanent tracking and auto-purging files.',
    h1: 'Privacy Policy',
    subtitle: 'Our commitment to protecting your privacy, data security, and digital confidentiality.',
    platform: 'all',
    placeholder: 'Paste video URL here...',
    breadcrumbs: [
      { name: 'Home', path: '/' },
      { name: 'Privacy Policy', path: '/privacy-policy' },
    ],
    howItWorks: [],
    features: [],
    faqs: [],
    relatedTools: [
      { label: 'Terms of Service', href: '/terms' },
      { label: 'Frequently Asked Questions', href: '/faq' },
      { label: 'Home', href: '/' },
    ]
  },

  '/terms': {
    path: '/terms',
    title: 'Terms of Service',
    metaDescription: 'Review the Terms of Service governing your use of MediaFlow, personal use conditions, and intellectual property disclaimers.',
    h1: 'Terms of Service',
    subtitle: 'Terms and conditions governing the lawful, personal use of the MediaFlow service.',
    platform: 'all',
    placeholder: 'Paste video URL here...',
    breadcrumbs: [
      { name: 'Home', path: '/' },
      { name: 'Terms of Service', path: '/terms' },
    ],
    howItWorks: [],
    features: [],
    faqs: [],
    relatedTools: [
      { label: 'Privacy Policy', href: '/privacy-policy' },
      { label: 'Frequently Asked Questions', href: '/faq' },
      { label: 'Home', href: '/' },
    ]
  },
};
