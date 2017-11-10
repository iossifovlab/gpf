import { GeneSymbols } from './gene-symbols';
import { Component, OnInit, forwardRef } from '@angular/core';

import { Observable } from 'rxjs';
import { toValidationObservable, validationErrorsToStringArray } from '../utils/to-observable-with-validation';
import { ValidationError } from 'class-validator';
import { QueryStateProvider } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';

@Component({
  selector: 'gpf-gene-symbols',
  templateUrl: './gene-symbols.component.html',
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => GeneSymbolsComponent) }]
})
export class GeneSymbolsComponent extends QueryStateProvider implements OnInit {
  private geneSymbols = new GeneSymbols();
  errors: string[];

  private flashingAlert = false;

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  ngOnInit() {
    this.stateRestoreService.getState(this.constructor.name).subscribe(
      (state) => {
        if (state['geneSymbols']) {
          this.geneSymbols.geneSymbols = state['geneSymbols'].join('\n');
        }
      });
  }


  getState() {
    return toValidationObservable(this.geneSymbols)
      .map(state => {
        let result = state.geneSymbols
          .split(/[,\s]/)
          .filter(s => s !== '')
          .map(s => s.toUpperCase());
        if (result.length === 0) {
          return {};
        }

        return { geneSymbols: result };
      })
      .catch(errors => {
        this.flashingAlert = true;
        setTimeout(() => { this.flashingAlert = false; }, 1000);

        return Observable.throw(`${this.constructor.name}: invalid state`);
      });
  }
}
