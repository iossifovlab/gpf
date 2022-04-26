// Loosely based on https://github.com/oxycoder/ng2-loading-animate

import { Component } from '@angular/core';
import { FullscreenLoadingService } from './fullscreen-loading.service';

@Component({
  selector: 'gpf-fullscreen-loading',
  templateUrl: './fullscreen-loading.component.html',
  styleUrls: ['./fullscreen-loading.component.css']
})
export class FullscreenLoadingComponent {
  public showLoading = false;

  public constructor(
    private fullscreenLoadingService: FullscreenLoadingService
  ) {
    fullscreenLoadingService.loadingStateChange.subscribe((state: boolean) => {
      this.showLoading = state;
    });
  }
}
