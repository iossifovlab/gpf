import {
  OnInit,
  Component,
  HostListener,
  Input,
  ViewChildren,
  ChangeDetectionStrategy
} from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import {
  PhenoBrowserModalContentComponent
} from '../pheno-browser-modal-content/pheno-browser-modal-content.component';
import { PhenoMeasure, PhenoMeasures } from '../pheno-browser/pheno-browser';
import { SortingButtonsComponent } from 'app/sorting-buttons/sorting-buttons.component';
import { isNumber, isString } from 'lodash';

@Component({
  selector: 'gpf-pheno-browser-table',
  templateUrl: './pheno-browser-table.component.html',
  styleUrls: ['./pheno-browser-table.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class PhenoBrowserTableComponent implements OnInit {
  @Input() public measures: PhenoMeasures;
  @Input() public measuresChangeTick: number;
  @ViewChildren(SortingButtonsComponent) public sortingButtonsComponents: SortingButtonsComponent[];


  public singleColumnWidth;
  public columnsCount = 4;
  public sortBy: string;
  public orderBy = 'desc';

  public constructor(
    private modalService: NgbModal
  ) { }

  public ngOnInit(): void {
    this.columnsCount += 2*Object.keys(this.measures.regressionNames).length;
    if (this.measures.hasDescriptions) {
      this.columnsCount += 1;
    }
    this.onResize();
  }

  public sort(sortBy: string, orderBy: string): void {
    if (this.sortBy !== sortBy) {
      this.resetSortButtons();
    }

    this.sortBy = sortBy;
    this.orderBy = orderBy;

    const sortButton = this.sortingButtonsComponents.find(
      sortingButtonsComponent => sortingButtonsComponent.id === this.sortBy
    );

    if (sortButton) {
      sortButton.emitSort();
    }

    this.sortTable(this.measures.measures, this.orderBy, this.sortBy);
  }

  public sortTable(data: PhenoMeasure[], orderBy: string, sortBy: string): void {
    data.sort((m1, m2) => {
      let a: string | number;
      let b: string | number;
      if (sortBy.includes('pvalueRegressionMale')) {
        const arr = sortBy.split('.');
        a = m1.regressions.getReg(arr[0]).pvalueRegressionMale;
        b = m2.regressions.getReg(arr[0]).pvalueRegressionMale;
      } else if (sortBy.includes('pvalueRegressionFemale')) {
        const arr = sortBy.split('.');
        a = m1.regressions.getReg(arr[0]).pvalueRegressionFemale;
        b = m2.regressions.getReg(arr[0]).pvalueRegressionFemale;
      } else {
        a = m1[sortBy] as string;
        b = m2[sortBy] as string;
      }

      const compareResult = orderBy === 'asc' ? this.comparator(a, b) : this.comparator(b, a);
      if (compareResult === 0) {
        return data.indexOf(m1) - data.indexOf(m2);
      }
      return compareResult;
    });
  }

  public comparator(a: string | number, b: string | number): number {
    if ((a === undefined || a === null || a === 'NaN') && (b === undefined || b === null || b === 'NaN')) {
      return 0;
    }
    if (a === undefined || a === null || a === 'NaN') {
      return -1;
    }
    if (b === undefined || b === null || b === 'NaN') {
      return 1;
    }
    if (isNumber(a) && isNumber(b)) {
      return a - b;
    }
    if (isString(a) && isString(b)) {
      return a.localeCompare(b);
    }
    return 0;
  }

  // public sort2(data: PhenoMeasure[], orderBy: string, sortBy: string): void {
  //   data.forEach((measure, idx) => {
  //     measure['arrayPosition'] = idx;
  //   });
  //   data.sort((a, b) => {
  //     const compareResult = orderBy === 'asc' ? this.comparator(a, b, sortBy) : this.comparator(b, a, sortBy);
  //     if (compareResult === 0) {
  //       return a['arrayPosition'] - b['arrayPosition'];
  //     }
  //     return compareResult;
  //   });
  // }

  // public comparator(a: any, b: any, sortBy: string): number {
  //   let leftVal = a[sortBy];
  //   let rightVal = b[sortBy];

  //   if (leftVal === '-') {
  //     leftVal = null;
  //   }
  //   if (rightVal === '-') {
  //     rightVal = null;
  //   }
  //   if ((leftVal === undefined || leftVal === null) && (rightVal === undefined || rightVal === null)) {
  //     return 0;
  //   }
  //   if (leftVal === undefined || leftVal === null) {
  //     return -1;
  //   }
  //   if (rightVal === undefined || rightVal === null) {
  //     return 1;
  //   }

  //   if (!isNaN(leftVal) && !isNaN(rightVal)) {
  //     return Number(leftVal) - Number(rightVal);
  //   }
  //   return leftVal.localeCompare(rightVal);
  // }


  private resetSortButtons(): void {
    const sortButton = this.sortingButtonsComponents.find(
      sortingButtonsComponent => sortingButtonsComponent.id === this.sortBy
    );

    if (sortButton) {
      sortButton.resetSortState();
    }
  }

  @HostListener('window:resize', ['$event'])
  public onResize(): void {
    const screenWidth = window.innerWidth;
    const padding = 60;
    const scrollSize = 15;

    this.singleColumnWidth = `${(screenWidth - padding - scrollSize) / this.columnsCount}px`;
  }

  public openModal(imageUrl: string): void {
    if (imageUrl) {
      const modalRef = this.modalService.open(PhenoBrowserModalContentComponent, {
        windowClass: 'modal-fullscreen'
      });
      (modalRef.componentInstance as PhenoBrowserModalContentComponent).imageUrl = imageUrl;
    }
  }
}
