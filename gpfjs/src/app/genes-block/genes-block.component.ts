import { Component, Input, ViewChild, AfterViewInit } from '@angular/core';
import { Store, Selector } from '@ngxs/store';
import { GeneSymbolsState } from 'app/gene-symbols/gene-symbols.state';
import { GeneSetsState } from 'app/gene-sets/gene-sets.state';
import { GeneWeightsState } from 'app/gene-weights/gene-weights.state';

@Component({
  selector: 'gpf-genes-block',
  templateUrl: './genes-block.component.html',
  styleUrls: ['./genes-block.component.css'],
})
export class GenesBlockComponent implements AfterViewInit {
  @Input() showAllTab = true;
  @ViewChild('nav') ngbNav;

  constructor(private store: Store) { }

  ngAfterViewInit() {
    this.store.selectOnce(GenesBlockComponent.genesBlockState).subscribe(state => {
      if (state.geneSymbols.length) {
        setTimeout(() => this.ngbNav.select('geneSymbols'));
      } else if (state.geneSet !== null) {
        setTimeout(() => this.ngbNav.select('geneSets'));
      } else if (state.geneWeight !== null) {
        setTimeout(() => this.ngbNav.select('geneWeights'));
      }
    });
  }

  @Selector([GeneSymbolsState, GeneSetsState, GeneWeightsState])
  static genesBlockState(
    geneSymbolsState, geneSetsState, geneWeightsState
  ) {
    return {...geneSymbolsState, ...geneSetsState, ...geneWeightsState};
  }
}
