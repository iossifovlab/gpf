import {
  GeneSymbolsState, GENE_SYMBOLS_CHANGE, GENE_SYMBOLS_INIT
} from './gene-symbols';
import { Component, OnInit, forwardRef } from '@angular/core';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { toObservableWithValidation, validationErrorsToStringArray } from '../utils/to-observable-with-validation'
import { ValidationError } from "class-validator";
import { QueryStateProvider } from '../query/query-state-provider'

@Component({
  selector: 'gpf-gene-symbols',
  templateUrl: './gene-symbols.component.html',
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => GeneSymbolsComponent) }]
})
export class GeneSymbolsComponent extends QueryStateProvider implements OnInit {
  geneSymbolsInternal: string;
  errors: string[];
  geneSymbolsState: Observable<[GeneSymbolsState, boolean, ValidationError[]]>;

  constructor(
    private store: Store<any>
  ) {
    super();
    this.geneSymbolsState = toObservableWithValidation(GeneSymbolsState, this.store.select('geneSymbols'));
  }

  ngOnInit() {
    this.store.dispatch({
      'type': GENE_SYMBOLS_INIT,
    });

    this.geneSymbolsState.subscribe(
      ([geneSymbolsState, isValid, validationErrors]) => {
        if (geneSymbolsState) {
          this.errors = validationErrorsToStringArray(validationErrors);
          this.geneSymbolsInternal = geneSymbolsState.geneSymbols;
        }
      }
    );
  }

  set geneSymbols(geneSymbols: string) {
    this.store.dispatch({
      'type': GENE_SYMBOLS_CHANGE,
      'payload': geneSymbols
    });
  }

  get geneSymbols() {
    return this.geneSymbolsInternal;
  }

  getState() {
    return this.geneSymbolsState.take(1).map(
      ([geneSymbols, isValid, validationErrors]) => {
        if (!isValid) {
          throw "invalid state"
        }

        console.log(geneSymbols.geneSymbols)

        let result = geneSymbols.geneSymbols
          .split(/[,\s]/)
          .filter(s => s !== '')
          .map(s => s.toUpperCase());
        if (result.length === 0) {
          return {};
        }

        return { geneSymbols: result }
    });
  }

}
