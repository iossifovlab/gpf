import { Component, AfterViewInit, Input, Output, EventEmitter } from '@angular/core';
import { DatasetsService } from 'app/datasets/datasets.service';
import { MeasuresService } from '../measures/measures.service';
import { ContinuousMeasure } from '../measures/measures';
import { first } from 'rxjs/operators';

@Component({
  selector: 'gpf-pheno-measure-selector',
  templateUrl: './pheno-measure-selector.component.html',
  styleUrls: ['./pheno-measure-selector.component.css']
})
export class PhenoMeasureSelectorComponent implements AfterViewInit {
  @Input() public datasetId: string;
  @Output() public selectedMeasureChange = new EventEmitter(true);
  @Output() public measuresChange = new EventEmitter(true);

  public measures: Array<ContinuousMeasure> = [];
  public filteredMeasures: Array<ContinuousMeasure> = [];
  public searchString = '';
  public selectedMeasure: ContinuousMeasure;
  public loadingMeasures = false;
  public loadingDropdown = false;

  public constructor(
    private measuresService: MeasuresService,
    private datasetsService: DatasetsService,
  ) { }

  public ngAfterViewInit(): void {
    this.loadingMeasures = true;
    const datasetId = this.datasetsService.getSelectedDataset().id;
    const self = this;
    this.measuresService.getContinuousMeasures(datasetId).pipe(first()).subscribe(measures => {
      this.measures = measures;
      this.measuresChange.emit(this.measures);
      this.loadingMeasures = false;
      const dropdown = $('#tags') as any;
      dropdown.autocomplete({
        minLength: 0,
        delay: 0,
        source: this.measures.map(measure => measure.name),
        select: function(event, ui) { 
          self.measures.forEach(element => {
            if(element.name === ui.item.value) {
              self.selectMeasure(element);
            }
          });
          dropdown.trigger('blur');
        },
      }).bind('focus', () => {
        dropdown.val('');
        dropdown.autocomplete('search');
        self.selectMeasure(null);
      });
    });
  }

  public selectMeasure(measure: ContinuousMeasure, sendEvent: boolean = true): void {
    this.selectedMeasure = measure;
    this.searchString = measure ? measure.name : '';
    if (sendEvent) {
      this.selectedMeasureChange.emit(measure);
    }
  }
}
