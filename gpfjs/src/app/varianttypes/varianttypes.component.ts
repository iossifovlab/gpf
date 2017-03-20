import { DatasetsState } from '../datasets/datasets';
import {
  VariantTypesState, VARIANT_TYPES_INIT,
  VARIANT_TYPES_CHECK_ALL, VARIANT_TYPES_UNCHECK_ALL,
  VARIANT_TYPES_UNCHECK, VARIANT_TYPES_CHECK
} from './varianttypes';
import { Component, OnInit, forwardRef } from '@angular/core';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { QueryStateProvider } from '../query/query-state-provider'
import { QueryData } from '../query/query'
import { toObservableWithValidation, validationErrorsToStringArray } from '../utils/to-observable-with-validation'
import { ValidationError } from "class-validator";

@Component({
  selector: 'gpf-varianttypes',
  templateUrl: './varianttypes.component.html',
  styleUrls: ['./varianttypes.component.css'],
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => VarianttypesComponent) }]
})
export class VarianttypesComponent implements OnInit {
  sub: boolean = true;
  ins: boolean = true;
  del: boolean = true;
  CNV: boolean = true;

  variantTypesState: Observable<[VariantTypesState, boolean, ValidationError[]]>;
  hasCNV: Observable<boolean>;

  private errors: string[];
  private flashingAlert = false;

  constructor(
    private store: Store<any>
  ) {

    this.variantTypesState = toObservableWithValidation(VariantTypesState, this.store.select('variantTypes'));

    let datasetsState: Observable<DatasetsState> = this.store.select('datasets');
    this.hasCNV = datasetsState.map(state => {
      if (!state || !state.selectedDataset) {
        return false;
      }
      return state.selectedDataset.genotypeBrowser.hasCNV;
    });

  }

  ngOnInit() {
    this.store.dispatch({
      'type': VARIANT_TYPES_INIT,
    });

    this.variantTypesState.subscribe(
      ([variantTypesState, isValid, validationErrors]) => {
        this.errors = validationErrorsToStringArray(validationErrors);

        this.sub = variantTypesState.sub;
        this.ins = variantTypesState.ins;
        this.del = variantTypesState.del;
        this.CNV = variantTypesState.CNV;
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

  getState() {
    return this.variantTypesState.take(1).map(
      ([variantTypes, isValid, validationErrors]) => {
        if (!isValid) {
          this.flashingAlert = true;
          setTimeout(()=>{ this.flashingAlert = false }, 1000)

          throw "invalid state"
        }
        return { variantTypes: QueryData.trueFalseToStringArray(variantTypes) }
    });
  }
}
