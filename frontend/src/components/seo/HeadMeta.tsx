import React, { useEffect } from 'react';
import { appConfig, getCanonicalUrl } from '../../config/appConfig';
import { generateJsonLdGraph, type BreadcrumbItem } from '../../utils/seoHelpers';

export interface HeadMetaProps {
  title: string;
  description: string;
  canonicalPath: string;
  ogType?: string;
  ogImage?: string;
  breadcrumbs?: BreadcrumbItem[];
  isToolPage?: boolean;
}

export const HeadMeta: React.FC<HeadMetaProps> = ({
  title,
  description,
  canonicalPath,
  ogType = 'website',
  ogImage,
  breadcrumbs,
  isToolPage,
}) => {
  useEffect(() => {
    // 1. Title
    document.title = title;

    // 2. Meta description
    let descTag = document.querySelector('meta[name="description"]');
    if (!descTag) {
      descTag = document.createElement('meta');
      descTag.setAttribute('name', 'description');
      document.head.appendChild(descTag);
    }
    descTag.setAttribute('content', description);

    // 3. Canonical URL
    const fullCanonical = getCanonicalUrl(canonicalPath);
    let canonicalTag = document.querySelector('link[rel="canonical"]');
    if (!canonicalTag) {
      canonicalTag = document.createElement('link');
      canonicalTag.setAttribute('rel', 'canonical');
      document.head.appendChild(canonicalTag);
    }
    canonicalTag.setAttribute('href', fullCanonical);

    // 4. Open Graph
    const setOgTag = (property: string, content: string) => {
      let tag = document.querySelector(`meta[property="${property}"]`);
      if (!tag) {
        tag = document.createElement('meta');
        tag.setAttribute('property', property);
        document.head.appendChild(tag);
      }
      tag.setAttribute('content', content);
    };

    const effectiveImage = ogImage || `${appConfig.canonicalDomain}/og-image.png`;

    setOgTag('og:title', title);
    setOgTag('og:description', description);
    setOgTag('og:url', fullCanonical);
    setOgTag('og:type', ogType);
    setOgTag('og:site_name', appConfig.brandName);
    setOgTag('og:image', effectiveImage);

    // 5. Twitter Card
    const setTwitterTag = (name: string, content: string) => {
      let tag = document.querySelector(`meta[name="${name}"]`);
      if (!tag) {
        tag = document.createElement('meta');
        tag.setAttribute('name', name);
        document.head.appendChild(tag);
      }
      tag.setAttribute('content', content);
    };
    setTwitterTag('twitter:card', 'summary_large_image');
    setTwitterTag('twitter:url', fullCanonical);
    setTwitterTag('twitter:title', title);
    setTwitterTag('twitter:description', description);
    setTwitterTag('twitter:image', effectiveImage);

    // 6. JSON-LD Structured Data
    const effectiveSchema = generateJsonLdGraph({
      title,
      description,
      canonicalPath,
      ogType,
      ogImage: effectiveImage,
      breadcrumbs,
      isToolPage,
    });

    let scriptTag = document.getElementById('json-ld-schema') as HTMLScriptElement;
    if (!scriptTag) {
      scriptTag = document.createElement('script');
      scriptTag.id = 'json-ld-schema';
      scriptTag.type = 'application/ld+json';
      document.head.appendChild(scriptTag);
    }
    scriptTag.textContent = JSON.stringify(effectiveSchema, null, 2);
  }, [title, description, canonicalPath, ogType, ogImage, breadcrumbs, isToolPage]);

  return null;
};
