// Vitest setup: register jest-dom and vitest-axe (accessibility) matchers.
import "@testing-library/jest-dom/vitest";
import * as axeMatchers from "vitest-axe/matchers";
import { expect, vi } from "vitest";

expect.extend(axeMatchers);

// axe-core checks color contrast through canvas APIs that jsdom does not
// implement. A tiny stub keeps accessibility tests focused and stderr clean.
HTMLCanvasElement.prototype.getContext = vi.fn(() => null);
