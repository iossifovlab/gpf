import { Component, Input, TemplateRef } from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { PopupComponent } from 'app/popup/popup.component';

@Component({
    selector: 'gpf-helper-modal',
    templateUrl: './helper-modal.component.html',
    styleUrls: ['./helper-modal.component.css'],
    standalone: false
})
export class HelperModalComponent {
  @Input() public modalContent: TemplateRef<unknown> | string;
  @Input() public isMarkdown = false;
  @Input() public buttonText = '';

  public constructor(
    private modalService: NgbModal
  ) {}

  public showHelp(): void {
    if (this.isMarkdown && typeof this.modalContent === 'string') {
      const modalRef = this.modalService.open(PopupComponent, {
        size: 'lg',
        centered: true
      });

      (modalRef.componentInstance as PopupComponent).data = this.modalContent;
    } else if (!this.isMarkdown && this.modalContent instanceof TemplateRef) {
      this.modalService.open(
        this.modalContent,
        {
          animation: false,
          centered: true,
          modalDialogClass: 'modal-dialog-centered'
        }
      );
    } else {
      this.modalService.open('Error: invalid modal content!', {
        size: 'lg',
        centered: true
      });
    }
  }
}
