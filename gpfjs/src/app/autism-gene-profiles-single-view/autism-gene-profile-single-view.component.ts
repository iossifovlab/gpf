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
  genomicScoresCategories = [];

  gene$: Observable<AutismGeneToolGene>;
  genomicScores: AutismGeneToolGenomicScoresCategory[];

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

    this.gene$.subscribe(res => {
      for (let i = 0; i < res['genomicScores'].length; i++) {
        this.geneWeightsService.getGeneWeights([...res['genomicScores'][i].scores.keys()].join(',')).subscribe(kek => {
          this.genomicScoresCategories.push({category: res['genomicScores'][i].category, scores: kek});
        });
      }
    });
  }

  formatScoreName(score: string) {
    return score.split('_').join(' ');
  }

  getGeneWeightByKey(category: string, key: string): GeneWeights {
    return this.genomicScoresCategories.find(
      genomicScoresCategory => genomicScoresCategory.category === category
    ).scores.find(weight => weight.weight === key);
  }

  getSingleScoreValue(genomicScores, category: string, score: string) {
    return genomicScores.find(cat => cat['category'] === category)['scores'].get(score);
  }

  get histogramOptions() {
    return this._histogramOptions;
  }

  get geneBrowserUrl(): string {
    if (!this.config) {
      return;
    }

    const dataset = this.config['defaultDataset'];
    let pathname = this.router.createUrlTree(['datasets', dataset, 'gene-browser', this.geneSymbol]).toString();

    pathname = this.location.prepareExternalUrl(pathname);

    return window.location.origin + pathname;
  }
}
