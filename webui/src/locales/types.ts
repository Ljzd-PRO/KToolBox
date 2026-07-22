export type TranslationShape<T> = {
  readonly [K in keyof T]: T[K] extends string ? string : TranslationShape<T[K]>;
} & Record<string, unknown>;
