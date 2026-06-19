// Register vitest-axe's custom matchers (e.g. toHaveNoViolations) with Vitest's
// assertion types so TypeScript recognises them in tests.
import "vitest";
import type { AxeMatchers } from "vitest-axe/matchers";

declare module "vitest" {
  // eslint-disable-next-line @typescript-eslint/no-empty-object-type
  interface Assertion<T = any> extends AxeMatchers {}
  interface AsymmetricMatchersContaining extends AxeMatchers {}
}
