import { Component, OnInit, EventEmitter, Output, Input } from '@angular/core';
import { Subject } from 'rxjs';
import { ValidateNested } from 'class-validator';
import { Store } from '@ngxs/store';
import { GeneService } from '../gene-view/gene.service';
import { GeneSymbols } from 'app/gene-symbols/gene-symbols.component';
import { SetGeneSymbols, GeneSymbolsState } from 'app/gene-symbols/gene-symbols.state';
import { StatefulComponent } from 'app/common/stateful-component';

@Component({
  selector: 'gpf-gene-symbol-with-search',
  templateUrl: './gene-symbols-with-search.component.html',
})
export class GeneSymbolsWithSearchComponent extends StatefulComponent implements OnInit {
  @Input() hideDropdown: boolean;
  @Output() inputClickEvent  = new EventEmitter();

  @ValidateNested()
  geneSymbols = new GeneSymbols();

  matchingGeneSymbols: string[] = [];
  searchString = '';
  searchKeystrokes$: Subject<string> = new Subject();

  constructor(protected store: Store, private geneService: GeneService) {
    super(store, GeneSymbolsState, 'geneSymbols');
  }

  ngOnInit() {
    super.ngOnInit();
    this.store.selectOnce(state => state.geneSymbolsState).subscribe(state => {
      // restore state
      this.geneSymbols.geneSymbols = state.geneSymbols.join('\n');
    });

    this.searchKeystrokes$
    .debounceTime(200)
    .distinctUntilChanged()
    .subscribe(searchTerm => {
      this.searchString = searchTerm;
      if (this.searchString !== '') {
        this.geneService.searchGenes(this.searchString).subscribe(
          response => this.matchingGeneSymbols = response['gene_symbols']
        );
      } else {
        this.matchingGeneSymbols = [];
      }
    });
  }

  searchBoxChange(searchTerm: string) {
    this.searchKeystrokes$.next(searchTerm.toUpperCase());
  }

  selectGene(geneSymbol: string) {
    this.geneSymbols.geneSymbols = geneSymbol;
    this.store.dispatch(new SetGeneSymbols(geneSymbol ? [geneSymbol] : []));
    this.inputClickEvent.emit();
  }
}
