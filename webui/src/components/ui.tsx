import {
  Autocomplete,
  Button,
  Chip,
  Description,
  EmptyState,
  FieldError,
  Input,
  InputGroup,
  Label,
  ListBox,
  Modal,
  NumberField,
  SearchField,
  Select,
  Skeleton,
  Switch,
  TextArea,
  TextField,
  Tooltip,
  useOverlayState,
} from "@heroui/react";
import { Check, ChevronDown, Eye, EyeOff, Inbox, Minus, Plus, Search, X, type LucideIcon } from "lucide-react";
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
  description,
  value,
  onChange,
  placeholder,
  isRequired = false,
  isDisabled,
}: {
  label: string;
  description?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  isRequired?: boolean;
  isDisabled?: boolean;
}) {
  const [visible, setVisible] = useState(false);
  const visibilityLabel = visible ? "Hide password" : "Show password";
  return (
    <TextField.Root
      className="grid gap-1.5"
      fullWidth
      isDisabled={isDisabled}
      isRequired={isRequired}
      type={visible ? "text" : "password"}
      value={value}
      variant="secondary"
      onChange={onChange}
    >
      <Label className="text-sm font-medium text-foreground">{label}</Label>
      <InputGroup>
        <InputGroup.Input autoComplete="off" placeholder={placeholder} />
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
      {description ? <Description className="text-xs leading-relaxed text-muted">{description}</Description> : null}
    </TextField.Root>
  );
}

export function NumberInput({
  label,
  description,
  value,
  onChange,
  minValue,
  maxValue,
  step,
  isDisabled,
}: {
  label: string;
  description?: string;
  value?: number;
  onChange: (value: number) => void;
  minValue?: number;
  maxValue?: number;
  step?: number;
  isDisabled?: boolean;
}) {
  return (
    <NumberField
      className="grid gap-1.5"
      fullWidth
      isDisabled={isDisabled}
      maxValue={maxValue}
      minValue={minValue}
      step={step}
      value={value}
      variant="secondary"
      onChange={onChange}
    >
      <Label className="text-sm font-medium text-foreground">{label}</Label>
      <NumberField.Group>
        <NumberField.DecrementButton aria-label={`Decrease ${label}`}>
          <Minus aria-hidden="true" size={15} />
        </NumberField.DecrementButton>
        <NumberField.Input />
        <NumberField.IncrementButton aria-label={`Increase ${label}`}>
          <Plus aria-hidden="true" size={15} />
        </NumberField.IncrementButton>
      </NumberField.Group>
      {description ? <Description className="text-xs leading-relaxed text-muted">{description}</Description> : null}
    </NumberField>
  );
}

export function CodeEditor({
  label,
  value,
  onChange,
  description,
  rows = 18,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  description?: string;
  rows?: number;
}) {
  return (
    <TextField.Root className="grid gap-1.5" fullWidth value={value} onChange={onChange}>
      <Label className="text-sm font-medium text-foreground">{label}</Label>
      <TextArea
        className="w-full resize-y font-mono text-xs leading-6"
        rows={rows}
        spellCheck={false}
        variant="secondary"
      />
      {description ? <Description className="text-xs leading-relaxed text-muted">{description}</Description> : null}
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

export function Toggle({
  label,
  description,
  isSelected,
  onChange,
  isDisabled,
}: {
  label: string;
  description?: string;
  isSelected: boolean;
  onChange: (selected: boolean) => void;
  isDisabled?: boolean;
}) {
  return (
    <Switch.Root
      className="flex min-h-11 items-center justify-between gap-4"
      isDisabled={isDisabled}
      isSelected={isSelected}
      onChange={onChange}
    >
      <Switch.Content className="min-w-0">
        <span className="block text-sm font-medium text-foreground">{label}</span>
        {description ? <span className="mt-0.5 block text-xs leading-relaxed text-muted">{description}</span> : null}
      </Switch.Content>
      <Switch.Control className="shrink-0">
        <Switch.Thumb>
          <Switch.Icon>
            <Check aria-hidden="true" size={11} />
          </Switch.Icon>
        </Switch.Thumb>
      </Switch.Control>
    </Switch.Root>
  );
}

export type SelectOption = { value: string; label: string };

export function SelectField({
  label,
  value,
  options,
  onChange,
  description,
  isDisabled,
}: {
  label: string;
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
  description?: string;
  isDisabled?: boolean;
}) {
  const selected = options.find((option) => option.value === value);
  return (
    <Select
      aria-label={label}
      className="select"
      fullWidth
      isDisabled={isDisabled}
      selectedKey={value || null}
      variant="secondary"
      onSelectionChange={(key) => onChange(key == null ? "" : String(key))}
    >
      <Label className="text-sm font-medium text-foreground">{label}</Label>
      <Select.Trigger>
        <Select.Value>{selected?.label ?? label}</Select.Value>
        <Select.Indicator>
          <ChevronDown aria-hidden="true" size={16} />
        </Select.Indicator>
      </Select.Trigger>
      {description ? <Description className="text-xs text-muted">{description}</Description> : null}
      <Select.Popover>
        <ListBox aria-label={label}>
          {options.map((option) => (
            <ListBox.Item id={option.value} key={option.value} textValue={option.label}>
              {option.label}
              <ListBox.ItemIndicator />
            </ListBox.Item>
          ))}
        </ListBox>
      </Select.Popover>
    </Select>
  );
}

export function AutocompleteField({
  label,
  value,
  options,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
  placeholder: string;
}) {
  const selected = options.find((option) => option.value === value);
  return (
    <Autocomplete
      aria-label={label}
      fullWidth
      selectedKey={value || null}
      variant="secondary"
      onSelectionChange={(key) => onChange(key == null ? "" : String(key))}
    >
      <Label className="text-sm font-medium text-foreground">{label}</Label>
      <Autocomplete.Trigger>
        <Autocomplete.Value>{selected?.label ?? placeholder}</Autocomplete.Value>
        <Autocomplete.ClearButton aria-label="Clear selection">
          <X aria-hidden="true" size={15} />
        </Autocomplete.ClearButton>
        <Autocomplete.Indicator>
          <ChevronDown aria-hidden="true" size={16} />
        </Autocomplete.Indicator>
      </Autocomplete.Trigger>
      <Autocomplete.Popover>
        <Autocomplete.Filter
          filter={(textValue, inputValue) => textValue.toLocaleLowerCase().includes(inputValue.toLocaleLowerCase())}
        >
          <SearchField aria-label={`${label} search`} autoFocus variant="secondary">
            <SearchField.Group>
              <SearchField.SearchIcon>
                <Search aria-hidden="true" size={15} />
              </SearchField.SearchIcon>
              <SearchField.Input placeholder={placeholder} />
              <SearchField.ClearButton />
            </SearchField.Group>
          </SearchField>
          <ListBox aria-label={label}>
            {options.map((option) => (
              <ListBox.Item id={option.value} key={option.value} textValue={option.label}>
                {option.label}
                <ListBox.ItemIndicator />
              </ListBox.Item>
            ))}
          </ListBox>
        </Autocomplete.Filter>
      </Autocomplete.Popover>
    </Autocomplete>
  );
}

export function AppModal({
  open,
  title,
  children,
  footer,
  onOpenChange,
  size = "lg",
}: {
  open: boolean;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  onOpenChange: (open: boolean) => void;
  size?: React.ComponentProps<typeof Modal.Container>["size"];
}) {
  const state = useOverlayState({ isOpen: open, onOpenChange });
  return (
    <Modal state={state}>
      <Modal.Backdrop>
        <Modal.Container className="mx-3" placement="center" scroll="inside" size={size}>
          <Modal.Dialog>
            <Modal.Header className="flex items-center justify-between gap-3 border-b border-border px-5 py-4">
              <Modal.Heading className="text-lg font-semibold text-foreground">{title}</Modal.Heading>
              <Modal.CloseTrigger
                aria-label="Close"
                className="grid size-10 place-items-center rounded-lg text-muted hover:bg-default"
              >
                <X aria-hidden="true" size={18} />
              </Modal.CloseTrigger>
            </Modal.Header>
            <Modal.Body className="p-5">{children}</Modal.Body>
            {footer ? <Modal.Footer className="flex flex-wrap justify-end gap-2 border-t border-border px-5 py-4">{footer}</Modal.Footer> : null}
          </Modal.Dialog>
        </Modal.Container>
      </Modal.Backdrop>
    </Modal>
  );
}
