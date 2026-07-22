import {
  Autocomplete,
  Button,
  Checkbox,
  Chip,
  Description,
  DateField,
  DateRangePicker,
  EmptyState,
  FieldError,
  Input,
  InputGroup,
  Label,
  ListBox,
  Modal,
  NumberField,
  ProgressBar,
  RangeCalendar,
  SearchField,
  Select,
  Skeleton,
  Surface,
  Switch,
  Table,
  TextArea,
  TextField,
  Tooltip,
  cn,
  useOverlayState,
} from "@heroui/react";
import type { DateValue } from "@internationalized/date";
import { DateRangePickerStateContext } from "react-aria-components";
import {
  IconCheck as Check,
  IconChevronDown as ChevronDown,
  IconEye as Eye,
  IconEyeOff as EyeOff,
  IconInbox as Inbox,
  IconCalendarOff as CalendarOff,
  IconMinus as Minus,
  IconPlus as Plus,
  IconSearch as Search,
  IconX as X,
  type TablerIcon,
} from "@tabler/icons-react";
import {
  useContext,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type ClipboardEvent,
  type KeyboardEvent,
  type ReactNode,
} from "react";
import { useTranslation } from "react-i18next";

import type { TaskStatus } from "../types";

function FieldLabel({ label, icon: Icon }: { label: ReactNode; icon?: TablerIcon }) {
  return (
    <Label className="field-label flex min-w-0 flex-1 items-center gap-1.5 text-sm font-semibold text-[var(--text-secondary)]">
      {Icon ? <Icon aria-hidden="true" className="field-label-icon shrink-0" size={15} stroke={1.8} /> : null}
      <span className="min-w-0 break-words leading-snug">{label}</span>
    </Label>
  );
}

export function FormSurface({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <Surface className={cn("form-surface control-surface rounded-lg border border-border p-4", className)} variant="secondary">
      {children}
    </Surface>
  );
}

export function DataTableFrame({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <Table className={className} variant="secondary">
      <Table.ScrollContainer className="app-table-frame">{children}</Table.ScrollContainer>
    </Table>
  );
}

export function IconButton({
  label,
  icon: Icon,
  onPress,
  variant = "ghost",
  isDisabled,
  className,
  tooltip,
}: {
  label: string;
  icon: TablerIcon;
  onPress: () => void;
  variant?: React.ComponentProps<typeof Button>["variant"];
  isDisabled?: boolean;
  className?: string;
  tooltip?: string;
}) {
  return (
    <Tooltip>
      <Button
        isIconOnly
        aria-disabled={isDisabled || undefined}
        aria-label={label}
        className={cn("size-11 min-w-11 shrink-0 aria-disabled:cursor-not-allowed aria-disabled:opacity-50", className)}
        isDisabled={isDisabled}
        variant={variant}
        onPress={onPress}
      >
        <Icon aria-hidden="true" size={18} stroke={1.8} />
      </Button>
      <Tooltip.Content>{tooltip ?? label}</Tooltip.Content>
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
  icon,
  isReadOnly = false,
  isDisabled = false,
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
  icon?: TablerIcon;
  isReadOnly?: boolean;
  isDisabled?: boolean;
}) {
  return (
    <TextField.Root
      className="grid gap-1.5"
      fullWidth
      isDisabled={isDisabled}
      isInvalid={isInvalid}
      isReadOnly={isReadOnly}
      isRequired={isRequired}
      type={type}
      value={value}
      variant="secondary"
      onChange={onChange}
    >
      <FieldLabel icon={icon} label={label} />
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
  icon,
}: {
  label: string;
  description?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  isRequired?: boolean;
  isDisabled?: boolean;
  icon?: TablerIcon;
}) {
  const { t } = useTranslation();
  const [visible, setVisible] = useState(false);
  const visibilityLabel = visible ? t("common.hidePassword") : t("common.showPassword");
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
      <FieldLabel icon={icon} label={label} />
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
  icon,
}: {
  label: string;
  description?: string;
  value?: number;
  onChange: (value: number) => void;
  minValue?: number;
  maxValue?: number;
  step?: number;
  isDisabled?: boolean;
  icon?: TablerIcon;
}) {
  const { t } = useTranslation();
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
      <FieldLabel icon={icon} label={label} />
      <NumberField.Group>
        <NumberField.DecrementButton aria-label={`${t("common.decrease")} ${label}`}>
          <Minus aria-hidden="true" size={15} />
        </NumberField.DecrementButton>
        <NumberField.Input />
        <NumberField.IncrementButton aria-label={`${t("common.increase")} ${label}`}>
          <Plus aria-hidden="true" size={15} />
        </NumberField.IncrementButton>
      </NumberField.Group>
      {description ? <Description className="text-xs leading-relaxed text-muted">{description}</Description> : null}
    </NumberField>
  );
}

export type DateRangeValue = { start: DateValue; end: DateValue };

export function DateRangeInput({
  label,
  description,
  value,
  onChange,
  icon,
}: {
  label: string;
  description?: string;
  value: DateRangeValue | null;
  onChange: (value: DateRangeValue | null) => void;
  icon?: TablerIcon;
}) {
  return (
    <DateRangePicker className="grid gap-1.5" value={value} onChange={onChange}>
      <FieldLabel icon={icon} label={label} />
      <DateField.Group fullWidth variant="secondary">
        <DateField.InputContainer>
          <DateField.Input slot="start">
            {(segment) => <DateField.Segment segment={segment} />}
          </DateField.Input>
          <DateRangePicker.RangeSeparator />
          <DateField.Input slot="end">
            {(segment) => <DateField.Segment segment={segment} />}
          </DateField.Input>
        </DateField.InputContainer>
        <DateField.Suffix>
          <DateRangePicker.Trigger aria-label={label}>
            <DateRangePicker.TriggerIndicator />
          </DateRangePicker.Trigger>
        </DateField.Suffix>
      </DateField.Group>
      {description ? <Description className="text-xs leading-relaxed text-muted">{description}</Description> : null}
      <DateRangePicker.Popover>
        <RangeCalendar aria-label={label}>
          <RangeCalendar.Header>
            <RangeCalendar.NavButton slot="previous" />
            <RangeCalendar.Heading />
            <RangeCalendar.NavButton slot="next" />
          </RangeCalendar.Header>
          <RangeCalendar.Grid>
            <RangeCalendar.GridHeader>
              {(day) => <RangeCalendar.HeaderCell>{day}</RangeCalendar.HeaderCell>}
            </RangeCalendar.GridHeader>
            <RangeCalendar.GridBody>
              {(date) => <RangeCalendar.Cell date={date} />}
            </RangeCalendar.GridBody>
          </RangeCalendar.Grid>
        </RangeCalendar>
      </DateRangePicker.Popover>
    </DateRangePicker>
  );
}

export function ChipListField({
  label,
  description,
  values,
  onChange,
  placeholder,
  icon,
  commitOnComma = true,
}: {
  label: string;
  description?: string;
  values: string[];
  onChange: (values: string[]) => void;
  placeholder?: string;
  icon?: TablerIcon;
  commitOnComma?: boolean;
}) {
  const { t } = useTranslation();
  const [draft, setDraft] = useState("");

  function appendValues(candidates: string[]) {
    const next = [...values];
    for (const candidate of candidates) {
      const normalized = candidate.trim();
      if (normalized && !next.includes(normalized)) next.push(normalized);
    }
    if (next.length !== values.length) onChange(next);
  }

  function commitDraft() {
    appendValues([draft]);
    setDraft("");
  }

  function updateDraft(next: string) {
    if (!commitOnComma || !/[,，]/u.test(next)) {
      setDraft(next);
      return;
    }
    const parts = next.split(/[,，]/u);
    const trailing = parts.pop() ?? "";
    appendValues(parts);
    setDraft(trailing);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.nativeEvent.isComposing) return;
    const isDelimiter = commitOnComma && (event.key === "," || event.key === "，");
    if (event.key === "Enter" || isDelimiter) {
      event.preventDefault();
      commitDraft();
      return;
    }
    if (event.key === "Backspace" && !draft && values.length) {
      event.preventDefault();
      onChange(values.slice(0, -1));
    }
  }

  function handlePaste(event: ClipboardEvent<HTMLInputElement>) {
    if (!commitOnComma) return;
    const text = event.clipboardData.getData("text");
    if (!/[,，\r\n]/u.test(text)) return;
    event.preventDefault();
    appendValues(text.split(/[,，\r\n]+/u));
    setDraft("");
  }

  return (
    <TextField.Root className="grid gap-1.5" fullWidth value={draft} onChange={updateDraft}>
      <FieldLabel icon={icon} label={label} />
      <InputGroup className="chip-list-control" fullWidth variant="secondary">
        {values.map((value) => (
          <Chip className="chip-list-item" color="accent" key={value} size="sm" variant="soft">
            <Chip.Label>{value}</Chip.Label>
            <Button
              isIconOnly
              aria-label={t("common.removeValue", { value })}
              className="chip-list-remove"
              size="sm"
              type="button"
              variant="ghost"
              onPress={() => onChange(values.filter((item) => item !== value))}
            >
              <X aria-hidden="true" size={13} />
            </Button>
          </Chip>
        ))}
        <InputGroup.Input
          className="chip-list-input"
          placeholder={values.length ? undefined : placeholder}
          onBlur={commitDraft}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
        />
      </InputGroup>
      {description ? <Description className="text-xs leading-relaxed text-muted">{description}</Description> : null}
    </TextField.Root>
  );
}

export function OptionalDateRangeField({
  label,
  description,
  startLabel,
  endLabel,
  startUnlimitedLabel,
  endUnlimitedLabel,
  startValue,
  endValue,
  startUnlimited,
  endUnlimited,
  onStartChange,
  onEndChange,
  onStartUnlimitedChange,
  onEndUnlimitedChange,
  errorMessage,
  icon,
}: {
  label: string;
  description?: string;
  startLabel: string;
  endLabel: string;
  startUnlimitedLabel: string;
  endUnlimitedLabel: string;
  startValue: DateValue | null;
  endValue: DateValue | null;
  startUnlimited: boolean;
  endUnlimited: boolean;
  onStartChange: (value: DateValue | null) => void;
  onEndChange: (value: DateValue | null) => void;
  onStartUnlimitedChange: (selected: boolean) => void;
  onEndUnlimitedChange: (selected: boolean) => void;
  errorMessage?: string;
  icon?: TablerIcon;
}) {
  const [calendarOpen, setCalendarOpen] = useState(false);

  function changeStart(value: DateValue | null) {
    onStartChange(value);
    if (value) onStartUnlimitedChange(false);
  }

  function changeEnd(value: DateValue | null) {
    onEndChange(value);
    if (value) onEndUnlimitedChange(false);
  }

  function toggleStart(selected: boolean) {
    onStartUnlimitedChange(selected);
    if (selected) onStartChange(null);
  }

  function toggleEnd(selected: boolean) {
    onEndUnlimitedChange(selected);
    if (selected) onEndChange(null);
  }

  function selectSingleBoundary(date: DateValue) {
    if (!startUnlimited && !endUnlimited) return;
    if (startUnlimited && !endUnlimited) changeEnd(date);
    else changeStart(date);
    window.requestAnimationFrame(() => setCalendarOpen(false));
  }

  return (
    <DateRangePicker
      className="grid gap-1.5"
      isInvalid={Boolean(errorMessage)}
      isOpen={calendarOpen}
      onOpenChange={setCalendarOpen}
    >
      <FieldLabel icon={icon} label={label} />
      <DateField.Group fullWidth variant="secondary">
        <DateField.InputContainer>
          <DateField.Input aria-label={startLabel} slot="start">
            {(segment) => <DateField.Segment segment={segment} />}
          </DateField.Input>
          <DateRangePicker.RangeSeparator />
          <DateField.Input aria-label={endLabel} slot="end">
            {(segment) => <DateField.Segment segment={segment} />}
          </DateField.Input>
        </DateField.InputContainer>
        <DateField.Suffix>
          <DateRangePicker.Trigger aria-label={label}>
            <DateRangePicker.TriggerIndicator />
          </DateRangePicker.Trigger>
        </DateField.Suffix>
      </DateField.Group>
      <PartialDateRangeStateBridge
        endValue={endValue}
        startValue={startValue}
        onEndChange={changeEnd}
        onStartChange={changeStart}
      />
      <DateRangePicker.Popover>
        <RangeCalendar aria-label={label}>
          <RangeCalendar.Header>
            <RangeCalendar.NavButton slot="previous" />
            <RangeCalendar.Heading />
            <RangeCalendar.NavButton slot="next" />
          </RangeCalendar.Header>
          <RangeCalendar.Grid>
            <RangeCalendar.GridHeader>
              {(day) => <RangeCalendar.HeaderCell>{day}</RangeCalendar.HeaderCell>}
            </RangeCalendar.GridHeader>
            <RangeCalendar.GridBody>
              {(date) => <RangeCalendar.Cell date={date} onClick={() => selectSingleBoundary(date)} />}
            </RangeCalendar.GridBody>
          </RangeCalendar.Grid>
        </RangeCalendar>
      </DateRangePicker.Popover>
      {description ? <Description className="text-xs leading-relaxed text-muted">{description}</Description> : null}
      <div className="optional-date-range-options">
        <FormCheckbox
          icon={CalendarOff}
          isSelected={startUnlimited}
          label={startUnlimitedLabel}
          onChange={toggleStart}
        />
        <FormCheckbox
          icon={CalendarOff}
          isSelected={endUnlimited}
          label={endUnlimitedLabel}
          onChange={toggleEnd}
        />
      </div>
      {errorMessage ? (
        <div role="alert">
          <FieldError>{errorMessage}</FieldError>
        </div>
      ) : null}
    </DateRangePicker>
  );
}

function PartialDateRangeStateBridge({
  startValue,
  endValue,
  onStartChange,
  onEndChange,
}: {
  startValue: DateValue | null;
  endValue: DateValue | null;
  onStartChange: (value: DateValue | null) => void;
  onEndChange: (value: DateValue | null) => void;
}) {
  const state = useContext(DateRangePickerStateContext);
  const previousExternal = useRef<{ start: string | null; end: string | null } | null>(null);
  const synchronizing = useRef(false);
  const desiredStart = dateValueKey(startValue);
  const desiredEnd = dateValueKey(endValue);
  const stateRange = state?.dateRange ?? state?.value;
  const stateStartValue = stateRange?.start ?? null;
  const stateEndValue = stateRange?.end ?? null;
  const stateStart = dateValueKey(stateStartValue);
  const stateEnd = dateValueKey(stateEndValue);

  useLayoutEffect(() => {
    if (!state) return;
    const previous = previousExternal.current;
    if (previous?.start === desiredStart && previous.end === desiredEnd) return;
    previousExternal.current = { start: desiredStart, end: desiredEnd };
    let changed = false;
    if (stateStart !== desiredStart) {
      state.setDateTime("start", startValue);
      changed = true;
    }
    if (stateEnd !== desiredEnd) {
      state.setDateTime("end", endValue);
      changed = true;
    }
    synchronizing.current = changed;
  }, [desiredEnd, desiredStart, endValue, startValue, state, stateEnd, stateStart]);

  useEffect(() => {
    if (!state) return;
    if (synchronizing.current) {
      synchronizing.current = false;
      return;
    }
    const startChanged = stateStart !== desiredStart;
    const endChanged = stateEnd !== desiredEnd;
    if (!startChanged && !endChanged) return;

    if (startChanged) onStartChange(stateStartValue);
    if (endChanged) onEndChange(stateEndValue);
  }, [
    desiredEnd,
    desiredStart,
    onEndChange,
    onStartChange,
    state,
    stateEnd,
    stateEndValue,
    stateStart,
    stateStartValue,
  ]);

  return null;
}

function dateValueKey(value: DateValue | null): string | null {
  return value?.toString() ?? null;
}

export function PawchiveIdentityFields({
  label,
  description,
  serviceLabel,
  creatorIdLabel,
  postIdLabel,
  service,
  creatorId,
  postId,
  onServiceChange,
  onCreatorIdChange,
  onPostIdChange,
  isReadOnly = false,
  icon,
}: {
  label: string;
  description?: string;
  serviceLabel: string;
  creatorIdLabel: string;
  postIdLabel?: string;
  service: string;
  creatorId: string;
  postId?: string;
  onServiceChange: (value: string) => void;
  onCreatorIdChange: (value: string) => void;
  onPostIdChange?: (value: string) => void;
  isReadOnly?: boolean;
  icon?: TablerIcon;
}) {
  return (
    <div className="grid gap-1.5">
      <FieldLabel icon={icon} label={label} />
      <div
        aria-label={label}
        aria-readonly={isReadOnly || undefined}
        className="pawchive-identity-fields"
        data-readonly={isReadOnly || undefined}
        role="group"
      >
        <code aria-hidden="true" className="pawchive-identity-token">/</code>
        <div className="pawchive-identity-input pawchive-identity-platform">
          <FormField
            isReadOnly={isReadOnly}
            isRequired={!isReadOnly}
            label={serviceLabel}
            value={service}
            onChange={onServiceChange}
          />
        </div>
        <code aria-hidden="true" className="pawchive-identity-token">/user/</code>
        <div className="pawchive-identity-input">
          <FormField
            isReadOnly={isReadOnly}
            isRequired={!isReadOnly}
            label={creatorIdLabel}
            value={creatorId}
            onChange={onCreatorIdChange}
          />
        </div>
        {postIdLabel !== undefined && onPostIdChange ? (
          <>
            <code aria-hidden="true" className="pawchive-identity-token">/post/</code>
            <div className="pawchive-identity-input">
              <FormField
                isReadOnly={isReadOnly}
                isRequired={!isReadOnly}
                label={postIdLabel}
                value={postId ?? ""}
                onChange={onPostIdChange}
              />
            </div>
          </>
        ) : null}
      </div>
      {description ? <Description className="text-xs leading-relaxed text-muted">{description}</Description> : null}
    </div>
  );
}

export function ProgressMeter({
  label,
  value,
  isIndeterminate = false,
}: {
  label: string;
  value: number;
  isIndeterminate?: boolean;
}) {
  return (
    <ProgressBar
      aria-label={label}
      className="grid gap-2"
      color="accent"
      isIndeterminate={isIndeterminate}
      value={Math.min(100, Math.max(0, value))}
    >
      <div className="flex items-center justify-between gap-3 text-sm">
        <Label className="font-medium text-foreground">{label}</Label>
        {!isIndeterminate ? <ProgressBar.Output className="tabular-nums text-muted" /> : null}
      </div>
      <ProgressBar.Track>
        <ProgressBar.Fill />
      </ProgressBar.Track>
    </ProgressBar>
  );
}

export function CodeEditor({
  label,
  value,
  onChange,
  description,
  rows = 18,
  icon,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  description?: string;
  rows?: number;
  icon?: TablerIcon;
}) {
  return (
    <TextField.Root className="grid gap-1.5" fullWidth value={value} onChange={onChange}>
      <FieldLabel icon={icon} label={label} />
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
  showDescription = false,
}: {
  title: string;
  description: string;
  actions?: ReactNode;
  showDescription?: boolean;
}) {
  if (!actions && !showDescription) return null;
  return (
    <header aria-label={title} className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
      {showDescription ? (
        <div className="min-w-0">
          <h2 className="sr-only">{title}</h2>
          <p className="text-sm leading-relaxed text-muted">{description}</p>
        </div>
      ) : <span className="sr-only">{description}</span>}
      {actions ? <div className="ml-auto flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  );
}

export function PageLoading() {
  const { t } = useTranslation();
  return (
    <div aria-label={t("common.loading")} className="grid gap-4" role="status">
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
  const { t } = useTranslation();
  return (
    <Chip color={taskTone[status]} size="sm" variant="soft">
      {t(`tasks.statuses.${status}`)}
    </Chip>
  );
}

export function FormSwitchField({
  label,
  description,
  isSelected,
  onChange,
  isDisabled,
  icon,
  className,
}: {
  label: string;
  description?: string;
  isSelected: boolean;
  onChange: (selected: boolean) => void;
  isDisabled?: boolean;
  icon?: TablerIcon;
  className?: string;
}) {
  return (
    <Switch.Root
      className={cn(
        "form-switch min-h-11 rounded-lg border border-[var(--field-border)] bg-surface px-3 py-2 shadow-[var(--field-shadow)]",
        className,
      )}
      isDisabled={isDisabled}
      isSelected={isSelected}
      onChange={onChange}
    >
      <Switch.Content className="min-w-0 items-center gap-3">
        <Switch.Control className="shrink-0">
          <Switch.Thumb />
        </Switch.Control>
        <FieldLabel icon={icon} label={label} />
      </Switch.Content>
      {description ? <Description className="pl-[3.75rem] text-xs leading-relaxed text-muted">{description}</Description> : null}
    </Switch.Root>
  );
}

export function CompactSwitch({
  label,
  isSelected,
  onChange,
  isDisabled,
  className,
}: {
  label: string;
  isSelected: boolean;
  onChange: (selected: boolean) => void;
  isDisabled?: boolean;
  className?: string;
}) {
  return (
    <Tooltip>
      <Switch.Root
        aria-label={label}
        className={cn("compact-switch", className)}
        isDisabled={isDisabled}
        isSelected={isSelected}
        onChange={onChange}
      >
        <Switch.Content className="compact-switch-content">
          <Switch.Control>
            <Switch.Thumb />
          </Switch.Control>
        </Switch.Content>
      </Switch.Root>
      <Tooltip.Content>{label}</Tooltip.Content>
    </Tooltip>
  );
}

export function FormCheckbox({
  label,
  description,
  isSelected,
  onChange,
  isDisabled,
  isIndeterminate = false,
  className,
  icon,
}: {
  label: ReactNode;
  description?: string;
  isSelected: boolean;
  onChange: (selected: boolean) => void;
  isDisabled?: boolean;
  isIndeterminate?: boolean;
  className?: string;
  icon?: TablerIcon;
}) {
  return (
    <Checkbox
      className={cn("form-checkbox min-h-11 rounded-lg px-2 py-1", className)}
      isDisabled={isDisabled}
      isIndeterminate={isIndeterminate}
      isSelected={isSelected}
      variant="secondary"
      onChange={onChange}
    >
      <Checkbox.Content className="w-full min-w-0 items-center gap-3">
        <Checkbox.Control className="shrink-0">
          {isSelected || isIndeterminate ? (
            <Checkbox.Indicator>
              {isIndeterminate ? <Minus aria-hidden="true" size={12} /> : <Check aria-hidden="true" size={12} />}
            </Checkbox.Indicator>
          ) : null}
        </Checkbox.Control>
        <FieldLabel icon={icon} label={label} />
      </Checkbox.Content>
      {description ? <Description className="pl-[2.875rem] text-xs leading-relaxed text-muted">{description}</Description> : null}
    </Checkbox>
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
  icon,
}: {
  label: string;
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
  description?: string;
  isDisabled?: boolean;
  icon?: TablerIcon;
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
      <FieldLabel icon={icon} label={label} />
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
  icon,
}: {
  label: string;
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
  placeholder: string;
  icon?: TablerIcon;
}) {
  const { t } = useTranslation();
  const selected = options.find((option) => option.value === value);
  return (
    <Autocomplete
      aria-label={label}
      fullWidth
      selectedKey={value || null}
      variant="secondary"
      onSelectionChange={(key) => onChange(key == null ? "" : String(key))}
    >
      <FieldLabel icon={icon} label={label} />
      <Autocomplete.Trigger>
        <Autocomplete.Value>{selected?.label ?? placeholder}</Autocomplete.Value>
        <Autocomplete.ClearButton aria-label={t("common.clearSelection")}>
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
          <SearchField aria-label={t("common.searchWithin", { label })} autoFocus variant="secondary">
            <SearchField.Group>
              <SearchField.SearchIcon>
                <Search aria-hidden="true" size={15} />
              </SearchField.SearchIcon>
              <SearchField.Input placeholder={placeholder} />
              <SearchField.ClearButton aria-label={t("common.clearSearch")} />
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

export function FormModal({
  open,
  title,
  children,
  actions,
  onOpenChange,
  size = "lg",
  isWide = false,
}: {
  open: boolean;
  title: string;
  children: ReactNode;
  actions: ReactNode;
  onOpenChange: (open: boolean) => void;
  size?: React.ComponentProps<typeof Modal.Container>["size"];
  isWide?: boolean;
}) {
  const { t } = useTranslation();
  const state = useOverlayState({ isOpen: open, onOpenChange });
  return (
    <Modal state={state}>
      <Modal.Trigger aria-hidden="true" className="hidden" tabIndex={-1} />
      <Modal.Backdrop>
        <Modal.Container
          className={cn("mx-3", isWide && "app-form-modal-container-wide")}
          placement="center"
          scroll="inside"
          size={size}
        >
          <Modal.Dialog className="app-modal-dialog overflow-hidden">
            <Modal.Header className="flex items-center justify-between gap-3 border-b border-border px-5 py-4">
              <Modal.Heading className="text-lg font-semibold text-foreground">{title}</Modal.Heading>
              <Modal.CloseTrigger
                aria-label={t("common.close")}
                className="grid size-10 place-items-center rounded-lg text-muted hover:bg-default"
              >
                <X aria-hidden="true" size={18} />
              </Modal.CloseTrigger>
            </Modal.Header>
            <Surface
              className="app-form-modal-surface control-surface min-h-0 flex-1 overflow-hidden rounded-none border-0 shadow-none"
              variant="secondary"
            >
              <Modal.Body className="app-form-modal-body p-4 sm:p-5">{children}</Modal.Body>
              <Modal.Footer className="app-form-modal-actions flex flex-wrap justify-end gap-2 border-t border-border px-5 py-4">
                {actions}
              </Modal.Footer>
            </Surface>
          </Modal.Dialog>
        </Modal.Container>
      </Modal.Backdrop>
    </Modal>
  );
}

export function ConfirmModal({
  open,
  title,
  children,
  actions,
  onOpenChange,
  size = "md",
}: {
  open: boolean;
  title: string;
  children: ReactNode;
  actions: ReactNode;
  onOpenChange: (open: boolean) => void;
  size?: React.ComponentProps<typeof Modal.Container>["size"];
}) {
  const { t } = useTranslation();
  const state = useOverlayState({ isOpen: open, onOpenChange });
  return (
    <Modal state={state}>
      <Modal.Trigger aria-hidden="true" className="hidden" tabIndex={-1} />
      <Modal.Backdrop>
        <Modal.Container className="mx-3" placement="center" scroll="inside" size={size}>
          <Modal.Dialog className="app-modal-dialog overflow-hidden">
            <Modal.Header className="flex items-center justify-between gap-3 border-b border-border px-5 py-4">
              <Modal.Heading className="text-lg font-semibold text-foreground">{title}</Modal.Heading>
              <Modal.CloseTrigger
                aria-label={t("common.close")}
                className="grid size-10 place-items-center rounded-lg text-muted hover:bg-default"
              >
                <X aria-hidden="true" size={18} />
              </Modal.CloseTrigger>
            </Modal.Header>
            <Modal.Body className="app-confirm-modal-body p-5">{children}</Modal.Body>
            <Modal.Footer className="app-confirm-modal-actions flex flex-wrap justify-end gap-2 border-t border-border px-5 py-4">
              {actions}
            </Modal.Footer>
          </Modal.Dialog>
        </Modal.Container>
      </Modal.Backdrop>
    </Modal>
  );
}
