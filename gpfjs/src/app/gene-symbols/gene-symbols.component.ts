import { Component, OnInit, AfterViewInit } from '@angular/core';
import { IsNotEmpty, ValidateNested } from 'class-validator';
import { Store } from '@ngxs/store';
import { SetGeneSymbols, GeneSymbolsState } from './gene-symbols.state';
import { StatefulComponent } from 'app/common/stateful-component';

export class GeneSymbols {
  @IsNotEmpty()
  geneSymbols = '';
}

@Component({
  selector: 'gpf-gene-symbols',
  templateUrl: './gene-symbols.component.html',
})
export class GeneSymbolsComponent extends StatefulComponent implements OnInit {

  @ValidateNested()
  geneSymbols: GeneSymbols = new GeneSymbols();

  constructor(protected store: Store) {
    super(store, GeneSymbolsState, 'geneSymbols');
  }

  ngOnInit() {
    super.ngOnInit();
    this.store.selectOnce(GeneSymbolsState).subscribe(state => {
      // restore state
      this.setGeneSymbols(state.geneSymbols.join('\n'));
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
