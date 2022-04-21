import { ErrorHandler, Injectable, Injector } from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { GlobalErrorDisplayComponent } from 'app/global-error-display/global-error-display.component';
import { environment } from '../../environments/environment';

@Injectable()
export class GlobalErrorHandler implements ErrorHandler {
  public constructor(
    private injector: Injector,
  ) { }

  private modalService: NgbModal;

  public handleError(error): void {
    console.error(error);

    if (!environment.production) {
      this.modalService = this.injector.get(NgbModal);
      if (!this.modalService.hasOpenModals()) {
        this.modalService.open(
          GlobalErrorDisplayComponent,
          {centered: true, size: 'sm', windowClass: 'global-error-modal'}
        );
      }
    }
  }
}
