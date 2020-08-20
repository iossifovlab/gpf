import { ErrorHandler, Injectable, Injector } from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { GlobalErrorDisplayComponent } from 'app/global-error-display/global-error-display.component';

@Injectable()
export class GlobalErrorHandler implements ErrorHandler {
  constructor(
    private injector: Injector,
  ) { }

  modalService: NgbModal;

  handleError(error: any): void {
    console.error(error);

    // this.modalService = this.injector.get(NgbModal);
    // if (!this.modalService.hasOpenModals()) {
    //   this.modalService.open(GlobalErrorDisplayComponent, {centered: true, size: 'sm', windowClass: 'global-error-modal'});
    // }
  }
}
