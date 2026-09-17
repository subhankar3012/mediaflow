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
  platform: 'youtube' | 'instagram' | 'all';
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
    title: 'Free Online Media Downloader - YouTube & Instagram MP4, MP3 | MediaFlow',
    metaDescription: 'Download high quality videos and audio from YouTube and Instagram for free. Fast, secure, and mobile-friendly with MP4, MP3, and thumbnail options.',
    h1: 'Online Video & Audio Downloader',
    subtitle: 'Paste any YouTube or Instagram link to download high-speed MP4 video, MP3 audio, or full-resolution thumbnails with zero quality loss.',
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
        description: 'Extract pristine MP3 and M4A audio from music videos, podcasts, and lectures with zero bitrate loss.',
        icon: 'music'
      },
      {
        title: '100% Free & No Registration',
        description: 'No accounts, no email captures, and no software installations. Unlimited personal downloads.',
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
        question: 'Is this media downloader completely free to use?',
        answer: 'Yes! MediaFlow is 100% free with no limits on personal downloads and requires no account registration or payment details.'
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
      { label: 'YouTube to MP3 Converter', href: '/youtube-to-mp3' },
      { label: 'YouTube to MP4 Downloader', href: '/youtube-to-mp4' },
      { label: 'Instagram Downloader', href: '/instagram-downloader' },
      { label: 'Instagram Reels Downloader', href: '/instagram-reels-downloader' },
    ]
  },

  '/youtube-video-downloader': {
    path: '/youtube-video-downloader',
    title: 'YouTube Video Downloader - Download YouTube Videos in HD MP4 & MP3 | MediaFlow',
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
    title: 'YouTube to MP3 Converter - Free High Quality Audio Downloader | MediaFlow',
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
    title: 'YouTube to MP4 Downloader - Download 1080p & 720p HD MP4 | MediaFlow',
    metaDescription: 'Convert and save YouTube videos as MP4 files in 1080p, 720p, and standard definition. Free, fast and compatible with all media players.',
    h1: 'YouTube to MP4 Downloader',
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
    title: 'Instagram Video & Photo Downloader - Save IG Videos, Reels & Posts | MediaFlow',
    metaDescription: 'Download Instagram videos, Reels, and photos in high quality. Fast, safe, free, and works on all desktop and mobile browsers.',
    h1: 'Instagram Video & Photo Downloader',
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
    title: 'Instagram Reels Downloader - Save IG Reels in HD MP4 with Audio | MediaFlow',
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
        title: 'Unlimited Downloads',
        description: 'Enjoy unlimited personal Reel downloads without limits, paywalls, or quotas.',
        icon: 'infinity'
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
      { label: 'YouTube to MP3 Converter', href: '/youtube-to-mp3' },
    ]
  },

  '/faq': {
    path: '/faq',
    title: 'Frequently Asked Questions - MediaFlow Downloader Help & FAQs',
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
        answer: 'Yes! MediaFlow is 100% free with no hidden subscriptions, fees, or daily download quotas.'
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
    title: 'About MediaFlow - Fast & High-Definition Media Downloader',
    metaDescription: 'Learn about MediaFlow, our mission to provide the fastest, cleanest, and most reliable video and audio downloader for the modern web.',
    h1: 'About MediaFlow',
    subtitle: 'A high-performance media extraction engine built for speed, simplicity, and strict user privacy.',
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
    title: 'Contact Support & Feedback - MediaFlow Downloader',
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
    title: 'Privacy Policy - MediaFlow Media Downloader',
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
    title: 'Terms of Service & Copyright Disclaimer - MediaFlow Downloader',
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
