import { Component, Input, inject } from '@angular/core';

import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  templateUrl: './pheno-browser-modal-content.component.html',
  styleUrls: ['./pheno-browser-modal-content.component.css'],
  standalone: false
})
export class PhenoBrowserModalContentComponent {
  public activeModal = inject(NgbActiveModal);

  @Input() public imageUrl;
}
