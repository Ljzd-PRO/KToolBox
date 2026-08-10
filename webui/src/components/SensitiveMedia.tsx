import { Button, Chip } from "@heroui/react";
import {
  IconChevronLeft,
  IconChevronRight,
  IconPhoto,
  IconPhotoOff,
  IconRefresh,
} from "@tabler/icons-react";
import { useEffect, useMemo, useState, type CSSProperties, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { useSensitiveMediaEnabled } from "../lib/sensitiveMedia";
import type { MediaAsset } from "../types";
import { ConfirmModal } from "./ui";

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

export function MediaThumbnailButton({
  asset,
  alt,
  className = "",
  fit = "cover",
  onPress,
}: {
  asset: MediaAsset;
  alt: string;
  className?: string;
  fit?: "contain" | "cover";
  onPress: () => void;
}) {
  const { t } = useTranslation();
  const enabled = useSensitiveMediaEnabled();
  const [failedSource, setFailedSource] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const source = asset.thumbnail_url;
  const failed = failedSource === source;

  if (!enabled) return null;
  if (failed) {
    return (
      <div className={`media-thumbnail-frame media-unavailable flex flex-col items-center justify-center gap-2 text-center text-muted ${className}`}>
        <IconPhotoOff aria-hidden="true" size={20} />
        <span className="text-xs">{t("sensitiveMedia.unavailable")}</span>
        <Button
          size="sm"
          variant="ghost"
          onPress={() => {
            setFailedSource(null);
            setAttempt((value) => value + 1);
          }}
        >
          <IconRefresh aria-hidden="true" size={14} />
          {t("sensitiveMedia.retry")}
        </Button>
      </div>
    );
  }

  return (
    <button
      aria-label={alt}
      className={`media-thumbnail-frame group relative block overflow-hidden text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 ${className}`}
      type="button"
      onClick={onPress}
    >
      <img
        alt={alt}
        className={`size-full transition-transform duration-200 group-hover:scale-[1.025] ${fit === "contain" ? "object-contain" : "object-cover"}`}
        decoding="async"
        loading="lazy"
        src={retrySource(source, attempt)}
        onError={() => setFailedSource(source)}
      />
      <span aria-hidden="true" className="absolute inset-0 bg-black/0 transition-colors group-hover:bg-black/10" />
    </button>
  );
}

export function WorkCover({
  asset,
  title,
  className = "",
  fit = "cover",
  onPress,
}: {
  asset?: MediaAsset | null;
  title: string;
  className?: string;
  fit?: "contain" | "cover";
  onPress?: () => void;
}) {
  const { t } = useTranslation();
  const enabled = useSensitiveMediaEnabled();
  if (!enabled) return null;
  const alt = t("sensitiveMedia.coverAlt", { title });
  if (asset && onPress) return <MediaThumbnailButton alt={alt} asset={asset} className={className} fit={fit} onPress={onPress} />;
  return (
    <SensitiveMediaImage
      alt={alt}
      asset={asset}
      className={`media-thumbnail-frame ${fit === "contain" ? "object-contain" : "object-cover"} ${className}`}
      showRetry
      variant="thumbnail"
    />
  );
}

export function MediaGallery({
  assets,
  title,
  onOpen,
}: {
  assets: MediaAsset[];
  title: string;
  onOpen: (index: number) => void;
}) {
  const { t } = useTranslation();
  const enabled = useSensitiveMediaEnabled();
  const signature = useMemo(() => assets.map((asset) => asset.thumbnail_url).join("\n"), [assets]);
  const [pagination, setPagination] = useState({ signature, count: 12 });
  if (!enabled || !assets.length) return null;

  const visibleCount = pagination.signature === signature ? pagination.count : 12;
  const visibleAssets = assets.slice(0, visibleCount);
  return (
    <section aria-label={`${t("sensitiveMedia.gallery")}: ${title}`} className="grid gap-3">
      <div className="flex items-center justify-between gap-3">
        <h3 className="flex items-center gap-2 text-sm font-semibold">
          <IconPhoto aria-hidden="true" className="text-accent" size={17} />
          {t("sensitiveMedia.gallery")}
        </h3>
        <Chip size="sm" variant="soft">{assets.length}</Chip>
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
        {visibleAssets.map((asset, index) => (
          <MediaThumbnailButton
            alt={t("sensitiveMedia.mediaAlt", { index: index + 1 })}
            asset={asset}
            className="aspect-[4/3] w-full rounded-lg border border-border bg-default"
            key={`${asset.kind}:${asset.thumbnail_url}`}
            onPress={() => onOpen(index)}
          />
        ))}
      </div>
      {visibleCount < assets.length ? (
        <Button
          className="justify-self-center"
          size="sm"
          variant="outline"
          onPress={() => setPagination({ signature, count: visibleCount + 12 })}
        >
          {t("sensitiveMedia.loadMore")}
        </Button>
      ) : null}
    </section>
  );
}

export function MediaViewer({
  assets,
  index,
  open,
  title,
  onClose,
  onIndexChange,
}: {
  assets: MediaAsset[];
  index: number;
  open: boolean;
  title: string;
  onClose: () => void;
  onIndexChange: (index: number) => void;
}) {
  const { t } = useTranslation();
  const enabled = useSensitiveMediaEnabled();
  const current = assets[index];
  const previous = () => onIndexChange((index - 1 + assets.length) % assets.length);
  const next = () => onIndexChange((index + 1) % assets.length);

  useEffect(() => {
    if (!open) return;
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "ArrowLeft" && assets.length > 1) {
        event.preventDefault();
        previous();
      } else if (event.key === "ArrowRight" && assets.length > 1) {
        event.preventDefault();
        next();
      } else if (event.key === "Escape") {
        onClose();
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  });

  useEffect(() => {
    if (!enabled && open) onClose();
  }, [enabled, onClose, open]);

  if (!current) return null;
  return (
    <ConfirmModal
      actions={(
        <div className="flex w-full items-center justify-between gap-3">
          <Button isDisabled={assets.length < 2} variant="outline" onPress={previous}>
            <IconChevronLeft aria-hidden="true" size={17} />
            <span className="hidden sm:inline">{t("sensitiveMedia.previous")}</span>
          </Button>
          <span className="text-sm tabular-nums text-muted">{t("sensitiveMedia.imagePosition", { current: index + 1, total: assets.length })}</span>
          <Button isDisabled={assets.length < 2} variant="outline" onPress={next}>
            <span className="hidden sm:inline">{t("sensitiveMedia.next")}</span>
            <IconChevronRight aria-hidden="true" size={17} />
          </Button>
        </div>
      )}
      open={open && enabled}
      size="lg"
      title={title || t("sensitiveMedia.viewer")}
      onOpenChange={(isOpen) => !isOpen && onClose()}
    >
      <div className="grid min-h-72 place-items-center overflow-hidden rounded-lg bg-black/90 p-2 sm:min-h-[30rem]">
        <SensitiveMediaImage
          alt={t("sensitiveMedia.mediaAlt", { index: index + 1 })}
          asset={current}
          className="max-h-[70vh] max-w-full object-contain"
          showRetry
          variant="original"
        />
      </div>
    </ConfirmModal>
  );
}
