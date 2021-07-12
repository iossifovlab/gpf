import { Component, Input, ViewChild, AfterViewInit } from '@angular/core';
import { Store, Selector } from '@ngxs/store';
import { GeneSymbolsState, GeneSymbolsModel } from 'app/gene-symbols/gene-symbols.state';
import { GeneSetsState, GeneSetsModel } from 'app/gene-sets/gene-sets.state';
import { GeneWeightsState, GeneWeightsModel } from 'app/gene-weights/gene-weights.state';
import { StateReset } from 'ngxs-reset-plugin';

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
      if (state['geneSymbols']) {
        setTimeout(() => this.ngbNav.select('geneSymbols'));
      } else if (state['geneSet']) {
        setTimeout(() => this.ngbNav.select('geneSets'));
      } else if (state['geneWeight']) {
        setTimeout(() => this.ngbNav.select('geneWeights'));
      }
    });
  }

  onNavChange() {
    this.store.dispatch(new StateReset(GeneSymbolsState, GeneSetsState, GeneWeightsState));
  }

  @Selector([GeneSymbolsState, GeneSetsState.queryStateSelector, GeneWeightsState.queryStateSelector])
  static genesBlockState(
    geneSymbolsState: GeneSymbolsModel, geneSetsQueryState, geneWeightsState,
  ) {
    let result = {};
    if (geneSymbolsState.geneSymbols.length) {
      result['geneSymbols'] = geneSymbolsState.geneSymbols;
    }
    if (geneSetsQueryState) {
      result = {...result, geneSetsQueryState};
    }
    if (geneWeightsState) {
      result = {...result, geneWeightsState};
    }
    return result;
  }
}
