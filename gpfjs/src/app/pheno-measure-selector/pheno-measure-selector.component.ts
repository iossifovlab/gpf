import { Component, OnChanges, Input, ViewChild, Output, EventEmitter } from '@angular/core';

import { MeasuresService } from '../measures/measures.service';
import { ContinuousMeasure } from '../measures/measures';
import { first } from 'rxjs/operators';
import { NgbDropdown } from '@ng-bootstrap/ng-bootstrap';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';

@Component({
  selector: 'gpf-pheno-measure-selector',
  templateUrl: './pheno-measure-selector.component.html',
  styleUrls: ['./pheno-measure-selector.component.css']
})
export class PhenoMeasureSelectorComponent implements OnChanges {
  @Input() public datasetId: string;
  @Output() public selectedMeasureChange = new EventEmitter(true);
  @Output() public measuresChange = new EventEmitter(true);

  @ViewChild('searchBox') private searchBox;
  @ViewChild(NgbDropdown) private dropdown: NgbDropdown;

  public measures: Array<ContinuousMeasure> = [];
  public filteredMeasures: Array<ContinuousMeasure> = [];
  public searchString = '';
  public selectedMeasure: ContinuousMeasure;

  public constructor(
    private measuresService: MeasuresService,
    private fullscreenLoadingService: FullscreenLoadingService
  ) { }

  public ngOnChanges(): void {
    if (this.datasetId && this.measures.length === 0) {
      this.fullscreenLoadingService.setLoadingStart();
      this.measuresService.getContinuousMeasures(this.datasetId).pipe(first()).subscribe(measures => {
        this.measures = measures;
        this.measuresChange.emit(this.measures);
        this.fullscreenLoadingService.setLoadingStop();
      });
    }
  }

  public selectMeasure(measure: ContinuousMeasure, sendEvent: boolean = true): void {
    this.selectedMeasure = measure;
    this.searchString = measure ? measure.name : '';
    if (sendEvent) {
      this.selectedMeasureChange.emit(measure);
    }
  }

  public openDropdown(): void {
    if (this.dropdown && !this.dropdown.isOpen()) {
      this.dropdown.open();
    }
  }

  public closeDropdown(): void {
    if (this.dropdown && this.dropdown.isOpen()) {
      this.dropdown.close();
      this.searchBox.nativeElement.blur();
    }
  }

  public clear(): void {
    this.selectMeasure(null);
    this.searchBoxChange();
  }

  public searchBoxChange(): void {
    if (this.searchString.length) {
      this.filteredMeasures = this.measures.filter(value =>
        value.name.toLowerCase().indexOf(this.searchString.toLowerCase()) !== -1
      );
    } else {
      this.filteredMeasures = this.measures;
    }
    this.filteredMeasures = this.filteredMeasures.slice(0, 25);
  }
}
