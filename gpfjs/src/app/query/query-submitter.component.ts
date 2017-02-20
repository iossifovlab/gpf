import { Component, Output, EventEmitter } from '@angular/core';
import { Store } from '@ngrx/store';
import { QueryData } from './query';
import { QueryService } from './query.service';
import { GenotypePreview, GenotypePreviewsArray } from '../genotype-preview-table/genotype-preview';

@Component({
  selector: 'gpf-query-submitter',
  templateUrl: './query-submitter.component.html'
})
export class QuerySubmitterComponent {
  @Output() genotypePreviewsArrayChange = new EventEmitter();

  constructor(
    private store: Store<any>,
    private queryService: QueryService
  ) { }


  submitQuery() {
    this.store.take(1).subscribe(s => this.prepareQuery(s));
  }

  prepareQuery(state: any) {
    let queryData = new QueryData();
    let arrayToCommaSeparatedReduce = (acc, x, idx, source) => {
      return acc + ',' + x;
    };
    let trueFalseToCommaSeparated = (obj) => {
      let values = Array<string>();
      for (let key of Object.keys(obj)) {
        if (obj[key]) {
          values.push(key);
        }
      }
      return values;
    };

    queryData.datasetId = state.datasets.selectedDataset.id;
    queryData.effectTypes = state.effectTypes;
    queryData.gender = trueFalseToCommaSeparated(state.gender);
    queryData.variantTypes = trueFalseToCommaSeparated(state.variantTypes);
    queryData.presentInChild = state.presentInChild;

    queryData.pedigreeSelector = {
      id: state.pedigreeSelector.pedigree.id,
      checkedValues: state.pedigreeSelector.checkedValues
    };

    this.queryService.getGenotypePreviewByFilter(queryData).subscribe(
      (genotypePreviewsArray) => {
        this.genotypePreviewsArrayChange.emit(genotypePreviewsArray);
      });
  }
}
