import { Component, Input, OnInit } from '@angular/core';
import { AutismGeneToolConfig, AutismGeneToolGene } from 'app/autism-gene-profiles/autism-gene-profile';
import { Observable, zip } from 'rxjs';
import { GeneWeightsService } from '../gene-weights/gene-weights.service';
import { GeneWeights } from 'app/gene-weights/gene-weights';
import { AutismGeneProfilesService } from 'app/autism-gene-profiles/autism-gene-profiles.service';
import { mergeMap } from 'rxjs/operators';

@Component({
  selector: 'gpf-autism-gene-single-profile',
  templateUrl: './autism-gene-single-profile.component.html',
  styleUrls: ['./autism-gene-single-profile.component.css']
})
export class AutismGeneSingleProfileComponent implements OnInit {
  @Input() readonly geneSymbol: string;
  @Input() config: AutismGeneToolConfig;

  gene$: Observable<AutismGeneToolGene>;
  autismScoreGeneWeights: GeneWeights[];
  protectionScoreGeneWeights: GeneWeights[];
  geneSets: string[];

  private _histogramOptions = {
    width: 525,
    height: 100,
    marginLeft: 50,
    marginTop: 25,
  };

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
    private geneWeightsService: GeneWeightsService,
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
      this.autismScoreGeneWeights = res[0];
      this.protectionScoreGeneWeights = res[1];
    });
  }

  formatScoreName(score: string) {
    return score.split('_').join(' ');
  }

  getAutismScoreGeneWeight(autismScoreKey: string): GeneWeights {
    return this.autismScoreGeneWeights.find(weight => weight.weight === autismScoreKey);
  }

  getProtectionScoreGeneWeight(protectionScoreKey: string): GeneWeights {
    return this.protectionScoreGeneWeights.find(weight => weight.weight === protectionScoreKey);
  }

  get histogramOptions() {
    return this._histogramOptions;
  }

  get geneBrowserUrl(): string {
    if (!this.config) {
      return;
    }

    const dataset = this.config['defaultDataset'];

    return `/datasets/${dataset}/geneBrowser/${this.geneSymbol}`;
  }
}
