import { GeneSymbols } from './gene-symbols';
import { Component, OnInit, forwardRef } from '@angular/core';

import { Observable } from 'rxjs';
import { toValidationObservable, validationErrorsToStringArray } from '../utils/to-observable-with-validation';
import { ValidationError } from 'class-validator';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';

@Component({
  selector: 'gpf-gene-symbols',
  templateUrl: './gene-symbols.component.html',
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => GeneSymbolsComponent) }]
})
export class GeneSymbolsComponent extends QueryStateWithErrorsProvider implements OnInit {
  geneSymbols = new GeneSymbols();

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  ngOnInit() {
    this.stateRestoreService.getState(this.constructor.name)
      .take(1)
      .subscribe(state => {
        if (state['geneSymbols']) {
          this.geneSymbols.geneSymbols = state['geneSymbols'].join('\n');
        }
      });
  }


  getState() {
    return this.validateAndGetState(this.geneSymbols)
      .map(state => {
        let result = state.geneSymbols
          .split(/[,\s]/)
          .filter(s => s !== '')
          .map(s => s.toUpperCase());
        if (result.length === 0) {
          return {};
        }

        return { geneSymbols: result };
      });
  }
}
