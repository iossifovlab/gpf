import {
  Component, OnChanges, Input, Output,
  EventEmitter, ElementRef, ViewChild,
  HostListener
} from '@angular/core';
import { MeasuresService } from '../measures/measures.service';
import { ContinuousMeasure } from '../measures/measures';
import { first } from 'rxjs/operators';
import { CdkVirtualScrollViewport } from '@angular/cdk/scrolling';

@Component({
  selector: 'gpf-pheno-measure-selector',
  templateUrl: './pheno-measure-selector.component.html',
  styleUrls: ['./pheno-measure-selector.component.css']
})
export class PhenoMeasureSelectorComponent implements OnChanges {
  @Input() public datasetId: string;
  @Output() public selectedMeasureChange = new EventEmitter(true);
  @Output() public measuresChange = new EventEmitter(true);

  @ViewChild('measuresSearchBox') private searchBox: ElementRef;
  @ViewChild(CdkVirtualScrollViewport) private viewport: CdkVirtualScrollViewport;

  public measures: Array<ContinuousMeasure> = [];
  public filteredMeasures: Array<ContinuousMeasure> = [];
  public searchString = '';
  public selectedMeasure: ContinuousMeasure = null;
  public loadingMeasures = false;
  public loadingDropdown = false;
  public isSelected = false;
  public showDropdown = false;

  public topVisibleIdx = 0;
  public selectedIdx = -1;
  public idxSubscription = null;

  public constructor(
    private measuresService: MeasuresService,
  ) { }

  public ngOnChanges(): void {
    if (this.datasetId && this.measures.length === 0) {
      this.loadingMeasures = true;
      this.measuresService.getContinuousMeasures(this.datasetId).pipe(first()).subscribe(measures => {
        this.measures = measures;
        this.filterData();
        this.measuresChange.emit(this.measures);
        this.loadingMeasures = false;
      });
    }
  }

  @HostListener('window:keydown.tab', ['$event'])
  public handleTabKey(event): void {
    if (!this.showDropdown) {
      return;
    }
    event.preventDefault();
    if (event.code !== 'Tab') {
      return;
    }
    if (event.shiftKey) {
      this.prevItem();
    } else {
      this.nextItem();
    }
  }

  public selectMeasure(measure: ContinuousMeasure, sendEvent: boolean = true): void {
    this.selectedMeasure = measure;
    this.searchString = measure ? measure.name : '';
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
    if (this.selectedIdx < this.topVisibleIdx) {
      this.viewport.scrollToIndex(this.topVisibleIdx - 1);
    }
  }

  public nextItem(): void {
    if (this.idxSubscription === null) {
      this.initIdxSubscription();
    }

    if (this.selectedIdx + 1 < this.filteredMeasures.length) {
      this.selectedIdx += 1;
    }
    if (this.selectedIdx >= this.topVisibleIdx + 7) {
      this.viewport.scrollToIndex(this.topVisibleIdx + 1);
    }
  }

  public closeDropdown(): void {
    this.showDropdown = false;
    (this.searchBox.nativeElement as HTMLInputElement).blur();
  }

  public clear(): void {
    if (this.selectedMeasure === null) {
      return;
    }
    this.selectMeasure(null);
    this.isSelected = false;
    this.loadDropdownData();
  }

  public loadDropdownData($event = null): void {
    if ($event && ($event.key === 'ArrowUp' || $event.key === 'ArrowDown')) {
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
    this.selectedIdx = -1;
    this.topVisibleIdx = 0;
    this.viewport?.scrollToIndex(0);
    this.filteredMeasures = this.measures;
    if (this.searchString.length) {
      this.filteredMeasures = this.filteredMeasures.filter(measure =>
        measure.name.toLowerCase().indexOf(this.searchString.toLowerCase()) !== -1
      );
    }
  }
}
