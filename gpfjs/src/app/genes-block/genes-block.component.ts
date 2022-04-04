import { Component, Input, ViewChild, AfterViewInit } from '@angular/core';
import { Store, Selector } from '@ngxs/store';
import { GeneSymbolsState, GeneSymbolsModel } from 'app/gene-symbols/gene-symbols.state';
import { GeneSetsState, GeneSetsModel } from 'app/gene-sets/gene-sets.state';
import { GeneScoresState, GeneScoresModel } from 'app/gene-scores/gene-scores.state';
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

  @Selector([GeneSymbolsState, GeneSetsState.queryStateSelector, GeneScoresState.queryStateSelector])
  public static genesBlockState(
    geneSymbolsState: GeneSymbolsModel, geneSetsQueryState: GeneScoresModel, geneScoresState: GeneSetsModel,
  ): object {
    let result = {};
    if (geneSymbolsState.geneSymbols.length) {
      result['geneSymbols'] = geneSymbolsState.geneSymbols;
    }
    if (geneSetsQueryState) {
      result = {...result, ...geneSetsQueryState};
    }
    if (geneScoresState) {
      result = {...result, ...geneScoresState};
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
      } else if (state['geneScores']) {
        setTimeout(() => this.ngbNav.select('geneScores'));
      }
    });
  }

  public onNavChange(): void {
    this.store.dispatch(new StateReset(GeneSymbolsState, GeneSetsState, GeneScoresState));
  }
}
