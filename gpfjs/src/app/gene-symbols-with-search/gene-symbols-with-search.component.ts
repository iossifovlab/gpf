import { Component, OnInit, forwardRef, EventEmitter, Output, Input } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { IsNotEmpty, validate } from 'class-validator';
import { Store, Select } from '@ngxs/store';
import { GeneService } from '../gene-view/gene.service';
import { GeneSymbols } from 'app/gene-symbols/gene-symbols.component';
import { SetGeneSymbols, GeneSymbolsModel, GeneSymbolsState } from 'app/gene-symbols/gene-symbols.state';

@Component({
  selector: 'gpf-gene-symbol-with-search',
  templateUrl: './gene-symbols-with-search.component.html',
})
export class GeneSymbolsWithSearchComponent implements OnInit {
  @Input() hideDropdown: boolean;
  @Output() inputClickEvent  = new EventEmitter();
  @Select(GeneSymbolsState) state$: Observable<GeneSymbolsModel>;

  geneSymbols = new GeneSymbols();
  errors: Array<string> = [];

  matchingGeneSymbols: string[] = [];
  searchString = '';
  searchKeystrokes$: Subject<string> = new Subject();

  constructor(
    private store: Store,
    private geneService: GeneService
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
