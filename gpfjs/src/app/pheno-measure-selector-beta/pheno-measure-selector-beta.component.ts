import {
  Component, OnChanges, Input, Output,
  EventEmitter, ElementRef, ViewChild,
  HostListener
} from '@angular/core';
import { MeasuresService } from '../measures/measures.service';
import { Measure } from '../measures/measures';
import { first } from 'rxjs/operators';
import { CdkVirtualScrollViewport } from '@angular/cdk/scrolling';
import { Subscription } from 'rxjs';

@Component({
  selector: 'gpf-pheno-measure-selector-beta',
  templateUrl: './pheno-measure-selector-beta.component.html',
  styleUrls: ['./pheno-measure-selector-beta.component.css']
})
export class PhenoMeasureSelectorBetaComponent implements OnChanges {
  @Input() public datasetId: string;
  @Output() public selectedMeasureChange = new EventEmitter(true);
  @Output() public measuresChange = new EventEmitter(true);

  @ViewChild('measuresSearchBox') private searchBox: ElementRef;
  @ViewChild(CdkVirtualScrollViewport) private viewport: CdkVirtualScrollViewport;

  public measures: Array<Measure> = [];
  public filteredMeasures: Array<Measure> = [];
  public searchString = '';
  public selectedMeasure: Measure = null;
  public loadingMeasures = false;
  public loadingDropdown = false;
  public showDropdown = false;

  public topVisibleIdx = 0;
  public selectedIdx = -1;
  public idxSubscription: Subscription = null;

  public constructor(
    private measuresService: MeasuresService,
  ) { }

  public ngOnChanges(): void {
    if (this.datasetId && this.measures.length === 0) {
      this.loadingMeasures = true;
      this.measuresService.getMeasureList(this.datasetId).pipe(first()).subscribe(measures => {
        this.measures = measures;
        this.filterData();
        this.measuresChange.emit(this.measures);
        this.loadingMeasures = false;
      });
    }
  }

  @HostListener('window:keydown', ['$event'])
  public handleTabKey(event: KeyboardEvent): void {
    if (!this.showDropdown || event.code !== 'Tab') {
      return;
    }
    event.preventDefault();
    if (event.shiftKey) {
      this.prevItem();
    } else {
      this.nextItem();
    }
  }

  public selectMeasure(measure: Measure, sendEvent: boolean = true): void {
    this.selectedMeasure = measure;
    this.searchString = measure ? measure.id : '';
    if (sendEvent) {
      this.selectedMeasureChange.emit(measure);
    }
  }

  private initIdxSubscription(): void {
    this.idxSubscription = this.viewport.scrolledIndexChange.subscribe((idx) => {
      this.topVisibleIdx = idx;
    });
  }

  public prevItem(): void {
    if (this.idxSubscription === null) {
      this.initIdxSubscription();
    }

    if (this.selectedIdx > 0) {
      this.selectedIdx -= 1;
    }
    this.recenterVirtualScroll();
  }

  public nextItem(): void {
    if (this.idxSubscription === null) {
      this.initIdxSubscription();
    }

    if (this.selectedIdx + 1 < this.filteredMeasures.length) {
      this.selectedIdx += 1;
    }
    this.recenterVirtualScroll();
  }

  private recenterVirtualScroll(): void {
    if (this.selectedIdx < this.topVisibleIdx) {
      this.viewport.scrollToIndex(this.selectedIdx);
    }
    if (this.selectedIdx >= this.topVisibleIdx + 8) {
      this.viewport.scrollToIndex(this.selectedIdx - 7);
    }
  }

  public closeDropdown(): void {
    this.idxSubscription?.unsubscribe();
    this.idxSubscription = null;
    this.resetScroll();
    this.showDropdown = false;
    (this.searchBox.nativeElement as HTMLInputElement).blur();
  }

  public clear(): void {
    if (this.selectedMeasure === null) {
      return;
    }
    this.selectMeasure(null);
    this.resetScroll();
    this.loadDropdownData();
  }

  private resetScroll(): void {
    this.selectedIdx = -1;
    this.topVisibleIdx = 0;
    this.viewport?.scrollToIndex(0);
  }

  public onClearButtonClick(): void {
    this.searchString = '';
    this.selectMeasure(null);
    this.loadDropdownData();
  }

  public loadDropdownData($event: KeyboardEvent = null): void {
    if ($event && ($event.key === 'ArrowUp'
                   || $event.key === 'ArrowDown'
                   || $event.key === 'ArrowLeft'
                   || $event.key === 'ArrowRight'
                   || $event.key === 'Home'
                   || $event.key === 'End'
                   || $event.key === 'Tab'
                   || $event.key === 'Shift')) {
      return;
    }

    if (!this.loadingMeasures) {
      this.filterData();
    } else {
      this.loadingDropdown = true;
      const intervalId = setInterval(() => {
        if (!this.loadingMeasures) {
          this.filterData();
          this.loadingDropdown = false;
          clearInterval(intervalId);
        }
      }, 50);
    }
  }

  private filterData(): void {
    this.resetScroll();
    this.filteredMeasures = this.measures;
    if (this.searchString.length) {
      this.filteredMeasures = this.filteredMeasures.filter(measure =>
        measure.id.toLowerCase().indexOf(this.searchString.toLowerCase()) !== -1
      );
    }
  }
}
