import { Alert, Button } from "@heroui/react";
import {
  IconDatabaseExclamation,
  IconRefresh,
  IconWriting,
} from "@tabler/icons-react";
import { useTranslation } from "react-i18next";

export function ExternalChangeAlert({
  visible,
  onKeepEditing,
  onReload,
}: {
  visible: boolean;
  onKeepEditing: () => void;
  onReload: () => void;
}) {
  const { t } = useTranslation();
  if (!visible) return null;

  return (
    <Alert status="warning">
      <Alert.Indicator>
        <IconDatabaseExclamation aria-hidden="true" size={19} />
      </Alert.Indicator>
      <Alert.Content>
        <Alert.Title>{t("realtime.externalChangeTitle")}</Alert.Title>
        <Alert.Description>{t("realtime.externalChangeDescription")}</Alert.Description>
        <div className="mt-3 flex flex-wrap gap-2">
          <Button size="sm" variant="outline" onPress={onReload}>
            <IconRefresh aria-hidden="true" size={16} />
            {t("realtime.reload")}
          </Button>
          <Button size="sm" variant="ghost" onPress={onKeepEditing}>
            <IconWriting aria-hidden="true" size={16} />
            {t("realtime.keepEditing")}
          </Button>
        </div>
      </Alert.Content>
    </Alert>
  );
}
