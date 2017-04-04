import { Component, OnInit, Input, forwardRef } from '@angular/core';
import { MeasuresService } from '../measures/measures.service'
import { ContinuousMeasure } from '../measures/measures'
import { QueryStateCollector } from '../query/query-state-provider'

@Component({
  selector: 'gpf-multi-continuous-filter',
  templateUrl: './multi-continuous-filter.component.html',
  styleUrls: ['./multi-continuous-filter.component.css'],
  providers: [{provide: QueryStateCollector, useExisting: forwardRef(() => MultiContinuousFilterComponent) }]
})
export class MultiContinuousFilterComponent extends QueryStateCollector implements OnInit {
  @Input() name: string;
  @Input() datasetId: string;

  measures: Array<ContinuousMeasure>;
  selectedMeasure: ContinuousMeasure;

  constructor(
    private measuresService: MeasuresService
  ) {
    super();
  }

  ngOnInit() {
    this.measuresService.getContinuousMeasures(this.datasetId).subscribe(
      (measures) => {
        this.measures = measures;
      }
    )
  }

}
