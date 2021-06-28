import { Component, OnInit, forwardRef, Input } from '@angular/core';
import { IsNotEmpty, validate } from 'class-validator';
import { Observable } from 'rxjs';
import { Store, Select } from '@ngxs/store';
import { SetGeneSymbols, GeneSymbolsModel, GeneSymbolsState } from './gene-symbols.state';

export class GeneSymbols {
  @IsNotEmpty()
  geneSymbols = '';
}

@Component({
  selector: 'gpf-gene-symbols',
  templateUrl: './gene-symbols.component.html',
})
export class GeneSymbolsComponent implements OnInit {
  geneSymbols = new GeneSymbols();
  errors: Array<string> = [];

  @Select(GeneSymbolsState) state$: Observable<GeneSymbolsModel>;

  constructor(
    private store: Store,
  ) { }

  ngOnInit() {
    this.store.selectOnce(state => state.geneSymbolsState).subscribe(state => {
      // restore state
      this.geneSymbols.geneSymbols = state.geneSymbols.join('\n');
    });

    this.state$.subscribe(state => {
      // validate for errors
      validate(this.geneSymbols).then(errors => { this.errors = errors.map(err => String(err)); });
    });
  }

  setGeneSymbols(geneSymbols: string) {
    const result = geneSymbols
      .split(/[,\s]/)
      .filter(s => s !== '')
      .map(s => s.toUpperCase());
    this.geneSymbols.geneSymbols = geneSymbols;
    this.store.dispatch(new SetGeneSymbols(result));
  }
}
