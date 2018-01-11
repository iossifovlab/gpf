// Based on https://stackoverflow.com/questions/40776351/what-is-the-best-way-to-listen-for-component-resize-events-within-an-angular2-co

import { Injectable, NgZone } from '@angular/core';
import * as elementResizeDetectorMaker from 'element-resize-detector';

@Injectable()
export class ResizeService {
  private resizeDetector: any;

  constructor(
    private zone: NgZone
  ) {
    this.resizeDetector = elementResizeDetectorMaker({ strategy: 'scroll' });
  }

  addResizeEventListener(element: HTMLElement, handler: Function) {
    this.resizeDetector.listenTo(element, () => {
      this.zone.run(() => handler());
    });
  }

  removeResizeEventListener(element: HTMLElement) {
    this.resizeDetector.uninstall(element);
  }
}
