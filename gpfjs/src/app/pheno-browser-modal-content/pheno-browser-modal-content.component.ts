import { Component, Input } from '@angular/core';

import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
    templateUrl: './pheno-browser-modal-content.component.html',
    styleUrls: ['./pheno-browser-modal-content.component.css'],
    standalone: false
})
export class PhenoBrowserModalContentComponent {
  @Input() public imageUrl;

  public constructor(public activeModal: NgbActiveModal) {}
}
