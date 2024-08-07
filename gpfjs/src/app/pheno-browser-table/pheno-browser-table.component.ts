import {
  OnInit,
  Component,
  HostListener,
  Input,
  ViewChildren,
  Output,
  EventEmitter,
  ChangeDetectionStrategy
} from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import {
  PhenoBrowserModalContentComponent
} from '../pheno-browser-modal-content/pheno-browser-modal-content.component';
import { PhenoMeasures } from '../pheno-browser/pheno-browser';
import { SortingButtonsComponent } from 'app/sorting-buttons/sorting-buttons.component';

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
  @Output() public sortEvent = new EventEmitter<{id: string; order: string}>();


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

    this.sortEvent.emit({ id: this.sortBy, order: this.orderBy });
  }


  private resetSortButtons(): void {
    const sortButton = this.sortingButtonsComponents.find(
      sortingButtonsComponent => sortingButtonsComponent.id === this.sortBy
    );

    if (sortButton) {
      sortButton.resetSortState();
    }
  }

  public compare(leftVal: any, rightVal: any): number {
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
      modalRef.componentInstance.imageUrl = imageUrl;
    }
  }
}
