import {
  GeneSymbolsState, GENE_SYMBOLS_CHANGE
} from './gene-symbols';
import { Component, OnInit } from '@angular/core';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';

@Component({
  selector: 'gpf-gene-symbols',
  templateUrl: './gene-symbols.component.html',
})
export class GeneSymbolsComponent implements OnInit {
  geneSymbolsInternal: string;

  geneSymbolsState: Observable<GeneSymbolsState>;

  constructor(
    private store: Store<any>
  ) {

    this.geneSymbolsState = this.store.select('geneSymbols');
  }

  ngOnInit() {
    this.geneSymbolsState.subscribe(
      geneSymbolsState => {
        this.geneSymbolsInternal = geneSymbolsState.geneSymbols;
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
