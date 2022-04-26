// Loosely based on https://github.com/oxycoder/ng2-loading-animate

import { Injectable, EventEmitter } from '@angular/core';

@Injectable()
export class FullscreenLoadingService {
  public loadingStateChange: EventEmitter<boolean> = new EventEmitter<boolean>();

  public setLoadingStart(): void {
    this.loadingStateChange.emit(true);
  }

  public setLoadingStop(): void {
    this.loadingStateChange.emit(false);
  }
}
