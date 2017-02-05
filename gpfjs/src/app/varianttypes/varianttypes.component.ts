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

  variantTypesState: Observable<VariantTypesState>;

  constructor(
    private store: Store<any>
  ) {

    this.variantTypesState = this.store.select('variantTypes');
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
