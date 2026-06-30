Object.defineProperty(window, 'CSS', { value: null });
Object.defineProperty(document, 'doctype', {
  value: '<!DOCTYPE html>',
});
Object.defineProperty(window, 'getComputedStyle', {
  value: () => {
    return {
      display: 'none',
      appearance: ['-webkit-appearance'],
    };
  },
});
/**
 * ISSUE: https://github.com/angular/material2/issues/7101
 * Workaround for JSDOM missing transform property
 */
Object.defineProperty(document.body.style, 'transform', {
  value: () => {
    return {
      enumerable: true,
      configurable: true,
    };
  },
});

/**
 * JSDOM doesn't support the dataset property on HTMLElement
 * Override it to be writable
 */
try {
  Object.defineProperty(HTMLElement.prototype, 'dataset', {
    get() {
      if (!this.__dataset) {
        this.__dataset = {};
      }
      return this.__dataset;
    },
    set(value: Record<string, string>) {
      this.__dataset = value;
    },
    configurable: true,
    enumerable: true,
  });
} catch (e) {
  // Polyfill may have already been applied
}

/**
 * Ensure global timer functions are available in all scopes
 * This fixes ReferenceError: setTimeout is not defined in tests
 */
if (typeof window !== 'undefined' && !window.setTimeout) {
  window.setTimeout = setTimeout;
  window.setInterval = setInterval;
  window.clearTimeout = clearTimeout;
  window.clearInterval = clearInterval;
}
