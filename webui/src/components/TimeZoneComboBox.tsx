import { IconWorld } from "@tabler/icons-react";
import type { ReactNode } from "react";

import { timeZoneOptions } from "../lib/timezones";
import { ComboBoxField } from "./ui";

export function TimeZoneComboBox({
  label,
  value,
  onChange,
  description,
  isDisabled = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  description?: ReactNode;
  isDisabled?: boolean;
}) {
  return (
    <ComboBoxField
      description={description}
      icon={IconWorld}
      inputClassName="font-mono text-[0.8125rem]"
      isDisabled={isDisabled}
      label={label}
      options={timeZoneOptions(value)}
      value={value}
      onChange={onChange}
    />
  );
}
