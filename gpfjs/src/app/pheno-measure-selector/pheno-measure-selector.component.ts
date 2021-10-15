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
  @ViewChild('inputGroup') inputGroupSpan: any;
  @ViewChild('searchBox') searchBox: any;

  measures: Array<ContinuousMeasure>;
  filteredMeasures: Array<ContinuousMeasure>;
  internalSelectedMeasure: ContinuousMeasure;
  searchString: string;

  @Input() initialSelectedMeasure: string;

  @Output() selectedMeasureChange = new EventEmitter(true);
  @Output() measuresChange = new EventEmitter(true);
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
    this.selectedMeasure = {} as ContinuousMeasure;
    (<HTMLInputElement>document.getElementById('search-box')).value = '';
    this.searchBoxChange('');
  }

  onFocus(event) {
    event.stopPropagation();
    this.inputGroupSpan.nativeElement.classList.add('show');
    this.selectedMeasure = null;
  }

  searchBoxChange(searchFieldValue) {
    this.searchString = searchFieldValue;

    this.filteredMeasures = this.measures
      .filter(value => {
        return value.name.toLowerCase().indexOf(searchFieldValue.toLowerCase()) !== -1;
      });
  }
}
