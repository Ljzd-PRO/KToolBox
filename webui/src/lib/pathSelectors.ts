import type { PathSelector } from "../types";

export const TASK_OUTPUT_PATH_SELECTOR: PathSelector = {
  kind: "directory",
  scope: "host",
  value_mode: "absolute",
};
