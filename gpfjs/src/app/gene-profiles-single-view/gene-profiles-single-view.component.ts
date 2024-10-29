import { Component, ElementRef, HostListener, Input, OnInit, ViewChild } from '@angular/core';
import {
  GeneProfilesDatasetPersonSet, GeneProfilesDatasetStatistic, GeneProfilesGene,
  GeneProfilesGenomicScores, GeneProfilesSingleViewConfig, GeneProfilesEffectType
} from 'app/gene-profiles-single-view/gene-profiles-single-view';
import { Observable, of, zip } from 'rxjs';
import { GeneScoresService } from '../gene-scores/gene-scores.service';
import { CategoricalHistogram, GeneScores, NumberHistogram } from 'app/gene-scores/gene-scores';
import { GeneProfilesService } from 'app/gene-profiles-block/gene-profiles.service';
import { switchMap, take } from 'rxjs/operators';
import { Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { QueryService } from 'app/query/query.service';
import { GenomicScore } from 'app/genotype-browser/genotype-browser';
import { LGDS } from 'app/effect-types/effect-types';
import { setEffectTypes } from 'app/effect-types/effect-types.state';
import { setVariantTypes } from 'app/variant-types/variant-types.state';
import { setGeneSymbols } from 'app/gene-symbols/gene-symbols.state';
import { setPresentInChild } from 'app/present-in-child/present-in-child.state';
import { setPresentInParent } from 'app/present-in-parent/present-in-parent.state';
import { setPedigreeSelector } from 'app/pedigree-selector/pedigree-selector.state';
import { selectGeneProfiles, setGeneProfilesOpenedTabs } from 'app/gene-profiles-table/gene-profiles-table.state';
import { setStudyTypes } from 'app/study-types/study-types.state';
import { setGenomicScores } from 'app/genomic-scores-block/genomic-scores-block.state';
import { cloneDeep } from 'lodash';

@Component({
  selector: 'gpf-gene-profiles-single-view',
  templateUrl: './gene-profiles-single-view.component.html',
  styleUrls: ['./gene-profiles-single-view.component.css']
})
export class GeneProfileSingleViewComponent implements OnInit {
  @ViewChild('stickySpan', {static: false}) public menuElement: ElementRef;

  @Input() public readonly geneSymbol: string;
  @Input() public config: GeneProfilesSingleViewConfig;
  @Input() public isInGeneCompare = false;
  public compactView = false;
  public showTemplate = true;

  public genomicScoresGeneScores: {category: string; scores: GeneScores[]}[] = [];
  public gene$: Observable<GeneProfilesGene>;

  public histogramOptions = {
    width: 525,
    height: 110,
    marginLeft: 50,
    marginTop: 25
  };

  public isGeneInSFARI = false;
  public links = {
    geneBrowser: '',
    ucsc: '',
    geneCards: '',
    pubmed: '',
    sfariGene: ''
  };

  private headerBottomYPosition = 116;
  public isHeaderSticky: boolean;

  public constructor(
    private geneProfilesService: GeneProfilesService,
    private geneScoresService: GeneScoresService,
    private router: Router,
    private queryService: QueryService,
    private store: Store,
  ) { }

  public errorModal = false;

  @HostListener('window:scroll', ['$event'])
  public handleScroll(): void {
    if (this.isInGeneCompare) {
      if (window.pageYOffset >= this.headerBottomYPosition) {
        this.isHeaderSticky = true;
      } else {
        this.isHeaderSticky = false;
      }
    }
  }

  @HostListener('window:resize')
  public onResize(): void {
    const viewWidth = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
    if (viewWidth < 1252) {
      this.compactView = true;
    } else {
      this.compactView = false;
    }
  }

  public ngOnInit(): void {
    this.gene$ = this.geneProfilesService.getGene(this.geneSymbol);

    this.gene$.pipe(
      switchMap(gene => {
        gene.geneSets.forEach(element => {
          if (element.match(/sfari/i)) {
            this.isGeneInSFARI = true;
          }
        });

        let scores: string;
        const geneScoresObservables: Observable<GeneScores[]>[] = [];
        for (const genomicScore of gene.genomicScores) {
          scores = [...genomicScore.scores.map(score => score.id)].join(',');
          geneScoresObservables.push(
            this.geneScoresService.getGeneScores(scores)
          );
        }
        const genomicScoresObservables: Observable<[string, GeneScores[]]>[] = [];
        for (let k = 0; k < geneScoresObservables.length; k++) {
          genomicScoresObservables.push(
            zip(
              of(gene.genomicScores[k].id),
              geneScoresObservables[k]
            )
          );
        }
        return zip(...genomicScoresObservables);
      }),
    ).subscribe({
      next: (genomicScores) => {
        for (const genomicScore of genomicScores) {
          this.genomicScoresGeneScores.push({
            category: genomicScore[0],
            scores: genomicScore[1]
          });
        }
      },
      error: () => {
        this.errorModal = true;
      }
    });
  }

  public getGeneScoreByKey(category: string, key: string): GeneScores {
    return this.genomicScoresGeneScores
      .find(genomicScoresCategory => genomicScoresCategory.category === category).scores
      .find(score => score.score === key);
  }

  public getSingleScoreValue(genomicScores: GeneProfilesGenomicScores[], categoryId: string, scoreId: string): number {
    return genomicScores.find(category => category.id === categoryId).scores.find(score => score.id === scoreId).value;
  }

  public getGeneDatasetValue(
    gene: GeneProfilesGene,
    studyId: string,
    personSetId: string,
    statisticId: string
  ): GeneProfilesEffectType {
    return gene.studies.find(study => study.id === studyId).personSets
      .find(genePersonSet => genePersonSet.id === personSetId).effectTypes
      .find(effectType => effectType.id === statisticId);
  }

  public goToQuery(
    geneSymbol: string,
    personSet: GeneProfilesDatasetPersonSet,
    datasetId: string,
    statistic: GeneProfilesDatasetStatistic
  ): void {
    GeneProfileSingleViewComponent.goToQuery(
      this.store, this.queryService, geneSymbol, personSet, datasetId, statistic
    );
  }

  public static goToQuery(
    store: Store,
    queryService: QueryService,
    geneSymbol: string,
    personSet: GeneProfilesDatasetPersonSet,
    datasetId: string,
    statistic: GeneProfilesDatasetStatistic,
    newTab: boolean = true
  ): void {
    const effectTypes = {
      // eslint-disable-next-line @typescript-eslint/naming-convention
      LGDs: LGDS,
      intron: ['intron'],
      missense: ['missense'],
      synonymous: ['synonymous'],
    };

    const genomicScores: GenomicScore[] = [];
    if (statistic.scores) {
      genomicScores[0] = new GenomicScore(
        statistic.scores[0]['name'] as string,
        statistic.scores[0]['min'] as number,
        statistic.scores[0]['max'] as number,
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
    if (statistic.effects) {
      store.dispatch(setEffectTypes({effectTypes: effectTypes[statistic['effects'][0]] as string[]}));
    }
    if (statistic.variantTypes) {
      store.dispatch(setVariantTypes({variantTypes: statistic.variantTypes}));
    }
    store.dispatch(setGeneSymbols({geneSymbols: [geneSymbol]}));
    store.dispatch(setPresentInChild({presentInChild: presentInChildValues}));
    store.dispatch(setPresentInParent({presentInParent: {
      presentInParent: presentInParent,
      rarity: {
        rarityType: rarityType,
        rarityIntervalStart: 0,
        rarityIntervalEnd: 1
      }
    }}));
    store.dispatch(setPedigreeSelector({
      pedigreeSelector: {
        id: personSet.collectionId,
        checkedValues: [personSet.id]
      }
    }));
    store.dispatch(setStudyTypes({studyTypes: ['we']}));
    store.dispatch(setGenomicScores({genomicScores: genomicScores}));

    store.pipe(take(1)).subscribe(state => {
      const clonedState = cloneDeep(state);
      clonedState['datasetId'] = datasetId;
      queryService.saveQuery(clonedState, 'genotype')
        .pipe(take(1))
        .subscribe(urlObject => {
          const url = queryService.getLoadUrlFromResponse(urlObject);
          if (newTab) {
            const newWindow = window.open('', '_blank');
            newWindow.location.assign(url);
          } else {
            window.location.assign(url);
          }
        });
    });
  }

  public errorModalBack(): void {
    this.errorModal = false;

    let tabs = [] as string[];

    this.store.select(selectGeneProfiles).pipe(take(1)).subscribe(state => {
      tabs = state.openedTabs;

      const index = tabs.indexOf(this.geneSymbol, 0);
      tabs.splice(index, 1);

      this.store.dispatch(setGeneProfilesOpenedTabs({ openedTabs: tabs }));
      this.router.navigate(['/gene-profiles']);
    });
  }

  public isNumberHistogram(arg: object): arg is NumberHistogram {
    return arg instanceof NumberHistogram;
  }

  public isCategoricalHistogram(arg: object): arg is CategoricalHistogram {
    return arg instanceof CategoricalHistogram;
  }
}
