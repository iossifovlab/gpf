import { Component, Input, OnInit } from '@angular/core';
import { AutismGeneToolConfig, AutismGeneToolGene } from 'app/autism-gene-profiles/autism-gene-profile';
import { Observable } from 'rxjs';
import { GeneWeightsService } from '../gene-weights/gene-weights.service';
import { GeneWeights } from 'app/gene-weights/gene-weights';
import { AutismGeneProfilesService } from 'app/autism-gene-profiles/autism-gene-profiles.service';

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

    this.gene$.subscribe(res => {
      const autismScores: string = [...res['autismScores'].keys()].join(',');
      const protectionScores: string = [...res['protectionScores'].keys()].join(',');

      this.geneWeightsService.getGeneWeights(autismScores).subscribe(
        geneWeights => this.autismScoreGeneWeights = geneWeights
      );

      this.geneWeightsService.getGeneWeights(protectionScores).subscribe(
        geneWeights => this.protectionScoreGeneWeights = geneWeights
      );
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
