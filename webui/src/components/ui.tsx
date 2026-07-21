import {
  Button,
  Chip,
  Description,
  EmptyState,
  FieldError,
  Input,
  InputGroup,
  Label,
  Skeleton,
  TextField,
  Tooltip,
} from "@heroui/react";
import { Eye, EyeOff, Inbox, type LucideIcon } from "lucide-react";
import { useState, type ReactNode } from "react";

import type { TaskStatus } from "../types";

export function IconButton({
  label,
  icon: Icon,
  onPress,
  variant = "ghost",
  isDisabled,
}: {
  label: string;
  icon: LucideIcon;
  onPress: () => void;
  variant?: React.ComponentProps<typeof Button>["variant"];
  isDisabled?: boolean;
}) {
  return (
    <Tooltip>
      <Button
        isIconOnly
        aria-label={label}
        className="size-11 min-w-11 shrink-0"
        isDisabled={isDisabled}
        variant={variant}
        onPress={onPress}
      >
        <Icon aria-hidden="true" size={18} strokeWidth={1.8} />
      </Button>
      <Tooltip.Content>{label}</Tooltip.Content>
    </Tooltip>
  );
}

export function FormField({
  label,
  description,
  value,
  onChange,
  type = "text",
  autoComplete,
  isRequired,
  isInvalid,
  errorMessage,
  placeholder,
}: {
  label: string;
  description?: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  autoComplete?: string;
  isRequired?: boolean;
  isInvalid?: boolean;
  errorMessage?: string;
  placeholder?: string;
}) {
  return (
    <TextField.Root
      className="grid gap-1.5"
      fullWidth
      isInvalid={isInvalid}
      isRequired={isRequired}
      type={type}
      value={value}
      variant="secondary"
      onChange={onChange}
    >
      <Label className="text-sm font-medium text-foreground">{label}</Label>
      <Input autoComplete={autoComplete} placeholder={placeholder} />
      {description ? <Description className="text-xs leading-relaxed text-muted">{description}</Description> : null}
      {errorMessage ? <FieldError>{errorMessage}</FieldError> : null}
    </TextField.Root>
  );
}

export function PasswordField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  const [visible, setVisible] = useState(false);
  const visibilityLabel = visible ? "Hide password" : "Show password";
  return (
    <TextField.Root
      className="grid gap-1.5"
      fullWidth
      isRequired
      type={visible ? "text" : "password"}
      value={value}
      variant="secondary"
      onChange={onChange}
    >
      <Label className="text-sm font-medium text-foreground">{label}</Label>
      <InputGroup>
        <InputGroup.Input autoComplete="current-password" />
        <InputGroup.Suffix className="p-1">
          <Tooltip>
            <Button
              isIconOnly
              aria-label={visibilityLabel}
              aria-pressed={visible}
              size="sm"
              type="button"
              variant="ghost"
              onPress={() => setVisible((current) => !current)}
            >
              {visible ? <EyeOff aria-hidden="true" size={17} /> : <Eye aria-hidden="true" size={17} />}
            </Button>
            <Tooltip.Content>{visibilityLabel}</Tooltip.Content>
          </Tooltip>
        </InputGroup.Suffix>
      </InputGroup>
    </TextField.Root>
  );
}

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description: string;
  actions?: ReactNode;
}) {
  return (
    <header className="flex flex-col justify-between gap-4 border-b border-border pb-5 sm:flex-row sm:items-end">
      <div className="min-w-0">
        <h1 className="text-2xl font-semibold text-foreground">{title}</h1>
        <p className="mt-1 max-w-3xl text-sm leading-relaxed text-muted">{description}</p>
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  );
}

export function PageLoading() {
  return (
    <div aria-label="Loading" className="grid gap-4" role="status">
      <Skeleton className="h-20 rounded-lg" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }, (_, index) => (
          <Skeleton className="h-28 rounded-lg" key={index} />
        ))}
      </div>
      <Skeleton className="h-72 rounded-lg" />
    </div>
  );
}

export function EmptyPanel({ title, description }: { title: string; description?: string }) {
  return (
    <EmptyState className="min-h-52 rounded-lg border border-dashed border-border bg-surface p-8 text-center">
      <Inbox aria-hidden="true" className="mx-auto text-muted" size={26} />
      <p className="mt-3 font-medium text-foreground">{title}</p>
      {description ? <p className="mt-1 text-sm text-muted">{description}</p> : null}
    </EmptyState>
  );
}

const taskTone: Record<TaskStatus, React.ComponentProps<typeof Chip>["color"]> = {
  queued: "default",
  blocked: "warning",
  running: "accent",
  pause_requested: "warning",
  paused: "warning",
  stop_requested: "danger",
  stopped: "default",
  completed: "success",
  failed: "danger",
  interrupted: "danger",
};

export function TaskStatusChip({ status }: { status: TaskStatus }) {
  return (
    <Chip color={taskTone[status]} size="sm" variant="soft">
      {status.replaceAll("_", " ")}
    </Chip>
  );
}
