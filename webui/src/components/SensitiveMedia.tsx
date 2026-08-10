import { Button } from "@heroui/react";
import { IconPhotoOff, IconRefresh } from "@tabler/icons-react";
import { useState, type CSSProperties, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { useSensitiveMediaEnabled } from "../lib/sensitiveMedia";
import type { MediaAsset } from "../types";

type MediaVariant = "thumbnail" | "preview" | "original";

function assetSource(asset: MediaAsset, variant: MediaVariant): string {
  if (variant === "original") return asset.original_url;
  if (variant === "preview") return asset.preview_url;
  return asset.thumbnail_url;
}

function retrySource(source: string, attempt: number): string {
  if (!attempt) return source;
  return `${source}${source.includes("?") ? "&" : "?"}retry=${attempt}`;
}

export function SensitiveMediaImage({
  asset,
  alt,
  className,
  fallback,
  showRetry = false,
  variant = "thumbnail",
}: {
  asset?: MediaAsset | null;
  alt: string;
  className?: string;
  fallback?: ReactNode;
  showRetry?: boolean;
  variant?: MediaVariant;
}) {
  const { t } = useTranslation();
  const enabled = useSensitiveMediaEnabled();
  const source = asset ? assetSource(asset, variant) : null;
  const [failedSource, setFailedSource] = useState<string | null>(null);
  const [retryState, setRetryState] = useState<{ source: string; attempt: number } | null>(null);
  const failed = Boolean(source && failedSource === source);
  const attempt = source && retryState?.source === source ? retryState.attempt : 0;

  if (!enabled) return null;
  if (!source || failed) {
    return (
      <div className={className} data-media-fallback="true">
        {fallback !== undefined ? fallback : (
          <div className="media-unavailable flex size-full flex-col items-center justify-center gap-2 text-center text-muted">
            <IconPhotoOff aria-hidden="true" size={22} />
            <span className="text-xs">{t("sensitiveMedia.unavailable")}</span>
            {showRetry && source ? (
              <Button
                size="sm"
                variant="ghost"
                onPress={() => {
                  setFailedSource(null);
                  setRetryState((current) => ({
                    source,
                    attempt: current?.source === source ? current.attempt + 1 : 1,
                  }));
                }}
              >
                <IconRefresh aria-hidden="true" size={15} />
                {t("sensitiveMedia.retry")}
              </Button>
            ) : null}
          </div>
        )}
      </div>
    );
  }

  return (
    <img
      alt={alt}
      className={className}
      decoding="async"
      loading="lazy"
      src={retrySource(source, attempt)}
      onError={() => setFailedSource(source)}
    />
  );
}

const avatarSizes = {
  xs: 28,
  sm: 36,
  md: 44,
  lg: 64,
} as const;

export function CreatorAvatar({
  asset,
  name,
  size = "sm",
  className = "",
}: {
  asset?: MediaAsset | null;
  name: string;
  size?: keyof typeof avatarSizes;
  className?: string;
}) {
  const { t } = useTranslation();
  const enabled = useSensitiveMediaEnabled();
  if (!enabled) return null;
  const pixels = avatarSizes[size];
  const initial = Array.from(name.trim())[0]?.toLocaleUpperCase() ?? "?";
  const style = { "--creator-avatar-size": `${pixels}px` } as CSSProperties;
  return (
    <span
      className={`creator-avatar relative inline-grid shrink-0 place-items-center overflow-hidden rounded-full ${className}`}
      data-testid="creator-avatar"
      style={style}
    >
      <span aria-hidden="true" className="creator-avatar-initial">{initial}</span>
      <SensitiveMediaImage
        alt={t("sensitiveMedia.avatarAlt", { name })}
        asset={asset}
        className="absolute inset-0 size-full object-cover"
        fallback={null}
      />
    </span>
  );
}

export function CreatorBanner({
  asset,
  name,
  className = "",
}: {
  asset?: MediaAsset | null;
  name: string;
  className?: string;
}) {
  const { t } = useTranslation();
  const enabled = useSensitiveMediaEnabled();
  if (!enabled) return null;
  return (
    <div className={`creator-banner relative overflow-hidden ${className}`} data-testid="creator-banner">
      <SensitiveMediaImage
        alt={t("sensitiveMedia.bannerAlt", { name })}
        asset={asset}
        className="absolute inset-0 size-full object-cover"
        fallback={null}
      />
    </div>
  );
}
