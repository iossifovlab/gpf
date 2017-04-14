import { Component, OnInit, Input, forwardRef } from '@angular/core';
import { ContinuousMeasure } from '../measures/measures'
import { QueryStateProvider } from '../query/query-state-provider'
import { Observable }        from 'rxjs/Observable';

@Component({
  selector: 'gpf-pheno-tool-measure',
  templateUrl: './pheno-tool-measure.component.html',
  styleUrls: ['./pheno-tool-measure.component.css'],
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => PhenoToolMeasureComponent) }]
})
export class PhenoToolMeasureComponent extends QueryStateProvider implements OnInit {
  @Input() datasetId: string;

  internalSelectedMeasure: ContinuousMeasure;

  constructor() {
    super();
  }

  ngOnInit() {
  }

  set selectedMeasure(measure) {
    this.internalSelectedMeasure = measure;
    // this.store.dispatch({
    //   'type': PHENO_FILTERS_CHANGE_CONTINUOUS_MEASURE,
    //   'payload': {
    //     'id': this.continuousFilterConfig.name,
    //     'measure': measure  ? measure.name : null,
    //     'domainMin': measure ? measure.min : 0,
    //     'domainMax': measure ? measure.max : 0
    //   }
    // });
  }

  get selectedMeasure(): ContinuousMeasure {
    return this.internalSelectedMeasure;
  }

  getState() {
    return Observable.of({
      measureId: this.internalSelectedMeasure.name
    })
  }

}
