import { Component, Input } from '@angular/core';

import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import {
  PhenoBrowserModalContentComponent
} from '../pheno-browser-modal-content/pheno-browser-modal-content.component';
import { PhenoMeasures } from '../pheno-browser/pheno-browser';
import { PValueIntensityPipe } from '../utils/p-value-intensity.pipe';

@Component({
  selector: 'gpf-pheno-browser-table',
  templateUrl: './pheno-browser-table.component.html',
  styleUrls: ['./pheno-browser-table.component.css']
})
export class PhenoBrowserTableComponent {
  @Input() public measures: PhenoMeasures;

  public constructor(
    private modalService: NgbModal,
    private pValueIntensityPipe: PValueIntensityPipe
  ) { }

  public static compare(leftVal: any, rightVal: any): number {
    if (leftVal === null && rightVal === null) {
      return 0;
    }
    if (leftVal === null) {
      return -1;
    }
    if (rightVal === null) {
      return 1;
    }

    if (!isNaN(leftVal) && !isNaN(rightVal)) {
      return Number(leftVal) - Number(rightVal);
    }

    return leftVal.localeCompare(rightVal);
  }

  public regressionCompare(regressionId: string, field: string) {
    return (a: any, b: any) => {
      let leftVal = a['regressions'][regressionId];
      let rightVal = b['regressions'][regressionId];

      leftVal = !leftVal || isNaN(leftVal[field]) ? null : leftVal[field];
      rightVal = !rightVal || isNaN(rightVal[field]) ? null : rightVal[field];

      if (leftVal === null && rightVal === null) {
        return 0;
      }
      if (leftVal === null) {
        return -1;
      }
      if (rightVal === null) {
        return 1;
      }
      return Number(leftVal) - Number(rightVal);
    };
  }

  public getRegressionIds(): string[] {
    return Object.getOwnPropertyNames(this.measures.regressionNames);
  }

  public openModal(imageUrl: string): void {
    if (imageUrl) {
      const modalRef = this.modalService.open(PhenoBrowserModalContentComponent, {
        windowClass: 'modal-fullscreen'
      });
      modalRef.componentInstance.imageUrl = imageUrl;
    }
  }

  public getBackgroundColor(pValue: string): string {
    const intensity = this.pValueIntensityPipe.transform(pValue) as number;

    return `rgba(255, ${intensity}, ${intensity}, 0.8)`;
  }
}
