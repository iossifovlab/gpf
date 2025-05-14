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
  @Input() public measuresLoading: boolean;
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
    this.onResize();
  }

  public sort(sortBy: string, orderBy: string): void {
    if (this.sortBy !== sortBy) {
      this.resetCurrentSortButton();
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
        const regId = sortBy.split('.')[0];
        a = m1.regressions.getReg(regId).pvalueRegressionMale;
        b = m2.regressions.getReg(regId).pvalueRegressionMale;
      } else if (sortBy.includes('pvalueRegressionFemale')) {
        const regId = sortBy.split('.')[0];
        a = m1.regressions.getReg(regId).pvalueRegressionFemale;
        b = m2.regressions.getReg(regId).pvalueRegressionFemale;
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

  private comparator(a: string | number, b: string | number): number {
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

  private resetCurrentSortButton(): void {
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
