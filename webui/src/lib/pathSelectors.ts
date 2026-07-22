import type { PathSelector } from "../types";

export const TASK_OUTPUT_PATH_SELECTOR: PathSelector = {
  kind: "directory",
  scope: "project",
  value_mode: "absolute",
};
