import { Component, Input } from '@angular/core';

import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  templateUrl: './pheno-browser-modal-content.component.html',
  styleUrls: ['./pheno-browser-modal-content.component.css']
})
export class PhenoBrowserModalContentComponent {
  @Input() imageUrl;

  constructor(public activeModal: NgbActiveModal) {}
}
