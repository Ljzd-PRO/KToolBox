import { Button, Chip, Surface, toast } from "@heroui/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  IconArrowDown as ArrowDown,
  IconArrowUp as ArrowUp,
  IconBan as Ban,
  IconBraces as Braces,
  IconCheck as Check,
  IconEqual as Equal,
  IconFingerprint as Fingerprint,
  IconGitBranch as GitBranchPlus,
  IconLetterCase as CaseSensitive,
  IconListTree as ListTree,
  IconPencil as Pencil,
  IconPlus as Plus,
  IconPower as Power,
  IconTrash as Trash2,
  IconUsersGroup as UsersRound,
  IconX as X,
} from "@tabler/icons-react";
import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";

import {
  AutocompleteField,
  ChipListField,
  CompactSwitch,
  ConfirmModal,
  EmptyPanel,
  FormCheckbox,
  FormField,
  FormModal,
  FormSwitchField,
  IconButton,
  PageHeader,
  PageLoading,
  SelectField,
} from "../components/ui";
import { api, errorText } from "../lib/api";
import { useAuth } from "../lib/auth";
import type {
  BlockerSpec,
  ConditionGroup,
  CreatorReference,
  FieldCondition,
} from "../types";

const blankCondition = (): FieldCondition => ({
  kind: "field",
  field: "title",
  operator: "contains",
  values: [],
  expected: true,
  case_sensitive: false,
  negate: false,
});

const blankGroup = (): ConditionGroup => ({
  kind: "group",
  mode: "any",
  conditions: [blankCondition()],
  negate: false,
});

const blankBlocker = (): BlockerSpec => ({
  id: "",
  type: "field-match",
  enabled: true,
  scope: { mode: "global", creators: [] },
  options: { rule: blankGroup() },
});

export function BlockersPage() {
  const { t } = useTranslation();
  const { session } = useAuth();
  const queryClient = useQueryClient();
  const blockersQuery = useQuery({
    queryKey: ["blockers"],
    queryFn: () => api<{ blockers: BlockerSpec[] }>("/blockers"),
  });
  const creatorsQuery = useQuery({
    queryKey: ["creators"],
    queryFn: () => api<CreatorReference[]>("/creators"),
  });
  const [editor, setEditor] = useState<BlockerSpec | null>(null);
  const [editorIndex, setEditorIndex] = useState<number | null>(null);
  const [scopeCandidate, setScopeCandidate] = useState("");
  const [saving, setSaving] = useState(false);
  const [removingIndex, setRemovingIndex] = useState<number | null>(null);

  if (blockersQuery.isLoading || creatorsQuery.isLoading) return <PageLoading />;
  const blockers = blockersQuery.data?.blockers ?? [];
  const creatorOptions = (creatorsQuery.data ?? []).map((creator) => ({
    value: `${creator.service}:${creator.creator_id}`,
    label: `${creator.alias || creator.creator_id} · ${creator.service}`,
  }));

  async function replaceBlockers(next: BlockerSpec[]) {
    if (!session) return;
    setSaving(true);
    try {
      await api<{ blockers: BlockerSpec[] }>("/blockers", {
        method: "PUT",
        body: next,
        csrfToken: session.csrf_token,
      });
      await queryClient.invalidateQueries({ queryKey: ["blockers"] });
      toast.success(t("blockers.saved"));
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
      throw error;
    } finally {
      setSaving(false);
    }
  }

  function openEditor(blocker?: BlockerSpec, index?: number) {
    setEditor(blocker ? structuredClone(blocker) : blankBlocker());
    setEditorIndex(index ?? null);
    setScopeCandidate("");
  }

  async function submitEditor(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editor) return;
    const next = [...blockers];
    if (editorIndex === null) next.push(editor);
    else next[editorIndex] = editor;
    try {
      await replaceBlockers(next);
      setEditor(null);
    } catch {
      // Toast is emitted by replaceBlockers; keep the editor open for correction.
    }
  }

  async function move(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= blockers.length) return;
    const next = [...blockers];
    [next[index], next[target]] = [next[target], next[index]];
    await replaceBlockers(next);
  }

  async function removeBlocker() {
    if (removingIndex === null) return;
    try {
      await replaceBlockers(blockers.filter((_, index) => index !== removingIndex));
      setRemovingIndex(null);
    } catch {
      // Toast is emitted by replaceBlockers; keep the confirmation open for retry.
    }
  }

  function updateEditorScope(mode: "global" | "creators") {
    if (!editor) return;
    setEditor({
      ...editor,
      scope: mode === "global" ? { mode, creators: [] } : { mode, creators: editor.scope.creators },
    });
  }

  function addScopeCreator(value: string) {
    if (!editor || !value) return;
    const creators = Array.from(new Set([...editor.scope.creators, value]));
    setEditor({ ...editor, scope: { mode: "creators", creators } });
    setScopeCandidate("");
  }

  return (
    <div className="grid gap-6">
      <PageHeader
        description={t("blockers.description")}
        title={t("blockers.title")}
        actions={
          <Button variant="primary" onPress={() => openEditor()}>
            <Plus aria-hidden="true" size={18} />
            {t("blockers.add")}
          </Button>
        }
      />

      {!blockers.length ? (
        <EmptyPanel title={t("blockers.empty")} />
      ) : (
        <section className="grid gap-3">
          {blockers.map((blocker, index) => (
            <Surface className="data-list-card rounded-lg border border-border p-4" key={blocker.id}>
              <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_5rem_auto] lg:items-center">
                <div className="flex min-w-0 flex-1 items-start gap-3">
                  <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-default text-muted" aria-hidden="true">
                    <Braces size={18} />
                  </span>
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="break-all font-semibold">{blocker.id}</h2>
                      <Chip color={blocker.enabled ? "success" : "default"} size="sm" variant="soft">
                        {blocker.enabled ? t("common.enabled") : t("common.disabled")}
                      </Chip>
                      <Chip color="accent" size="sm" variant="soft">
                        {blocker.type === "field-match" ? t("blockers.fieldMatch") : blocker.type}
                      </Chip>
                    </div>
                    <p className="mt-1 text-xs text-muted">
                      {blocker.scope.mode === "global"
                        ? t("blockers.global")
                        : `${t("blockers.selectedCreators")}: ${blocker.scope.creators.join(", ")}`}
                    </p>
                  </div>
                </div>
                <div className="list-switch-cell flex min-h-11 items-center justify-center lg:w-20">
                  <CompactSwitch
                    isDisabled={saving}
                    isSelected={blocker.enabled}
                    label={t("blockers.enabled")}
                    onChange={(enabled) => {
                      const next = [...blockers];
                      next[index] = { ...blocker, enabled };
                      void replaceBlockers(next);
                    }}
                  />
                </div>
                <div className="flex flex-wrap items-center justify-center gap-1 lg:justify-end">
                  <IconButton
                    icon={ArrowUp}
                    isDisabled={index === 0 || saving}
                    label={t("tasks.moveUp")}
                    tooltip={index === 0 ? t("tasks.firstInQueue") : t("tasks.moveUp")}
                    onPress={() => void move(index, -1)}
                  />
                  <IconButton
                    icon={ArrowDown}
                    isDisabled={index === blockers.length - 1 || saving}
                    label={t("tasks.moveDown")}
                    tooltip={index === blockers.length - 1 ? t("tasks.lastInQueue") : t("tasks.moveDown")}
                    onPress={() => void move(index, 1)}
                  />
                  <IconButton icon={Pencil} isDisabled={saving} label={t("common.edit")} onPress={() => openEditor(blocker, index)} />
                  <IconButton
                    className="text-danger"
                    icon={Trash2}
                    isDisabled={saving}
                    label={t("blockers.remove")}
                    onPress={() => setRemovingIndex(index)}
                  />
                </div>
              </div>
            </Surface>
          ))}
        </section>
      )}

      <FormModal
        actions={
          <>
            <Button variant="ghost" onPress={() => setEditor(null)}><X aria-hidden="true" size={17} />{t("common.cancel")}</Button>
            <Button form="blocker-form" isPending={saving} type="submit" variant="primary"><Check aria-hidden="true" size={17} />{t("common.save")}</Button>
          </>
        }
        open={editor !== null}
        size="lg"
        title={editorIndex === null ? t("blockers.add") : t("blockers.edit")}
        onOpenChange={(open) => !open && setEditor(null)}
      >
        {editor ? (
          <form className="grid gap-6" id="blocker-form" onSubmit={submitEditor}>
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                icon={Fingerprint}
                isRequired
                label={t("blockers.id")}
                value={editor.id}
                onChange={(id) => setEditor({ ...editor, id })}
              />
              <SelectField
                icon={Braces}
                label={t("blockers.type")}
                options={[{ value: "field-match", label: t("blockers.fieldMatch") }]}
                value={editor.type}
                onChange={(type) => setEditor({ ...editor, type })}
              />
            </div>
            <FormSwitchField
              icon={Power}
              isSelected={editor.enabled}
              label={t("blockers.enabled")}
              onChange={(enabled) => setEditor({ ...editor, enabled })}
            />
            <div className="grid gap-4 border-t border-border pt-5">
              <SelectField
                icon={UsersRound}
                label={t("blockers.scope")}
                options={[
                  { value: "global", label: t("blockers.global") },
                  { value: "creators", label: t("blockers.selectedCreators") },
                ]}
                value={editor.scope.mode}
                onChange={(mode) => updateEditorScope(mode as "global" | "creators")}
              />
              {editor.scope.mode === "creators" ? (
                <div className="grid gap-3">
                  <AutocompleteField
                    icon={UsersRound}
                    label={t("blockers.addScope")}
                    options={creatorOptions.filter((option) => !editor.scope.creators.includes(option.value))}
                    placeholder={t("blockers.addScope")}
                    value={scopeCandidate}
                    onChange={(value) => {
                      setScopeCandidate(value);
                      addScopeCreator(value);
                    }}
                  />
                  <div className="flex flex-wrap gap-2">
                    {editor.scope.creators.map((creator) => (
                      <Chip key={creator} size="sm" variant="soft">
                        {creator}
                        <Button
                          isIconOnly
                          aria-label={`${t("common.remove")} ${creator}`}
                          size="sm"
                          variant="ghost"
                          onPress={() =>
                            setEditor({
                              ...editor,
                              scope: {
                                mode: "creators",
                                creators: editor.scope.creators.filter((item) => item !== creator),
                              },
                            })
                          }
                        >
                          <Trash2 aria-hidden="true" size={12} />
                        </Button>
                      </Chip>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
            <div className="border-t border-border pt-5">
              <ConditionGroupEditor
                group={editor.options.rule ?? blankGroup()}
                onChange={(rule) => setEditor({ ...editor, options: { ...editor.options, rule } })}
              />
            </div>
          </form>
        ) : null}
      </FormModal>

      <ConfirmModal
        actions={
          <>
            <Button variant="ghost" onPress={() => setRemovingIndex(null)}><X aria-hidden="true" size={17} />{t("common.cancel")}</Button>
            <Button isPending={saving} variant="danger" onPress={() => void removeBlocker()}>
              <Trash2 aria-hidden="true" size={17} />
              {t("common.remove")}
            </Button>
          </>
        }
        open={removingIndex !== null}
        size="md"
        title={t("blockers.removeTitle")}
        onOpenChange={(open) => !open && setRemovingIndex(null)}
      >
        <p className="text-sm leading-relaxed text-muted">{t("blockers.removeBody", { id: removingIndex === null ? "" : blockers[removingIndex]?.id })}</p>
      </ConfirmModal>
    </div>
  );
}

function ConditionGroupEditor({
  group,
  onChange,
  removable = false,
  onRemove,
}: {
  group: ConditionGroup;
  onChange: (group: ConditionGroup) => void;
  removable?: boolean;
  onRemove?: () => void;
}) {
  const { t } = useTranslation();
  function updateCondition(index: number, condition: FieldCondition | ConditionGroup) {
    const conditions = [...group.conditions];
    conditions[index] = condition;
    onChange({ ...group, conditions });
  }
  function removeCondition(index: number) {
    if (group.conditions.length === 1) return;
    onChange({ ...group, conditions: group.conditions.filter((_, itemIndex) => itemIndex !== index) });
  }
  return (
    <div className={removable ? "grid gap-4 border-l-2 border-accent/40 pl-4" : "grid gap-4"}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="min-w-44 flex-1">
          <SelectField
            icon={ListTree}
            label={t("blockers.mode")}
            options={[
              { value: "any", label: t("blockers.any") },
              { value: "all", label: t("blockers.all") },
            ]}
            value={group.mode}
            onChange={(mode) => onChange({ ...group, mode: mode as "any" | "all" })}
          />
        </div>
        <FormSwitchField icon={Ban} isSelected={group.negate} label={t("blockers.negate")} onChange={(negate) => onChange({ ...group, negate })} />
        {removable ? (
          <Button isIconOnly aria-label={t("common.remove")} variant="ghost" onPress={onRemove}>
            <Trash2 aria-hidden="true" size={17} />
          </Button>
        ) : null}
      </div>
      <div className="grid gap-4">
        {group.conditions.map((condition, index) =>
          condition.kind === "group" ? (
            <ConditionGroupEditor
              group={condition}
              key={`group-${index}`}
              removable
              onChange={(next) => updateCondition(index, next)}
              onRemove={() => removeCondition(index)}
            />
          ) : (
            <ConditionEditor
              condition={condition}
              key={`field-${index}`}
              removable={group.conditions.length > 1}
              onChange={(next) => updateCondition(index, next)}
              onRemove={() => removeCondition(index)}
            />
          ),
        )}
      </div>
      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant="outline" onPress={() => onChange({ ...group, conditions: [...group.conditions, blankCondition()] })}>
          <Plus aria-hidden="true" size={16} />
          {t("blockers.addCondition")}
        </Button>
        <Button size="sm" variant="outline" onPress={() => onChange({ ...group, conditions: [...group.conditions, blankGroup()] })}>
          <GitBranchPlus aria-hidden="true" size={16} />
          {t("blockers.addGroup")}
        </Button>
      </div>
    </div>
  );
}

function ConditionEditor({
  condition,
  onChange,
  onRemove,
  removable,
}: {
  condition: FieldCondition;
  onChange: (condition: FieldCondition) => void;
  onRemove: () => void;
  removable: boolean;
}) {
  const { t } = useTranslation();
  const fieldOptions = [
    { value: "title", label: t("blockers.fields.title") },
    { value: "content", label: t("blockers.fields.content") },
    { value: "tags[*]", label: t("blockers.fields.tags") },
    { value: "file.name", label: t("blockers.fields.fileName") },
    { value: "attachments[*].name", label: t("blockers.fields.attachmentName") },
    { value: "id", label: t("blockers.fields.postId") },
    { value: "service", label: t("blockers.fields.service") },
  ];
  const operatorOptions = [
    { value: "contains", label: t("blockers.operators.contains") },
    { value: "equals", label: t("blockers.operators.equals") },
    { value: "regex", label: t("blockers.operators.regex") },
    { value: "exists", label: t("blockers.operators.exists") },
  ];
  return (
    <div className="grid gap-4 border-l-2 border-border pl-4">
      <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_minmax(0,0.75fr)_auto]">
        <SelectField
          icon={ListTree}
          label={t("blockers.field")}
          options={fieldOptions}
          value={condition.field}
          onChange={(field) => onChange({ ...condition, field })}
        />
        <SelectField
          icon={Equal}
          label={t("blockers.operator")}
          options={operatorOptions}
          value={condition.operator}
          onChange={(operator) =>
            onChange({
              ...condition,
              operator: operator as FieldCondition["operator"],
              values: operator === "exists" ? [] : condition.values,
            })
          }
        />
        <Button isIconOnly aria-label={t("common.remove")} isDisabled={!removable} variant="ghost" onPress={onRemove}>
          <Trash2 aria-hidden="true" size={17} />
        </Button>
      </div>
      {condition.operator !== "exists" ? (
        <ChipListField
          commitOnComma={condition.operator !== "regex"}
          description={t("blockers.valuesHint")}
          icon={Braces}
          label={t("blockers.values")}
          values={condition.values.filter(Boolean)}
          onChange={(values) => onChange({ ...condition, values })}
        />
      ) : null}
      <div className="flex flex-wrap items-center gap-5">
        {condition.operator !== "exists" ? (
          <FormCheckbox
            icon={CaseSensitive}
            isSelected={condition.case_sensitive}
            label={t("blockers.caseSensitive")}
            onChange={(case_sensitive) => onChange({ ...condition, case_sensitive })}
          />
        ) : null}
        <FormCheckbox
          icon={Ban}
          isSelected={condition.negate}
          label={t("blockers.negate")}
          onChange={(negate) => onChange({ ...condition, negate })}
        />
      </div>
    </div>
  );
}
