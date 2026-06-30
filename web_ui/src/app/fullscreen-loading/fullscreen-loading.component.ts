// Loosely based on https://github.com/oxycoder/ng2-loading-animate

import { Component, inject } from '@angular/core';
import { FullscreenLoadingService } from './fullscreen-loading.service';

@Component({
  selector: 'gpf-fullscreen-loading',
  templateUrl: './fullscreen-loading.component.html',
  styleUrls: ['./fullscreen-loading.component.css'],
  standalone: false
})
export class FullscreenLoadingComponent {
  private fullscreenLoadingService = inject(FullscreenLoadingService);

  public showLoading = false;

  public constructor() {
    const fullscreenLoadingService = this.fullscreenLoadingService;

    fullscreenLoadingService.loadingStateChange.subscribe((state: boolean) => {
      this.showLoading = state;
    });
  }

  public cancelLoading(): void {
    this.fullscreenLoadingService.interruptEvent.emit(true);
  }
}
