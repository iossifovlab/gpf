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

  regressionCompare(regressionId: string, field: string) {
    return (a: any, b: any) => {
      let leftVal = a['regressions'][regressionId];
      let rightVal = b['regressions'][regressionId];

      leftVal = !leftVal || isNaN(leftVal[field]) ? null : leftVal[field];
      rightVal = !rightVal || isNaN(rightVal[field]) ? null : rightVal[field];

      if (leftVal == null && rightVal == null) { return 0; }
      if (leftVal == null) { return -1; }
      if (rightVal == null) { return 1; }
      return +leftVal - +rightVal;
    }
  }

  getRegressionIds() {
    return Object.getOwnPropertyNames(this.measures.regressionNames);
  }

  getRegressionName(regressionId: string) {
    if(this.measures.regressionNames[regressionId]) {
      return this.measures.regressionNames[regressionId];
    }
    else {
      return regressionId;
    }
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
    const intensity = this.pValueIntensityPipe.transform(pValue);

    return `rgba(255, ${intensity}, ${intensity}, 0.8)`;
  }

}
