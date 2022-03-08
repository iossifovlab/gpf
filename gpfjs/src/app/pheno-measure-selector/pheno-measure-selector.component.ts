import { Component, OnChanges, Input, ViewChild, Output, EventEmitter } from '@angular/core';

import { MeasuresService } from '../measures/measures.service';
import { ContinuousMeasure } from '../measures/measures';
import { first } from 'rxjs/operators';
import { NgbDropdown } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'gpf-pheno-measure-selector',
  templateUrl: './pheno-measure-selector.component.html',
  styleUrls: ['./pheno-measure-selector.component.css']
})
export class PhenoMeasureSelectorComponent implements OnChanges {

  @Input() datasetId: string;
  @Output() selectedMeasureChange = new EventEmitter(true);
  @Output() measuresChange = new EventEmitter(true);

  @ViewChild('searchBox') searchBox: any;
  @ViewChild(NgbDropdown) private dropdown: NgbDropdown;

  public measures: Array<ContinuousMeasure> = [];
  public filteredMeasures: Array<ContinuousMeasure> = [];
  public searchString: string = '';
  public selectedMeasure: ContinuousMeasure;

  constructor(
    private measuresService: MeasuresService
  ) { }

  public ngOnChanges() {
    if (this.datasetId && this.measures.length === 0) {
      this.measuresService.getContinuousMeasures(this.datasetId).pipe(first()).subscribe(measures => {
        this.measures = measures;
        this.measuresChange.emit(this.measures);
      });
    }
  }

  selectMeasure(measure: ContinuousMeasure, sendEvent: boolean = true) {
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

  clear() {
    this.selectMeasure(null);
    this.searchBoxChange();
  }

  searchBoxChange() {
    if (this.searchString.length) {
      this.filteredMeasures = this.measures.filter(value => {
        return value.name.toLowerCase().indexOf(this.searchString.toLowerCase()) !== -1;
      });
    } else {
      this.filteredMeasures = this.measures;
    }
    this.filteredMeasures = this.filteredMeasures.slice(0, 25);
  }
}
