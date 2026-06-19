// Vitest setup: register jest-dom and vitest-axe (accessibility) matchers.
import "@testing-library/jest-dom/vitest";
import * as axeMatchers from "vitest-axe/matchers";
import { expect } from "vitest";

expect.extend(axeMatchers);
