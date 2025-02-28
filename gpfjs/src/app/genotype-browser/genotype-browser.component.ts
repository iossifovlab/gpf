import { Component, Input, OnDestroy, OnInit } from '@angular/core';
import { combineLatest, Observable, Subscription } from 'rxjs';
import { QueryService } from '../query/query.service';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { ConfigService } from '../config/config.service';
import { Dataset, PersonSet, PersonSetCollection } from '../datasets/datasets';
import { GenotypePreviewVariantsArray } from 'app/genotype-preview-model/genotype-preview';
import { filter, map, switchMap, take } from 'rxjs/operators';
import { clone } from 'lodash';
import { NavigationStart, Router } from '@angular/router';
import { selectDatasetId } from 'app/datasets/datasets.state';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Store } from '@ngrx/store';
import { selectErrors } from 'app/common/errors.state';
import { selectVariantTypes } from 'app/variant-types/variant-types.state';
import { selectEffectTypes } from 'app/effect-types/effect-types.state';
import { selectFamilyIds } from 'app/family-ids/family-ids.state';
import { selectFamilyTags } from 'app/family-tags/family-tags.state';
import { selectGenders } from 'app/gender/gender.state';
import { selectGeneScores } from 'app/gene-scores/gene-scores.state';
import { selectGeneSets } from 'app/gene-sets/gene-sets.state';
import { selectGeneSymbols } from 'app/gene-symbols/gene-symbols.state';
import { selectGenomicScores } from 'app/genomic-scores-block/genomic-scores-block.state';
import { selectInheritanceTypes } from 'app/inheritancetypes/inheritancetypes.state';
import { selectPedigreeSelector } from 'app/pedigree-selector/pedigree-selector.state';
import { selectPersonFilters } from 'app/person-filters/person-filters.state';
import { selectPersonIds } from 'app/person-ids/person-ids.state';
import { selectPresentInChild } from 'app/present-in-child/present-in-child.state';
import { selectPresentInParent } from 'app/present-in-parent/present-in-parent.state';
import { selectRegionsFilters } from 'app/regions-filter/regions-filter.state';
import { selectStudyFilters } from 'app/study-filters/study-filters.state';
import { selectStudyTypes } from 'app/study-types/study-types.state';
import {
  selectUniqueFamilyVariantsFilter
} from 'app/unique-family-variants-filter/unique-family-variants-filter.state';
import {
  selectFamilyMeasureHistograms,
  selectPersonMeasureHistograms
} from 'app/person-filters-selector/measure-histogram.state';


@Component({
  selector: 'gpf-genotype-browser',
  templateUrl: './genotype-browser.component.html',
  styleUrls: ['./genotype-browser.component.css'],
})
export class GenotypeBrowserComponent implements OnInit, OnDestroy {
  public genotypePreviewVariantsArray: GenotypePreviewVariantsArray;
  public showTable = false;
  public legend: Array<PersonSet>;

  public disableQueryButtons;
  private routerSubscription: Subscription;

  public selectedDatasetId: string;
  public selectedDataset: Dataset;

  @Input()
  public genotypeBrowserState: object;
  public loadingFinished: boolean;

  public variantsCountDisplay: string;

  public constructor(
    private queryService: QueryService,
    public readonly configService: ConfigService,
    private loadingService: FullscreenLoadingService,
    private router: Router,
    private datasetsService: DatasetsService,
    private store: Store
  ) {
    this.routerSubscription = this.router.events.pipe(
      filter(event => event instanceof NavigationStart)
    ).subscribe(() => {
      this.queryService.cancelStreamPost();
      this.loadingService.setLoadingStop();
    });
  }

  public ngOnInit(): void {
    this.genotypeBrowserState = {};

    this.store.select(selectDatasetId).pipe(
      take(1),
      switchMap(datasetIdState => this.datasetsService.getDataset(datasetIdState))
    ).subscribe(dataset => {
      if (!dataset) {
        return;
      }
      this.selectedDataset = dataset;
    });

    this.getGenotypeBrowserState().subscribe(state => {
      this.genotypeBrowserState = {...state};
      this.queryService.cancelStreamPost();
      this.genotypePreviewVariantsArray = null;
    });

    this.loadingService.interruptEvent.subscribe(() => {
      this.queryService.cancelStreamPost();
      this.loadingService.setLoadingStop();
      this.showTable = false;
      this.loadingFinished = true;
      this.genotypePreviewVariantsArray = null;
    });

    this.store.select(selectErrors).subscribe(errorState => {
      setTimeout(() => {
        this.disableQueryButtons = errorState.length > 0;
      });
    });
  }

  private getGenotypeBrowserState(): Observable<object> {
    return combineLatest(
      this.store.select(selectVariantTypes),
      this.store.select(selectEffectTypes),
      this.store.select(selectGenders),
      this.store.select(selectInheritanceTypes),
      this.store.select(selectPresentInChild),
      this.store.select(selectPresentInParent), // edited
      this.store.select(selectStudyTypes),
      this.store.select(selectPedigreeSelector),
      this.store.select(selectFamilyIds),
      this.store.select(selectFamilyTags),
      this.store.select(selectPersonFilters),
      this.store.select(selectGeneSymbols),
      this.store.select(selectGeneSets),
      this.store.select(selectGeneScores),
      this.store.select(selectRegionsFilters),
      this.store.select(selectGenomicScores),
      this.store.select(selectPersonIds),
      this.store.select(selectUniqueFamilyVariantsFilter),
      this.store.select(selectStudyFilters),
      this.store.select(selectFamilyMeasureHistograms),
      this.store.select(selectPersonMeasureHistograms),
    ).pipe(
      map(([
        variantTypesState,
        effectTypesState,
        gendersState,
        inheritanceTypesState,
        presentInChildState,
        presentInParentState, // edited
        studyTypesState,
        pedigreeSelectorState,
        familyIdsState,
        familyTagsState,
        personFiltersState,
        geneSymbolsState,
        geneSetsState,
        geneScoresState,
        regionsFiltersState,
        genomicScoresState,
        personIdsState,
        uniqueFamilyVariantsFilterState,
        studyFiltersState,
        familyMeasureHistogramsState,
        personMeasureHistogramsState,
      ]) => {
        const presentInParent = {
          presentInParent: presentInParentState.presentInParent,
          rarity: {}
        };

        if (presentInParentState.rarity.rarityType === 'ultraRare') {
          presentInParent['rarity']['ultraRare'] = true;
        } else {
          presentInParent['rarity']['ultraRare'] = false;
        }

        if (
          presentInParentState.rarity.rarityType === 'rare'
          || presentInParentState.rarity.rarityType === 'interval'
        ) {
          presentInParent['rarity']['minFreq'] = presentInParentState.rarity.rarityIntervalStart;
          presentInParent['rarity']['maxFreq'] = presentInParentState.rarity.rarityIntervalEnd;
        }

        const state = {
          ...variantTypesState?.length && {variantTypes: variantTypesState},
          ...effectTypesState?.length && {effectTypes: effectTypesState},
          ...gendersState?.length && {genders: gendersState},
          ...{inheritanceTypeFilter: inheritanceTypesState},
          ...presentInChildState?.length && {presentInChild: presentInChildState},
          ...studyTypesState?.length && {studyTypes: studyTypesState},
          ...familyIdsState?.length && {familyIds: familyIdsState},
          ...geneSymbolsState?.length && {geneSymbols: geneSymbolsState},
          ...regionsFiltersState?.length && {regions: regionsFiltersState},
          ...{genomicScores: genomicScoresState},
          ...personIdsState?.length && {personIds: personIdsState},
          ...{studyFilters: studyFiltersState},
          uniqueFamilyVariants: uniqueFamilyVariantsFilterState,
          personSetCollection: {...pedigreeSelectorState},
          ...!familyTagsState?.tagIntersection && {tagIntersection: familyTagsState.tagIntersection},
          ...familyTagsState.selectedFamilyTags?.length && {selectedFamilyTags: familyTagsState.selectedFamilyTags},
          ...familyTagsState.deselectedFamilyTags?.length
              && {deselectedFamilyTags: familyTagsState.deselectedFamilyTags},
          ...personFiltersState?.familyFilters?.length && {familyFilters: personFiltersState.familyFilters},
          ...personFiltersState?.personFilters?.length && {personFilters: personFiltersState.personFilters},
          ...geneSetsState.geneSet && { geneSet: {
            geneSet: geneSetsState.geneSet.name,
            geneSetsCollection: geneSetsState.geneSetsCollection.name,
            geneSetsTypes: geneSetsState.geneSetsTypes
          }},
          ...geneScoresState.score && {geneScores: geneScoresState},
          ...presentInParent.presentInParent?.length && {presentInParent: presentInParent},
          ...familyMeasureHistogramsState?.length && { familyMeasureHistograms: familyMeasureHistogramsState.map(s => ({
            source: s.measure,
            isFamily: true,
            histogramType: s.histogramType,
            min: s.rangeStart,
            max: s.rangeEnd,
            values: s.values,
          }))},
          ...personMeasureHistogramsState?.length && { personMeasureHistograms: personMeasureHistogramsState.map(s => ({
            source: s.measure,
            isFamily: false,
            histogramType: s.histogramType,
            min: s.rangeStart,
            max: s.rangeEnd,
            values: s.values,
          }))},
        };
        return state;
      })
    );
  }

  public ngOnDestroy(): void {
    this.loadingService.setLoadingStop();
    this.routerSubscription.unsubscribe();
  }

  public submitQuery(): void {
    this.loadingFinished = false;
    this.showTable = false;
    this.variantsCountDisplay = 'Loading variants...';
    this.loadingService.setLoadingStart();

    this.genotypePreviewVariantsArray = null;
    this.genotypeBrowserState['datasetId'] = this.selectedDataset.id;
    this.legend = this.selectedDataset.personSetCollections
      .getLegend(this.genotypeBrowserState['personSetCollection'] as PersonSetCollection);

    this.queryService.streamingSubject.pipe(take(1)).subscribe(() => {
      this.showTable = true;
      this.loadingService.setLoadingStop();
    });

    this.queryService.streamingFinishedSubject.pipe(take(1)).subscribe(() => {
      this.showTable = true;
      this.loadingFinished = true;
    });

    this.patchState();
    this.genotypePreviewVariantsArray = this.queryService.getGenotypePreviewVariantsByFilter(
      this.selectedDataset,
      this.genotypeBrowserState,
      this.selectedDataset?.genotypeBrowserConfig?.maxVariantsCount !== undefined
        ? this.selectedDataset?.genotypeBrowserConfig?.maxVariantsCount + 1
        : undefined,
      () => {
        this.variantsCountDisplay = this.genotypePreviewVariantsArray?.getVariantsCountFormatted(
          this.selectedDataset?.genotypeBrowserConfig?.maxVariantsCount
        );
      }
    );
  }

  public onSubmit(event): void {
    this.patchState();
    this.genotypeBrowserState['datasetId'] = this.selectedDataset.id;
    const args = clone(this.genotypeBrowserState);
    args['download'] = true;
    /* eslint-disable @typescript-eslint/no-unsafe-member-access */
    event.target.queryData.value = JSON.stringify(args);
    event.target.submit();
    /* eslint-enable */
  }

  private patchState(): void {
    /* FIXME: Hack to remove presentInChild and presentInParent from
      query arguments if they are not enabled (would interfere with results).
      This should be removed when a central converter from state to query args
      is implemented. */
    if (!this.selectedDataset.genotypeBrowserConfig.hasPresentInChild) {
      delete this.genotypeBrowserState['presentInChild'];
    }

    if (!this.selectedDataset.genotypeBrowserConfig.hasPresentInParent) {
      delete this.genotypeBrowserState['presentInParent'];
    }
  }
}
