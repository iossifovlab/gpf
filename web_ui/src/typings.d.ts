// Minimal type stubs for the oboe streaming JSON parser. The library
// ships no .d.ts; this is the surface QueryService actually uses.
declare module 'oboe' {
  interface OboeInstance {
    node(pattern: string, listener: (data: unknown) => void): OboeInstance;
    done(listener: (data: unknown) => void): OboeInstance;
    fail(listener: (error: { thrown?: Error; statusCode?: number; body?: string }) => void): OboeInstance;
    abort(): void;
  }

  interface OboeOptions {
    url: string;
    method?: string;
    headers?: Record<string, string>;
    body?: unknown;
    withCredentials?: boolean;
  }

  function oboe(opts: OboeOptions): OboeInstance;
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace oboe {
    type Instance = OboeInstance;
  }

  export = oboe;
}
