import { Component, Input, ViewChild, AfterViewInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { NgbNav } from '@ng-bootstrap/ng-bootstrap';
import { resetGeneSymbols, selectGeneSymbols } from 'app/gene-symbols/gene-symbols.state';
import { resetGeneSetsValues, selectGeneSets } from 'app/gene-sets/gene-sets.state';
import { resetGeneScoresValues, selectGeneScores } from 'app/gene-scores/gene-scores.state';
import { combineLatest, take } from 'rxjs';

@Component({
  selector: 'gpf-genes-block',
  templateUrl: './genes-block.component.html',
  styleUrls: ['./genes-block.component.css'],
})
export class GenesBlockComponent implements AfterViewInit {
  @Input() public showAllTab = true;
  @ViewChild('nav') public ngbNav: NgbNav;

  public constructor(private store: Store) { }

  public ngAfterViewInit(): void {
    combineLatest([
      this.store.select(selectGeneSymbols),
      this.store.select(selectGeneSets),
      this.store.select(selectGeneScores),
    ]).pipe(take(1)).subscribe(([geneSymbols, geneSets, geneScores]) => {
      if (geneSymbols.length) {
        setTimeout(() => this.ngbNav.select('geneSymbols'));
      } else if (geneSets.geneSet) {
        setTimeout(() => this.ngbNav.select('geneSets'));
      } else if (geneScores.score) {
        setTimeout(() => this.ngbNav.select('geneScores'));
      }
    });
  }

  public onNavChange(): void {
    this.store.dispatch(resetGeneSymbols());
    this.store.dispatch(resetGeneSetsValues());
    this.store.dispatch(resetGeneScoresValues());
  }
}
