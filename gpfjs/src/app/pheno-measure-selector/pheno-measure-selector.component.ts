import { Component, OnChanges, Input, ViewChild, Output, EventEmitter,
  ElementRef } from '@angular/core';

import { MeasuresService } from '../measures/measures.service';
import { ContinuousMeasure } from '../measures/measures';
import { first } from 'rxjs/operators';
import { MatAutocompleteTrigger } from '@angular/material/autocomplete';

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
  @ViewChild('triggeMeasuresDropdown') private dropdownTrigger: MatAutocompleteTrigger;

  public measures: Array<ContinuousMeasure> = [];
  public filteredMeasures: Array<ContinuousMeasure> = [];
  public searchString = '';
  public selectedMeasure: ContinuousMeasure;
  public loadingMeasures = false;
  public loadingDropdown = false;
  public isSelected = false;

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

  public selectMeasure(measure: ContinuousMeasure, sendEvent: boolean = true): void {
    this.selectedMeasure = measure;
    this.searchString = measure ? measure.name : '';
    if (measure) {
      this.dropdownTrigger.closePanel();
      (this.searchBox.nativeElement as HTMLInputElement).blur();
    }

    if (sendEvent) {
      this.selectedMeasureChange.emit(measure);
    }
  }

  public clear(): void {
    this.selectMeasure(null);
    this.isSelected = false;
    this.loadDropdownData();
  }

  public loadDropdownData(): void {
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
    this.filteredMeasures = this.measures;
    if (this.searchString.length) {
      this.filteredMeasures = this.filteredMeasures.filter(measure =>
        measure.name.toLowerCase().indexOf(this.searchString.toLowerCase()) !== -1
      );
    }
  }
}
