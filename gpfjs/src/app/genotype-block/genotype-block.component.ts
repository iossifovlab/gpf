import { DatasetsState } from '../dataset/dataset';
import { Component, OnInit } from '@angular/core';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';

@Component({
  selector: 'gpf-genotype-block',
  templateUrl: './genotype-block.component.html',
  styleUrls: ['./genotype-block.component.css']
})
export class GenotypeBlockComponent implements OnInit {
  hasCNV: Observable<boolean>;

  constructor(
    private store: Store<any>
  ) {

    let datasetsState: Observable<DatasetsState> = this.store.select('datasets');
    this.hasCNV = datasetsState.map(state => {
      if (!state || !state.selectedDataset) {
        return false;
      }
      return state.selectedDataset.genotypeBrowser.hasCNV;
    });
  }

  ngOnInit() {
  }

}
