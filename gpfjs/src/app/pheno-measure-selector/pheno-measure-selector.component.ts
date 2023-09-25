import { Component, AfterViewInit, Input, Output, EventEmitter, ViewChild, ElementRef } from '@angular/core';
import { DatasetsService } from 'app/datasets/datasets.service';
import { MeasuresService } from '../measures/measures.service';
import { ContinuousMeasure } from '../measures/measures';
import { first } from 'rxjs/operators';
import { JqueryUIElement } from 'typings';

@Component({
  selector: 'gpf-pheno-measure-selector',
  templateUrl: './pheno-measure-selector.component.html'
})
export class PhenoMeasureSelectorComponent implements AfterViewInit {
  @Input() public datasetId: string;
  @Output() public selectedMeasureChange = new EventEmitter(true);
  @Output() public measuresChange = new EventEmitter(true);
  @ViewChild('measureSelectorDropdown') public measureSelectorDropdownRef: ElementRef;

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
    this.measuresService.getContinuousMeasures(datasetId).pipe(first()).subscribe(measures => {
      this.measures = measures;
      this.measuresChange.emit(this.measures);
      this.loadingMeasures = false;
      this.fillDropdown();
    });
  }

  private fillDropdown(): void {
    const dropdown = $(this.measureSelectorDropdownRef.nativeElement) as unknown as JqueryUIElement;
    dropdown.autocomplete({
      minLength: 0,
      delay: 0,
      source: this.measures.map(measure => measure.name),
      select: (event, ui: {item: { value: string }}) => {
        this.measures.forEach(element => {
          if (element.name === ui.item.value) {
            this.selectMeasure(element);
          }
        });

        dropdown.trigger('blur');
        dropdown.attr('title', ui.item.value);
      },
    }).bind('focus', () => {
      dropdown.val('');
      dropdown.removeAttr('title');
      dropdown.autocomplete('search');
      this.selectMeasure(null);
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
