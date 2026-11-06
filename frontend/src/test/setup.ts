import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

// jsdom has no canvas. ECharts only uses one to measure text: answer "no context" without the
// "Not implemented" message jsdom prints on every call.
Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', { value: () => null });

afterEach(() => {
  cleanup();
});
