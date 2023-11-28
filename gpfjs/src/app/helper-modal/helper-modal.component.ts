import { Component, Input } from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { PopupComponent } from 'app/popup/popup.component';

@Component({
  selector: 'gpf-helper-modal',
  templateUrl: './helper-modal.component.html',
  styleUrls: ['./helper-modal.component.css']
})
export class HelperModalComponent {
  @Input() public modalContent: string;

  public constructor(
    private modalService: NgbModal
  ) {}
  public showHelp(): void {
    const modalRef = this.modalService.open(PopupComponent, {
      size: 'lg',
      centered: true
    });

    (modalRef.componentInstance as PopupComponent).data = this.modalContent;
  }
}
