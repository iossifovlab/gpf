import { Component, OnInit, Input, forwardRef, ViewChild, Output, EventEmitter } from '@angular/core';

import { Subscription } from 'rxjs';

import { MeasuresService } from '../measures/measures.service';
import { ContinuousMeasure } from '../measures/measures';
import { DatasetsService } from '../datasets/datasets.service';

@Component({
  selector: 'gpf-pheno-measure-selector',
  templateUrl: './pheno-measure-selector.component.html',
  styleUrls: ['./pheno-measure-selector.component.css']
})
export class PhenoMeasureSelectorComponent implements OnInit {
  @ViewChild('searchBox') searchBox: any;

  measures: Array<ContinuousMeasure>;
  filteredMeasures: Array<ContinuousMeasure>;
  internalSelectedMeasure: ContinuousMeasure;
  searchString: string;

  @Input() initialSelectedMeasure: string;

  @Output() selectedMeasureChange = new EventEmitter(true);
  @Output() measuresChange = new EventEmitter(true);
  @Output() clearEvent = new EventEmitter(true);
  @Output() focusEvent = new EventEmitter(true);
  private subscription: Subscription;

  constructor(
    private measuresService: MeasuresService,
    private datasetsService: DatasetsService
  ) { }

  public ngOnInit() {
    const datasetId = this.datasetsService.getSelectedDataset().id;
    this.measuresService.getContinuousMeasures(datasetId).subscribe(measures => {
      this.measures = measures;
      let search = this.initialSelectedMeasure;
      if (this.initialSelectedMeasure) {
        this.selectedMeasure = this.measures
          .find(m => m.name === this.initialSelectedMeasure);
      }
      if (!this.selectedMeasure) {
        search = '';
      }
      this.searchBoxChange(search);
      this.measuresChange.emit(this.measures);
    });
  }

  @Input()
  set selectedMeasure(measure) {
    this.internalSelectedMeasure = measure;
    this.selectedMeasureChange.emit(measure);
  }

  get selectedMeasure(): ContinuousMeasure {
    return this.internalSelectedMeasure;
  }

  clear() {
    this.selectedMeasure = null;
    (<HTMLInputElement>document.getElementById('search-box')).value = '';
    this.searchBoxChange('');
    this.clearEvent.emit(true);
  }

  onFocus() {
    this.focusEvent.emit(true);
  }

  searchBoxChange(searchFieldValue) {
    this.searchString = searchFieldValue;

    if(this.measures !== undefined) {
      this.filteredMeasures = this.measures
        .filter(value => {
          return value.name.toLowerCase().indexOf(searchFieldValue.toLowerCase()) !== -1;
        });
    }
  }
}
