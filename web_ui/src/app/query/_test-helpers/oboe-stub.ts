// Test-only helper for QueryService specs (tb-z39.1).
//
// QueryService imports oboe as a default export and uses a fluent
// chain: `oboe(opts).node(...).done(...).fail(...)`. The chain
// callbacks drive the streamingSubject lifecycle — emitting partial
// rows, the null sentinel on done, and on fail. To exercise that
// lifecycle from a spec we need to capture the SUT's callbacks so
// the test can invoke them synchronously.
//
// Usage:
//   // top of spec:
//   jest.mock('oboe', () => ({ __esModule: true, default: jest.fn() }));
//   import { makeOboeStub } from './_test-helpers/oboe-stub';
//
//   // inside beforeEach (after TestBed.inject):
//   const oboe = makeOboeStub();
//
//   // inside an it-block:
//   service.streamPost('url', { ... });
//   const cb = oboe.latest();
//   cb.node?.({ row: 1 });
//   cb.done?.();

export type OboeCallbacks = {
  node?: (data: unknown) => void;
  done?: (data?: unknown) => void;
  fail?: (err: unknown) => void;
  abort: jest.Mock;
};

type OboeChain = {
  node: (pattern: string, cb: (data: unknown) => void) => OboeChain;
  done: (cb: (data?: unknown) => void) => OboeChain;
  fail: (cb: (err: unknown) => void) => OboeChain;
  abort: jest.Mock;
};

export type OboeStub = {
  instance: jest.Mock;
  latest: () => OboeCallbacks;
};

/**
 * Wires the module-level `jest.mock('oboe', ...)` mock so each call
 * to `oboe(opts)` returns a fresh fluent chain that records the
 * SUT's `.node` / `.done` / `.fail` callbacks. Tests drive the
 * lifecycle by invoking the captured callbacks via `latest()`.
 *
 * The caller must have placed a top-of-file
 *   jest.mock('oboe', () => ({ __esModule: true, default: jest.fn() }));
 * before any import that pulls in QueryService. (Jest hoists
 * `jest.mock` calls per-file; calling `makeOboeStub()` only resets
 * and configures that already-installed mock.)
 */
export function makeOboeStub(): OboeStub {
  const oboeModule: { default: jest.Mock } = jest.requireMock('oboe');
  const instance = oboeModule.default;
  instance.mockReset();

  const captured: OboeCallbacks[] = [];

  instance.mockImplementation((): OboeChain => {
    const callbacks: OboeCallbacks = { abort: jest.fn() };
    captured.push(callbacks);

    const chain: OboeChain = {
      node: function(_pattern: string, cb: (data: unknown) => void): OboeChain {
        callbacks.node = cb;
        return chain;
      },
      done: function(cb: (data?: unknown) => void): OboeChain {
        callbacks.done = cb;
        return chain;
      },
      fail: function(cb: (err: unknown) => void): OboeChain {
        callbacks.fail = cb;
        return chain;
      },
      abort: callbacks.abort,
    };

    return chain;
  });

  return {
    instance: instance,
    latest: function(): OboeCallbacks {
      if (captured.length === 0) {
        throw new Error(
          'makeOboeStub.latest(): no oboe(opts) call has happened yet'
        );
      }
      return captured[captured.length - 1];
    },
  };
}
