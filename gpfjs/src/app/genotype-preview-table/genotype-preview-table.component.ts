import { Input, Component } from '@angular/core';
import { GenotypePreview, GenotypePreviewVariantsArray, GenotypePreviewInfo } from '../genotype-preview-model/genotype-preview';
import { AdditionalColumn } from '../datasets/datasets';

@Component({
  selector: 'gpf-genotype-preview-table',
  templateUrl: './genotype-preview-table.component.html',
  styleUrls: ['./genotype-preview-table.component.css']
})
export class GenotypePreviewTableComponent {
  @Input() genotypePreviewInfo: GenotypePreviewInfo;
  @Input() genotypePreviewVariantsArray: GenotypePreviewVariantsArray;
  @Input() columns: Array<AdditionalColumn>;
  constructor(
  ) { }

  comparator(field: string) {
    if (field === 'variant.location') {
      return this.locationComparator;
    } else {
      return (a: GenotypePreview, b: GenotypePreview) => {
        let leftVal = a.get(field);
        let rightVal = b.get(field);

        if (leftVal == "-") leftVal = null;
        if (rightVal == "-") rightVal = null;

        if (leftVal == null && rightVal == null) {
          return 0;
        }
        if (leftVal == null) {
          return -1;
        }
        if (rightVal == null) {
          return 1;
        }

        if (leftVal.constructor === Array) {
          leftVal = leftVal[0];
        }

        if (rightVal.constructor === Array) {
          rightVal = rightVal[0];
        }

        if (!isNaN(leftVal) && !isNaN(rightVal)) {
          return +leftVal - +rightVal;
        }

        return leftVal.localeCompare(rightVal);
      };
    }
  }


  locationComparator(a: GenotypePreview, b: GenotypePreview): number {
    const XYMStringToNum = (str: string): number => {
      if (str === 'X') {
        return 100;
      }
      if (str === 'Y') {
        return 101;
      }
      if (str === 'M') {
        return 102;
      }
      return +str;
    };

    const leftVar = a.get('variant.location');
    const rightVar = b.get('variant.location');

    const leftArr = leftVar.split(':');
    const rightArr = rightVar.split(':');

    if (leftArr[0] === rightArr[0]) {
      return +leftArr[1] - +rightArr[1];
    } else {
      return XYMStringToNum(leftArr[0]) - XYMStringToNum(rightArr[0]);
    }

  }
}
