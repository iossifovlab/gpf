declare function elementResizeDetectorMaker(options?: elementResizeDetectorMaker.ErdmOptions): elementResizeDetectorMaker.Erd;

declare namespace elementResizeDetectorMaker {
    interface ErdmOptions {
        strategy?: 'scroll' | 'object';
    }

    interface Erd {
        listenTo(element: HTMLElement, callback: (elem: HTMLElement) => void);
        removeListener(element: HTMLElement, callback: (elem: HTMLElement) => void);
        removeAllListeners(element: HTMLElement);
        uninstall(element: HTMLElement);
    }
}

export = elementResizeDetectorMaker;
