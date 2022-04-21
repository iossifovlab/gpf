import { Component, Input, ViewChild, AfterViewInit } from '@angular/core';
import { Store, Selector } from '@ngxs/store';
import { GeneSymbolsState, GeneSymbolsModel } from 'app/gene-symbols/gene-symbols.state';
import { GeneSetsState } from 'app/gene-sets/gene-sets.state';
import { GeneWeightsState } from 'app/gene-weights/gene-weights.state';
import { StateReset } from 'ngxs-reset-plugin';
import { NgbNav } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'gpf-genes-block',
  templateUrl: './genes-block.component.html',
  styleUrls: ['./genes-block.component.css'],
})
export class GenesBlockComponent implements AfterViewInit {
  @Input() public showAllTab = true;
  @ViewChild('nav') public ngbNav: NgbNav;

  @Selector([GeneSymbolsState, GeneSetsState.queryStateSelector, GeneWeightsState.queryStateSelector])
  public static genesBlockState(geneSymbolsState: GeneSymbolsModel, geneSetsQueryState, geneWeightsState): object {
    let result = {};
    if (geneSymbolsState.geneSymbols.length) {
      result['geneSymbols'] = geneSymbolsState.geneSymbols;
    }
    if (geneSetsQueryState) {
      result = {...result, ...geneSetsQueryState} as object;
    }
    if (geneWeightsState) {
      result = {...result, ...geneWeightsState} as object;
    }
    return result;
  }

  public constructor(private store: Store) { }

  public ngAfterViewInit(): void {
    this.store.selectOnce(GenesBlockComponent.genesBlockState).subscribe(state => {
      if (state['geneSymbols']) {
        setTimeout(() => this.ngbNav.select('geneSymbols'));
      } else if (state['geneSet']) {
        setTimeout(() => this.ngbNav.select('geneSets'));
      } else if (state['geneWeights']) {
        setTimeout(() => this.ngbNav.select('geneWeights'));
      }
    });
  }

  public onNavChange(): void {
    this.store.dispatch(new StateReset(GeneSymbolsState, GeneSetsState, GeneWeightsState));
  }
}
