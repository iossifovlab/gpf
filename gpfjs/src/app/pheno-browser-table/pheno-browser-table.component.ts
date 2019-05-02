import { Component, Input } from '@angular/core';

import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { PhenoBrowserModalContentComponent } from '../pheno-browser-modal-content/pheno-browser-modal-content.component';
import { PhenoMeasures } from '../pheno-browser/pheno-browser';

import { PValueIntensityPipe } from '../utils/p-value-intensity.pipe';


@Component({
  selector: 'gpf-pheno-browser-table',
  templateUrl: './pheno-browser-table.component.html',
  styleUrls: ['./pheno-browser-table.component.css']
})
export class PhenoBrowserTableComponent {

  constructor(
    private modalService: NgbModal,
    private pValueIntensityPipe: PValueIntensityPipe
) { }

  @Input('measures') measures: PhenoMeasures;

//  minDomainComparator(a: any, b: any): number {
//    let leftVal = a.valuesDomain[0];
//    let rightVal = b.valuesDomain[0];
//
//    return PhenoBrowserTableComponent.compare(leftVal, rightVal);
//  }
//  maxDomainComparator(a: any, b: any): number {
//    let leftVal = a.valuesDomain[1];
//    let rightVal = b.valuesDomain[1];
//
//    return PhenoBrowserTableComponent.compare(leftVal, rightVal);
//  }

  static compare(leftVal: any, rightVal: any): number {
    if (leftVal == null && rightVal == null) {
      return 0;
    }
    if (leftVal == null) {
      return -1;
    }
    if (rightVal == null) {
      return 1;
    }

    if (!isNaN(leftVal) && !isNaN(rightVal)) {
      return +leftVal - +rightVal;
    }

    return leftVal.localeCompare(rightVal);
  }


  openModal(content, imageUrl) {
    if (imageUrl) {
      const modalRef = this.modalService.open(PhenoBrowserModalContentComponent, {
        windowClass: 'modal-fullscreen'
      });
      modalRef.componentInstance.imageUrl = imageUrl;
    }
  }

  getBackgroundColor(pValue: string): string {
    let intensity = this.pValueIntensityPipe.transform(pValue);

    return `rgba(255, ${intensity}, ${intensity}, 0.8)`;
  }

}
