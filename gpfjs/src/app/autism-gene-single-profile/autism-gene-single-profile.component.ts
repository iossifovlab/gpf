import { Component, Input, OnChanges, OnInit } from '@angular/core';
import { AutismGeneToolConfig, AutismGeneToolGene } from 'app/autism-gene-profiles/autism-gene-profile';
import { Observable } from 'rxjs';
import { AutismGeneSingleProfileService } from './autism-gene-single-profile.service';
import { GeneWeightsService } from '../gene-weights/gene-weights.service';
import { GeneWeights } from 'app/gene-weights/gene-weights';

@Component({
  selector: 'gpf-autism-gene-single-profile',
  templateUrl: './autism-gene-single-profile.component.html',
  styleUrls: ['./autism-gene-single-profile.component.css']
})
export class AutismGeneSingleProfileComponent implements OnInit, OnChanges {
  @Input() readonly geneSymbol: string;
  @Input() config: AutismGeneToolConfig;

  private gene$: Observable<AutismGeneToolGene>;
  private autismScores: String[];
  private protectionScores: String[];
  private autismScoreGeneWeights: GeneWeights[];
  private protectionScoreGeneWeights: GeneWeights[];
  private geneLists: string[];

  constructor(
    private autismGeneSingleProfileService: AutismGeneSingleProfileService,
    private geneWeightsService: GeneWeightsService,
  ) { }

  ngOnChanges(): void {
    if (this.config) {
      this.geneLists = this.config['geneLists'];
    }
  }

  ngOnInit(): void {
    this.gene$ = this.autismGeneSingleProfileService.getGene(this.geneSymbol);

    this.gene$.subscribe(res => {
      this.protectionScores = [...res['protectionScores'].keys()];
      this.autismScores = [...res['autismScores'].keys()];

      this.geneWeightsService.getGeneWeights().subscribe(
        geneWeights => {
          this.autismScoreGeneWeights = geneWeights.filter(
            geneWeight => {
              return this.autismScores.includes(geneWeight['weight']);
            }
          );

          this.protectionScoreGeneWeights = geneWeights.filter(
            geneWeight => {
              return this.protectionScores.includes(geneWeight['weight']);
            }
          );
        }
      );
    });
  }

  formatScoreName(score: string) {
    return score.split('_').join(' ');
  }
}
