//Loosely based on https://github.com/oxycoder/ng2-loading-animate

import { Injectable, EventEmitter } from '@angular/core';

@Injectable()
export class FullscreenLoadingService {
  loadingStateChange: EventEmitter<boolean> = new EventEmitter();

  setLoadingStart() {
    this.loadingStateChange.emit(true);
  }

  setLoadingStop() {
    this.loadingStateChange.emit(false);
  }
}
