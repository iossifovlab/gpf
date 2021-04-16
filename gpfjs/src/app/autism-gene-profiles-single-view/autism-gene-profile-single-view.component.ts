import { Component, Input, OnInit } from '@angular/core';
import { AutismGeneToolConfig, AutismGeneToolGene, AutismGeneToolGeneSetsCategory, AutismGeneToolGenomicScoresCategory } from 'app/autism-gene-profiles-table/autism-gene-profile-table';
import { Observable, zip } from 'rxjs';
import { GeneWeightsService } from '../gene-weights/gene-weights.service';
import { GeneWeights } from 'app/gene-weights/gene-weights';
import { AutismGeneProfilesService } from 'app/autism-gene-profiles-block/autism-gene-profiles.service';
import { mergeMap } from 'rxjs/operators';
import { Router } from '@angular/router';
import { Location } from '@angular/common';

@Component({
  selector: 'gpf-autism-gene-profile-single-view',
  templateUrl: './autism-gene-profile-single-view.component.html',
  styleUrls: ['./autism-gene-profile-single-view.component.css']
})
export class AutismGeneProfileSingleViewComponent implements OnInit {
  @Input() readonly geneSymbol: string;
  @Input() config: AutismGeneToolConfig;

  gene$: Observable<AutismGeneToolGene>;
  genomicScores: AutismGeneToolGenomicScoresCategory[];
  geneSets: AutismGeneToolGeneSetsCategory[];

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
    this.geneSets = this.config['geneSets'];
    this.gene$ = this.autismGeneProfilesService.getGene(this.geneSymbol);
    let autismScores: string;
    let protectionScores: string;
    this.gene$.pipe(
      mergeMap((res) => {
        autismScores = [...res['autismScores'].keys()].join(',');
        protectionScores = [...res['protectionScores'].keys()].join(',');
        return zip(
          this.geneWeightsService.getGeneWeights(autismScores),
          this.geneWeightsService.getGeneWeights(protectionScores)
        );
      }),
    ).subscribe(res => {
      // this.autismScoreGeneWeights = res[0];
      // this.protectionScoreGeneWeights = res[1];
    });
  }

  formatScoreName(score: string) {
    return score.split('_').join(' ');
  }

  // getAutismScoreGeneWeight(autismScoreKey: string): GeneWeights {
  //   return this.autismScoreGeneWeights.find(weight => weight.weight === autismScoreKey);
  // }

  // getProtectionScoreGeneWeight(protectionScoreKey: string): GeneWeights {
  //   return this.protectionScoreGeneWeights.find(weight => weight.weight === protectionScoreKey);
  // }

  get histogramOptions() {
    return this._histogramOptions;
  }

  get geneBrowserUrl(): string {
    if (!this.config) {
      return;
    }

    const dataset = this.config['defaultDataset'];
    let pathname = this.router.createUrlTree(['datasets', dataset, 'geneBrowser', this.geneSymbol]).toString();

    pathname = this.location.prepareExternalUrl(pathname);

    return window.location.origin + pathname;
  }
}
