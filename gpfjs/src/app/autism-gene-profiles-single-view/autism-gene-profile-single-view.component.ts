import { Component, Input, OnInit } from '@angular/core';
import { AgpConfig, AgpGene, AgpGenomicScores, AgpGenomicScoresCategory } from 'app/autism-gene-profiles-table/autism-gene-profile-table';
import { Observable } from 'rxjs';
import { GeneWeightsService } from '../gene-weights/gene-weights.service';
import { GeneWeights } from 'app/gene-weights/gene-weights';
import { AutismGeneProfilesService } from 'app/autism-gene-profiles-block/autism-gene-profiles.service';
import { switchMap, tap } from 'rxjs/operators';
import { Router } from '@angular/router';
import { Location } from '@angular/common';
import { GeneService } from 'app/gene-view/gene.service';
import { Gene } from 'app/gene-view/gene';
import { DatasetsService } from 'app/datasets/datasets.service';
import { DatasetDetails } from 'app/datasets/datasets';

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

  isGeneInSFARI = false;
  links = {
    SFARIgene: '',
    UCSC: '',
    GeneCards: '',
    Pubmed: ''
  };

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
    private geneWeightsService: GeneWeightsService,
    private geneService: GeneService,
    private datasetsService: DatasetsService,
    private location: Location,
    private router: Router,
  ) { }

  ngOnInit(): void {
    this.gene$ = this.autismGeneProfilesService.getGene(this.geneSymbol);
    this.gene$.pipe(
      switchMap(gene => {
        gene.geneSets.forEach(element => {
          if (element.match(/sfari/i)) {
            this.isGeneInSFARI = true;
          }
        });

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

    this.geneService.getGene(this.geneSymbol).subscribe(gene => {
      this.datasetsService.getDatasetDetails(this.config.defaultDataset).subscribe(datasetDetails => {
        this.setLinks(this.geneSymbol, gene, datasetDetails);
      });
    });
  }

  setLinks(geneSymbol: string, gene: Gene, datasetDetails: DatasetDetails): void {
    if (this.isGeneInSFARI) {
      this.links.SFARIgene = 'https://gene.sfari.org/database/human-gene/' + geneSymbol;
    }

    this.links.UCSC = this.getUCSCLink(gene, datasetDetails);
    this.links.GeneCards = 'https://www.genecards.org/cgi-bin/carddisp.pl?gene=' + geneSymbol;
    this.links.Pubmed = 'https://pubmed.ncbi.nlm.nih.gov/?term=' + geneSymbol + '%20AND%20(autism%20OR%20asd)';
  }

  getUCSCLink(gene: Gene, datasetDetails: DatasetDetails): string {
    return 'https://genome.ucsc.edu/cgi-bin/hgTracks?db=' + datasetDetails.genome + '&lastVirtModeType=default'
      + '&lastVirtModeExtraState=&virtModeType=default&virtMode=0&nonVirtPosition=&position=chr'
      + gene.transcripts[0].chrom + '%3A' + gene.transcripts[0].start + '-'
      + gene.transcripts[gene.transcripts.length - 1].stop
      + '&hgsid=1120191263_9kJvHXmsIQajgm163GA7k8YV4ay4';
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

  getGeneDatasetValue(gene: AgpGene, studyId: string, personSetId: string, statisticId: string) {
    return gene.studies.find(study => study.id === studyId).personSets
    .find(genePersonSet => genePersonSet.id === personSetId).effectTypes
    .find(effectType => effectType.id === statisticId);
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
