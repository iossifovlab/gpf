import { Component, Input, OnInit } from '@angular/core';
import { AgpDatasetPersonSet, AgpDatasetStatistic, AgpGene, AgpGenomicScores, AgpGenomicScoresCategory, AgpTableConfig } from 'app/autism-gene-profiles-table/autism-gene-profile-table';
import { Observable, of, zip } from 'rxjs';
import { GeneWeightsService } from '../gene-weights/gene-weights.service';
import { GeneWeights } from 'app/gene-weights/gene-weights';
import { AutismGeneProfilesService } from 'app/autism-gene-profiles-block/autism-gene-profiles.service';
import { switchMap, take, tap } from 'rxjs/operators';
import { Router } from '@angular/router';
import { Location } from '@angular/common';
import { GeneService } from 'app/gene-view/gene.service';
import { Gene } from 'app/gene-view/gene';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Store } from '@ngxs/store';
import { QueryService } from 'app/query/query.service';
import { GenomicScore } from 'app/genotype-browser/genotype-browser';
import { SetEffectTypes } from 'app/effecttypes/effecttypes.state';
import { SetGeneSymbols } from 'app/gene-symbols/gene-symbols.state';
import { SetGenomicScores } from 'app/genomic-scores-block/genomic-scores-block.state';
import { SetPedigreeSelector } from 'app/pedigree-selector/pedigree-selector.state';
import { SetPresentInChildValues } from 'app/present-in-child/present-in-child.state';
import { SetPresentInParentValues } from 'app/present-in-parent/present-in-parent.state';
import { SetStudyTypes } from 'app/study-types/study-types.state';
import { SetVariantTypes } from 'app/varianttypes/varianttypes.state';
import { EffectTypes } from 'app/effecttypes/effecttypes';

@Component({
  selector: 'gpf-autism-gene-profile-single-view',
  templateUrl: './autism-gene-profile-single-view.component.html',
  styleUrls: ['./autism-gene-profile-single-view.component.css']
})
export class AutismGeneProfileSingleViewComponent implements OnInit {
  @Input() readonly geneSymbol: string;
  @Input() config: AgpTableConfig;
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
    GeneBrowser: '',
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
    private queryService: QueryService,
    private store: Store,
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
        zip(...geneWeightsObservables).subscribe(geneWeightsArray => {
          for (let k = 0; k < geneWeightsArray.length; k++) {
            this.genomicScoresGeneWeights.push({
              category: gene.genomicScores[k].id,
              scores: geneWeightsArray[k]
            });
          }
        });
        return this.geneService.getGene(this.geneSymbol);
      }),
      switchMap(gene => {
        return zip(of(gene), this.datasetsService.getDataset(this.config.defaultDataset));
      })
    ).subscribe(([gene, dataset]) => {
      this.setLinks(this.geneSymbol, gene, dataset.genome);
    });
  }

  setLinks(geneSymbol: string, gene: Gene, datasetGenome): void {
    if (this.isGeneInSFARI) {
      this.links.SFARIgene = 'https://gene.sfari.org/database/human-gene/' + geneSymbol;
    }

    this.links.GeneBrowser = this.getGeneBrowserLink();
    this.links.UCSC = this.getUCSCLink(gene, datasetGenome);
    this.links.GeneCards = 'https://www.genecards.org/cgi-bin/carddisp.pl?gene=' + geneSymbol;
    this.links.Pubmed = 'https://pubmed.ncbi.nlm.nih.gov/?term=' + geneSymbol + '%20AND%20(autism%20OR%20asd)';
  }

  getUCSCLink(gene: Gene, datasetGenome): string {
    const genome: string = datasetGenome;
    const chromosomePrefix: string = genome === 'hg38' ? '' : 'chr';
    const chromosome: string = gene.transcripts[0].chrom;
    const geneStartPosition: number = gene.transcripts[0].start;
    const geneStopPosition: number = gene.transcripts[gene.transcripts.length - 1].stop;

    return `https://genome.ucsc.edu/cgi-bin/hgTracks?db=${genome}&position=${chromosomePrefix}${chromosome}%3A${geneStartPosition}-${geneStopPosition}`;
  }

  getGeneBrowserLink(): string {
    if (!this.config) {
      return;
    }

    const dataset = this.config.defaultDataset;
    let pathname = this.router.createUrlTree(['datasets', dataset, 'gene-browser', this.geneSymbol]).toString();
    pathname = this.location.prepareExternalUrl(pathname);
    return window.location.origin + pathname;
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

  goToQuery(geneSymbol: string, personSet: AgpDatasetPersonSet, datasetId: string, statistic: AgpDatasetStatistic) {
    AutismGeneProfileSingleViewComponent.goToQuery(
      this.store, this.queryService, geneSymbol, personSet, datasetId, statistic
    );
  }

  static goToQuery(
    store: Store, queryService: QueryService, geneSymbol: string, personSet: AgpDatasetPersonSet, datasetId: string, statistic: AgpDatasetStatistic
  ) {
    const effectTypes = {
      lgds: EffectTypes['LGDS'],
      intron: ['Intron'],
      missense: ['Missense'],
    };
    const newWindow = window.open('', '_blank');

    const genomicScores: GenomicScore[] = [];
    if (statistic.scores) {
      genomicScores[0] = new GenomicScore(
        statistic.scores[0]['name'],
        statistic.scores[0]['min'],
        statistic.scores[0]['max'],
      );
    }

    const presentInChildValues = ['proband only', 'proband and sibling', 'sibling only'];
    const presentInParentRareValues = ['father only', 'mother only', 'mother and father'];

    let presentInParent: string[] = ['neither'];
    let rarityType = 'all';
    if (statistic.category === 'rare') {
      rarityType = 'rare';
      presentInParent = presentInParentRareValues;
    }

    store.dispatch([
      new SetGeneSymbols([geneSymbol]),
      new SetEffectTypes(new Set(effectTypes[statistic['effects'][0]])),
      new SetStudyTypes(new Set(['we'])),
      new SetVariantTypes(new Set(statistic['variantTypes'])),
      new SetGenomicScores(genomicScores),
      new SetPresentInChildValues(new Set(presentInChildValues)),
      new SetPresentInParentValues(new Set(presentInParent), rarityType, 0, 1),
      new SetPedigreeSelector(personSet.collectionId, new Set([personSet.id])),
    ]);

    store.selectOnce(state => state).subscribe(state => {
      state['datasetId'] = datasetId;
      queryService.saveQuery(state, 'genotype')
      .pipe(take(1))
      .subscribe(urlObject => {
        const url = queryService.getLoadUrlFromResponse(urlObject);
        newWindow.location.assign(url);
      });
    });
  }
}
