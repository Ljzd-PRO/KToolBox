import { Alert, Button } from "@heroui/react";
import { IconAlertTriangle, IconEye, IconX } from "@tabler/icons-react";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useTranslation } from "react-i18next";

import { ConfirmModal } from "../components/ui";

export const SENSITIVE_MEDIA_STORAGE_KEY = "ktoolbox-nsfw-mode";

type SensitiveMediaContextValue = {
  enabled: boolean;
  requestChange: (enabled: boolean) => void;
  disable: () => void;
};

const SensitiveMediaContext = createContext<SensitiveMediaContextValue | null>(null);

function storedPreference(): boolean {
  return localStorage.getItem(SENSITIVE_MEDIA_STORAGE_KEY) === "true";
}

export function SensitiveMediaProvider({ children }: { children: ReactNode }) {
  const { t } = useTranslation();
  const [enabled, setEnabled] = useState(storedPreference);
  const [confirming, setConfirming] = useState(false);

  const persist = useCallback((next: boolean) => {
    localStorage.setItem(SENSITIVE_MEDIA_STORAGE_KEY, String(next));
    setEnabled(next);
  }, []);

  const requestChange = useCallback((next: boolean) => {
    if (next) setConfirming(true);
    else persist(false);
  }, [persist]);

  const disable = useCallback(() => persist(false), [persist]);

  useEffect(() => {
    document.documentElement.dataset.nsfw = enabled ? "enabled" : "disabled";
  }, [enabled]);

  useEffect(() => {
    function synchronize(event: StorageEvent) {
      if (event.key !== SENSITIVE_MEDIA_STORAGE_KEY) return;
      const next = event.newValue === "true";
      setEnabled(next);
      if (next) setConfirming(false);
    }
    window.addEventListener("storage", synchronize);
    return () => window.removeEventListener("storage", synchronize);
  }, []);

  const value = useMemo(() => ({ enabled, requestChange, disable }), [disable, enabled, requestChange]);

  return (
    <SensitiveMediaContext.Provider value={value}>
      {children}
      <ConfirmModal
        actions={
          <>
            <Button variant="ghost" onPress={() => setConfirming(false)}>
              <IconX aria-hidden="true" size={17} />
              {t("common.cancel")}
            </Button>
            <Button
              className="sensitive-media-confirm-action"
              variant="primary"
              onPress={() => {
                persist(true);
                setConfirming(false);
              }}
            >
              <IconEye aria-hidden="true" size={17} />
              {t("sensitiveMedia.confirmAction")}
            </Button>
          </>
        }
        open={confirming}
        title={t("sensitiveMedia.confirmTitle")}
        onOpenChange={setConfirming}
      >
        <div className="grid gap-4">
          <Alert status="warning">
            <Alert.Indicator><IconAlertTriangle aria-hidden="true" size={18} /></Alert.Indicator>
            <Alert.Content>
              <Alert.Title>{t("sensitiveMedia.label")}</Alert.Title>
              <Alert.Description>{t("sensitiveMedia.confirmBody")}</Alert.Description>
            </Alert.Content>
          </Alert>
          <div className="grid gap-2 text-sm leading-relaxed text-muted">
            <p>{t("sensitiveMedia.confirmPersistence")}</p>
            <p>{t("sensitiveMedia.confirmNetwork")}</p>
          </div>
        </div>
      </ConfirmModal>
    </SensitiveMediaContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useSensitiveMedia(): SensitiveMediaContextValue {
  const context = useContext(SensitiveMediaContext);
  if (!context) throw new Error("useSensitiveMedia must be used inside SensitiveMediaProvider");
  return context;
}
