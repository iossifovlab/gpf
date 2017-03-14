import {
  GeneSymbolsState, GENE_SYMBOLS_CHANGE, GENE_SYMBOLS_INIT
} from './gene-symbols';
import { Component, OnInit } from '@angular/core';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { toObservableWithValidation, validationErrorsToStringArray } from '../utils/to-observable-with-validation'
import { ValidationError } from "class-validator";

@Component({
  selector: 'gpf-gene-symbols',
  templateUrl: './gene-symbols.component.html',
})
export class GeneSymbolsComponent implements OnInit {
  geneSymbolsInternal: string;
  errors: string[];
  geneSymbolsState: Observable<[GeneSymbolsState, boolean, ValidationError[]]>;

  constructor(
    private store: Store<any>
  ) {

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

}
