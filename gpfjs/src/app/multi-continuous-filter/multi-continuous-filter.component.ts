import { Component, OnInit, Input } from '@angular/core';
import { MeasuresService } from '../measures/measures.service'
import { ContinuousMeasure } from '../measures/measures'

@Component({
  selector: 'gpf-multi-continuous-filter',
  templateUrl: './multi-continuous-filter.component.html',
  styleUrls: ['./multi-continuous-filter.component.css']
})
export class MultiContinuousFilterComponent implements OnInit {
  @Input() name: string;
  @Input() datasetId: string;

  measures: Array<ContinuousMeasure>;
  selectedMeasure: ContinuousMeasure;

  constructor(
    private measuresService: MeasuresService
  ) { }

  ngOnInit() {
    this.measuresService.getContinuousMeasures(this.datasetId).subscribe(
      (measures) => {
        this.measures = measures;
      }
    )
  }

}
