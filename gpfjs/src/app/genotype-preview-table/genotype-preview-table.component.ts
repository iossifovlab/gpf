import { Input, Component } from '@angular/core';
import { GenotypePreview, GenotypePreviewsArray } from './genotype-preview';
import { PhenoColumn } from '../datasets/datasets';

@Component({
  selector: 'gpf-genotype-preview-table',
  templateUrl: './genotype-preview-table.component.html',
  styleUrls: ['./genotype-preview-table.component.css']
})
export class GenotypePreviewTableComponent {
  @Input() genotypePreviewsArray: GenotypePreviewsArray;
  @Input() phenoColumns: Array<PhenoColumn>;
  constructor(
  ) { }

  additionalDataComparator(field: string) {
    return (a: any, b: any) => {
      let leftVal = a['additionalData'][field];
      let rightVal = b['additionalData'][field];

      if (leftVal == null && rightVal == null) { return 0; }
      if (leftVal == null) { return -1; }
      if (rightVal == null) { return 1; }

      if (!isNaN(leftVal) && !isNaN(rightVal)) {
        return +leftVal - +rightVal;
      }

      return leftVal.localeCompare(rightVal);
    };
  }


  locationComparator(a: any, b: any): number {
    let XYMStringToNum = (str: string): number => {
      if (str === 'X') { return 100; }
      if (str === 'Y') { return 101; }
      if (str === 'M') { return 102; }
      return +str;
    };

    let leftVar = a.location;
    let rightVar = b.location;

    let leftArr = leftVar.split(':');
    let rightArr = rightVar.split(':');

    if (leftArr[0] === rightArr[0]) {
      return +leftArr[1] - +rightArr[1];
    } else {
      return XYMStringToNum(leftArr[0]) - XYMStringToNum(rightArr[0]);
    }

  }
}
