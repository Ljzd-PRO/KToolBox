import { StreamLanguage } from "@codemirror/language";
import { lintGutter, linter, type Diagnostic } from "@codemirror/lint";
import { properties } from "@codemirror/legacy-modes/mode/properties";
import { toml } from "@codemirror/legacy-modes/mode/toml";
import CodeMirror, { EditorView } from "@uiw/react-codemirror";
import { useId, useMemo } from "react";

import { useTheme } from "../lib/theme";

export type LegacyConfigEditorIssue = {
  line?: number | null;
  column?: number | null;
  message: string;
};

export function LegacyConfigEditor({
  description,
  format,
  issues,
  label,
  placeholder,
  value,
  onChange,
}: {
  description: string;
  format: "env" | "toml";
  issues: LegacyConfigEditorIssue[];
  label: string;
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
}) {
  const labelId = useId();
  const descriptionId = useId();
  const theme = useTheme();
  const extensions = useMemo(
    () => [
      StreamLanguage.define(format === "env" ? properties : toml),
      EditorView.contentAttributes.of({
        "aria-describedby": descriptionId,
        "aria-labelledby": labelId,
      }),
      lintGutter(),
      linter(
        (view) =>
          issues.flatMap<Diagnostic>((issue) => {
            if (!issue.line || issue.line < 1 || issue.line > view.state.doc.lines) {
              return [];
            }
            const line = view.state.doc.line(issue.line);
            const from = Math.min(
              line.to,
              line.from + Math.max(0, (issue.column ?? 1) - 1),
            );
            return [
              {
                from,
                to: Math.max(from, line.to),
                severity: "error",
                message: issue.message,
              },
            ];
          }),
        { delay: 0 },
      ),
    ],
    [descriptionId, format, issues, labelId],
  );

  return (
    <div className="legacy-config-editor grid min-w-0 gap-1.5">
      <label className="text-sm font-semibold text-foreground" id={labelId}>
        {label}
      </label>
      <CodeMirror
        basicSetup={{
          bracketMatching: true,
          closeBrackets: true,
          foldGutter: false,
          highlightActiveLine: true,
          highlightActiveLineGutter: true,
          lineNumbers: true,
          searchKeymap: true,
        }}
        extensions={extensions}
        height="18rem"
        maxHeight="24rem"
        minHeight="12rem"
        placeholder={placeholder}
        theme={theme.effective}
        value={value}
        onChange={onChange}
      />
      <p className="text-xs leading-5 text-muted" id={descriptionId}>
        {description}
      </p>
    </div>
  );
}
