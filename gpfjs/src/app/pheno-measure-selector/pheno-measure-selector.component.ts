import { Component, OnInit, OnDestroy, Input, forwardRef, ViewChild, Output, EventEmitter } from '@angular/core';

import { Subscription } from 'rxjs';

import { MeasuresService } from '../measures/measures.service';
import { ContinuousMeasure } from '../measures/measures';
import { DatasetsService } from '../datasets/datasets.service';

@Component({
  selector: 'gpf-pheno-measure-selector',
  templateUrl: './pheno-measure-selector.component.html',
  styleUrls: ['./pheno-measure-selector.component.css']
})
export class PhenoMeasureSelectorComponent implements OnInit, OnDestroy {
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

  ngOnInit() {
    this.subscription = this.datasetsService.getSelectedDataset()
      .subscribe(dataset => {
        this.measuresService.getContinuousMeasures(dataset.id)
          .subscribe(measures => {
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
      });
  }

  ngOnDestroy() {
    if (this.subscription) {
      this.subscription.unsubscribe();
      this.subscription = null;
    }
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
    this.searchBox.nativeElement.value = '';
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
