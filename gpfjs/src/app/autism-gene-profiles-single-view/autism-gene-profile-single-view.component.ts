import { Component, Input, OnInit } from '@angular/core';
import { AgpConfig, AgpGene, AgpGeneSetsCategory, AgpGenomicScores, AgpGenomicScoresCategory } from 'app/autism-gene-profiles-table/autism-gene-profile-table';
import { Observable, zip } from 'rxjs';
import { GeneWeightsService } from '../gene-weights/gene-weights.service';
import { GeneWeights } from 'app/gene-weights/gene-weights';
import { AutismGeneProfilesService } from 'app/autism-gene-profiles-block/autism-gene-profiles.service';
import { mergeMap, switchMap, tap } from 'rxjs/operators';
import { Router } from '@angular/router';
import { Location } from '@angular/common';

@Component({
  selector: 'gpf-autism-gene-profile-single-view',
  templateUrl: './autism-gene-profile-single-view.component.html',
  styleUrls: ['./autism-gene-profile-single-view.component.css']
})
export class AutismGeneProfileSingleViewComponent implements OnInit {
  @Input() readonly geneSymbol: string;
  @Input() config: AgpConfig;
  genomicScoresGeneWeights = [];

  gene$: Observable<AgpGene>;
  genomicScores: AgpGenomicScoresCategory[];

  private _histogramOptions = {
    width: 525,
    height: 100,
    marginLeft: 50,
    marginTop: 25,
  };

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
    private geneWeightsService: GeneWeightsService,
    private location: Location,
    private router: Router,
  ) { }

  ngOnInit(): void {
    this.gene$ = this.autismGeneProfilesService.getGene(this.geneSymbol);

    this.gene$.pipe(
      switchMap(gene => {
        let scores: string;
        const geneWeightsObservables = [];
        for (let i = 0; i < gene.genomicScores.length; i++) {
          scores = [...gene.genomicScores[i].scores.map(score => score.id)].join(',');
          geneWeightsObservables.push(
            this.geneWeightsService.getGeneWeights(scores)
          );
        }
        return Observable.zip(...geneWeightsObservables).pipe(
          tap(geneWeightsArray => {
            for (let k = 0; k < geneWeightsArray.length; k++) {
              this.genomicScoresGeneWeights.push({
                category: gene.genomicScores[k].id,
                scores: geneWeightsArray[k]
              });
            }
          })
        );
      })
    ).subscribe();
  }

  formatScoreName(score: string) {
    return score.split('_').join(' ');
  }

  getGeneWeightByKey(category: string, key: string): GeneWeights {
    return this.genomicScoresGeneWeights
      .find(genomicScoresCategory => genomicScoresCategory.category === category).scores
      .find(score => score.weight === key);
  }

  getSingleScoreValue(genomicScores: AgpGenomicScores[], categoryId: string, scoreId: string) {
    return genomicScores.find(category => category.id === categoryId).scores.find(score => score.id === scoreId).value;
  }

  get histogramOptions() {
    return this._histogramOptions;
  }

  get geneBrowserUrl(): string {
    if (!this.config) {
      return;
    }

    const dataset = this.config.defaultDataset;
    let pathname = this.router.createUrlTree(['datasets', dataset, 'gene-browser', this.geneSymbol]).toString();

    pathname = this.location.prepareExternalUrl(pathname);

    return window.location.origin + pathname;
  }
}
