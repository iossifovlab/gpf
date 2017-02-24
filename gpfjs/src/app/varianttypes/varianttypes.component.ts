import { DatasetsState } from '../datasets/datasets';
import {
  VariantTypesState,
  VARIANT_TYPES_CHECK_ALL, VARIANT_TYPES_UNCHECK_ALL,
  VARIANT_TYPES_UNCHECK, VARIANT_TYPES_CHECK
} from './varianttypes';
import { Component, OnInit } from '@angular/core';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';


@Component({
  selector: 'gpf-varianttypes',
  templateUrl: './varianttypes.component.html',
  styleUrls: ['./varianttypes.component.css']
})
export class VarianttypesComponent implements OnInit {
  sub: boolean = true;
  ins: boolean = true;
  del: boolean = true;
  cnv: boolean = true;

  variantTypesState: Observable<VariantTypesState>;
  hasCNV: Observable<boolean>;

  constructor(
    private store: Store<any>
  ) {

    this.variantTypesState = this.store.select('variantTypes');

    let datasetsState: Observable<DatasetsState> = this.store.select('datasets');
    this.hasCNV = datasetsState.map(state => {
      if (!state || !state.selectedDataset) {
        return false;
      }
      return state.selectedDataset.genotypeBrowser.hasCNV;
    });

  }

  ngOnInit() {
    this.variantTypesState.subscribe(
      variantTypesState => {
        this.sub = variantTypesState.sub;
        this.ins = variantTypesState.ins;
        this.del = variantTypesState.del;
      }
    );
  }

  selectAll(): void {
    this.store.dispatch({
      'type': VARIANT_TYPES_CHECK_ALL,
    });
  }

  selectNone(): void {
    this.store.dispatch({
      'type': VARIANT_TYPES_UNCHECK_ALL,
    });
  }

  variantTypesCheckValue(variantType: string, value: boolean): void {
    if (variantType === 'sub' || variantType === 'ins' || variantType === 'del') {
      this.store.dispatch({
        'type': value ? VARIANT_TYPES_CHECK : VARIANT_TYPES_UNCHECK,
        'payload': variantType
      });
    }
  }
}
