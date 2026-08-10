import { Button, Chip, Popover, Surface, Tooltip } from "@heroui/react";
import { IconEye, IconEyeOff } from "@tabler/icons-react";
import { useTranslation } from "react-i18next";

import { useSensitiveMedia } from "../lib/sensitiveMedia";
import { CompactSwitch } from "./ui";

function StatusIcon({ enabled, size = 18 }: { enabled: boolean; size?: number }) {
  const Icon = enabled ? IconEye : IconEyeOff;
  return <Icon aria-hidden="true" size={size} stroke={1.8} />;
}

function SwitchRow({ showDescription = false }: { showDescription?: boolean }) {
  const { t } = useTranslation();
  const media = useSensitiveMedia();
  return (
    <div className="flex min-h-11 min-w-0 items-center gap-3">
      <span
        aria-hidden="true"
        className={`sensitive-media-status-icon grid size-9 shrink-0 place-items-center rounded-lg ${media.enabled ? "is-enabled" : ""}`}
      >
        <StatusIcon enabled={media.enabled} />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
          <p className="whitespace-nowrap text-sm font-semibold text-foreground">{t("sensitiveMedia.label")}</p>
          {media.enabled ? <Chip color="warning" size="sm" variant="soft">18+</Chip> : null}
        </div>
        {showDescription ? <p className="mt-0.5 text-xs leading-relaxed text-muted">{t("sensitiveMedia.description")}</p> : null}
      </div>
      <CompactSwitch
        className={media.enabled ? "sensitive-media-switch is-enabled" : "sensitive-media-switch"}
        isSelected={media.enabled}
        label={media.enabled ? t("sensitiveMedia.enabled") : t("sensitiveMedia.disabled")}
        onChange={media.requestChange}
      />
    </div>
  );
}

export function SensitiveMediaInlineControl() {
  const { t } = useTranslation();
  return (
    <Surface aria-label={t("sensitiveMedia.label")} className="sensitive-media-inline rounded-lg px-2" role="group">
      <SwitchRow />
    </Surface>
  );
}

export function SensitiveMediaDrawerControl() {
  return <SwitchRow showDescription />;
}

export function SensitiveMediaPopoverControl() {
  const { t } = useTranslation();
  const media = useSensitiveMedia();
  const status = media.enabled ? t("sensitiveMedia.enabled") : t("sensitiveMedia.disabled");
  return (
    <Popover>
      <Tooltip>
        <Button
          isIconOnly
          aria-label={`${t("sensitiveMedia.change")}. ${status}`}
          aria-pressed={media.enabled}
          className={`size-11 min-w-11 shrink-0 ${media.enabled ? "sensitive-media-trigger-enabled" : ""}`}
          variant="outline"
        >
          <StatusIcon enabled={media.enabled} />
        </Button>
        <Tooltip.Content>{status}</Tooltip.Content>
      </Tooltip>
      <Popover.Content
        className="w-80 max-w-[calc(100vw-1.5rem)] rounded-lg border border-border"
        offset={10}
        placement="bottom end"
      >
        <Popover.Arrow />
        <Popover.Dialog className="p-3">
          <SwitchRow showDescription />
        </Popover.Dialog>
      </Popover.Content>
    </Popover>
  );
}
