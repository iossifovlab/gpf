// Based on https://stackoverflow.com/questions/40776351/what-is-the-best-way-to-listen-for-component-resize-events-within-an-angular2-co

import { Injectable, NgZone, inject } from '@angular/core';
import elementResizeDetectorMaker from 'element-resize-detector';

@Injectable()
export class ResizeService {
  private zone = inject(NgZone);

  private resizeDetector: any;

  public constructor() {
    this.resizeDetector = elementResizeDetectorMaker({ strategy: 'scroll' });
  }

  public addResizeEventListener(element: HTMLElement, handler: Function): void {
    this.resizeDetector.listenTo(element, () => {
      this.zone.run(() => handler());
    });
  }

  public removeResizeEventListener(element: HTMLElement): void {
    this.resizeDetector.uninstall(element);
  }
}
