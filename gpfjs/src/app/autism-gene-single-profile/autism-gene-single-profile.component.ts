import { Component, Input, OnChanges, OnInit } from '@angular/core';
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
export class AutismGeneSingleProfileComponent implements OnInit, OnChanges {
  @Input() readonly geneSymbol: string;
  @Input() config: AutismGeneToolConfig;

  private gene$: Observable<AutismGeneToolGene>;
  private autismScoreGeneWeights: GeneWeights[];
  private protectionScoreGeneWeights: GeneWeights[];
  private geneSets: string[];

  private _histogramWidth = 525;
  private _histogramHeight = 145;

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
    private geneWeightsService: GeneWeightsService,
  ) { }

  ngOnChanges(): void {
    if (this.config) {
      this.geneSets = this.config['geneSets'];
    }
  }

  ngOnInit(): void {
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

  get histogramWidth() {
    return this._histogramWidth;
  }

  get histogramHeight() {
    return this._histogramHeight;
  }
}
