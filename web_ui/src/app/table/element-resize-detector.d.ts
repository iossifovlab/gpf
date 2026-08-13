// Minimal type stubs for element-resize-detector. The library ships no .d.ts
// and there is no @types package; this is the surface ResizeService uses.
//
// This must be a `declare module` block: written as a plain top-level
// `export =`, the file is just an unreferenced module and imports of
// 'element-resize-detector' stay unresolved.
declare module 'element-resize-detector' {
  interface ErdmOptions {
    strategy?: 'scroll' | 'object';
  }

  interface Erd {
    listenTo(element: HTMLElement, callback: (elem: HTMLElement) => void): void;
    removeListener(element: HTMLElement, callback: (elem: HTMLElement) => void): void;
    removeAllListeners(element: HTMLElement): void;
    uninstall(element: HTMLElement): void;
  }

  function elementResizeDetectorMaker(options?: ErdmOptions): Erd;
  namespace elementResizeDetectorMaker {
    type Detector = Erd;
    type Options = ErdmOptions;
  }

  export = elementResizeDetectorMaker;
}
