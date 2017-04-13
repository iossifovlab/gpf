import { Component, OnInit, Input, forwardRef, ViewChild, Output, EventEmitter } from '@angular/core';
import { MeasuresService } from '../measures/measures.service'
import { ContinuousMeasure } from '../measures/measures'

@Component({
  selector: 'gpf-pheno-measure-selector',
  templateUrl: './pheno-measure-selector.component.html',
  styleUrls: ['./pheno-measure-selector.component.css']
})
export class PhenoMeasureSelectorComponent implements OnInit {
  @Input() datasetId: string;
  @ViewChild("inputGroup") inputGroupSpan: any;
  @ViewChild("searchBox") searchBox: any;

  measures: Array<ContinuousMeasure>;
  filteredMeasures: Array<ContinuousMeasure>;
  internalSelectedMeasure: ContinuousMeasure;
  searchString: string;

  @Output() selectedMeasureChange = new EventEmitter();
  @Output() measuresChange = new EventEmitter();

  constructor(
    private measuresService: MeasuresService
  ) { }

  ngOnInit() {

    this.measuresService.getContinuousMeasures(this.datasetId).subscribe(
      (measures) => {
        this.measures = measures;
        this.searchBoxChange('');
        this.measuresChange.emit(this.measures);
      }
    )
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
    this.inputGroupSpan.nativeElement.classList.add("show");
    this.selectedMeasure = null;
  }

  searchBoxChange(searchFieldValue) {
    this.searchString = searchFieldValue;

    this.filteredMeasures = this.measures.filter(
      (value) => {
        return ~value.name.indexOf(searchFieldValue);
      }
    )
  }

}
