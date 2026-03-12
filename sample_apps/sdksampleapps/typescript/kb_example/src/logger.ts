/**
 * Standard logger for kb_example scripts.
 * Use this instead of console so output is consistent and easy to follow.
 */

const LEVEL = {
  INFO: "info",
  WARN: "warn",
  ERROR: "error",
} as const;

function formatMessage(level: string, message: string, rest: unknown[]): void {
  const prefix = `[${level.toUpperCase()}]`;
  const args = rest.length > 0 ? rest : [];
  switch (level) {
    case LEVEL.WARN:
      console.warn(prefix, message, ...args);
      break;
    case LEVEL.ERROR:
      console.error(prefix, message, ...args);
      break;
    default:
      console.log(prefix, message, ...args);
  }
}

export const logger = {
  /** Log an informational message. */
  info(message: string, ...args: unknown[]): void {
    formatMessage(LEVEL.INFO, message, args);
  },

  /** Log a warning. */
  warn(message: string, ...args: unknown[]): void {
    formatMessage(LEVEL.WARN, message, args);
  },

  /** Log an error. */
  error(message: string, ...args: unknown[]): void {
    formatMessage(LEVEL.ERROR, message, args);
  },

  /** Log a label and a value as pretty-printed JSON. Use for API responses. */
  json(label: string, value: unknown): void {
    const formatted =
      typeof value === "string" ? value : JSON.stringify(value, null, 2);
    console.log(`[INFO] ${label}\n${formatted}`);
  },
};
