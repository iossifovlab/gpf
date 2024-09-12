/* eslint-disable max-len */
import { createReducer, on } from '@ngrx/store';
import { GeneProfiles, initialState as geneProfilesInitialState } from 'app/gene-profiles-table/gene-profiles-table.state';
import { GeneScoresState, initialState as geneScoresInitialState } from 'app/gene-scores/gene-scores.state';
import { PedigreeSelector, initialState as pedigreeSelectorInitialState } from 'app/pedigree-selector/pedigree-selector.state';
import { PhenoToolMeasureState, initialState as phenoToolMeasureInitialState } from 'app/pheno-tool-measure/pheno-tool-measure.state';
import { PresentInParent, initialState as presentInParentInitialState } from 'app/present-in-parent/present-in-parent.state';
import { initialState as genomicScoresInitialState } from 'app/genomic-scores-block/genomic-scores-block.state';
import { initialState as familyTagsInitialState } from 'app/family-tags/family-tags.state';
import { initialState as personIdsInitialState } from 'app/person-ids/person-ids.state';
import { initialState as personFiltersInitialState } from 'app/person-filters/person-filters.state';
import { initialState as studyFiltersInitialState } from 'app/study-filters/study-filters.state';
import { initialState as effectTypesInitialState } from 'app/effect-types/effect-types.state';
import { initialState as genderInitialState } from 'app/gender/gender.state'
import { initialState as variantTypesInitialState } from 'app/variant-types/variant-types.state';
import { initialState as inheritanceTypesInitialState } from 'app/inheritancetypes/inheritancetypes.state';
import { EnrichmentModels, initialState as enrichmentModelsInitialState } from 'app/enrichment-models/enrichment-models.state';
import { GeneSetsState, initialState as geneSetsInitialState } from 'app/gene-sets/gene-sets.state';
import { initialState as geneSymbolsInitialState } from 'app/gene-symbols/gene-symbols.state';
import { initialState as presentInChildInitialState } from 'app/present-in-child/present-in-child.state';
import { initialState as regionsFilterInitialState } from 'app/regions-filter/regions-filter.state';
import { initialState as uniqueFamilyVariantsInitialState } from 'app/unique-family-variants-filter/unique-family-variants-filter.state';
import { initialState as familyTypeFilterInitialState } from 'app/family-type-filter/family-type-filter.state';
import { initialState as studyTypesInitialState } from 'app/study-types/study-types.state';
import { initialState as familyIdsInitialState } from 'app/family-ids/family-ids.state';
import { GenomicScoreInterface } from 'app/genotype-browser/genotype-browser';
import { PersonFilterState } from 'app/person-filters/person-filters';
import { FamilyTags } from 'app/family-tags/family-tags';
import { cloneDeep } from 'lodash';
import { reset } from './state-actions';

export interface State {
  errors: string[];
  familyIds: string[];
  familyTags: FamilyTags;
  personIds: string[];
  personFilters: { familyFilters: PersonFilterState[]; personFilters: PersonFilterState[] };
  studyFilters: string[];
  effectTypes: string[];
  genders: string[];
  variantTypes: string[];
  inheritanceTypes: string[];
  enrichmentModels: EnrichmentModels;
  geneSets: GeneSetsState;
  geneScores: GeneScoresState;
  geneSymbols: string[];
  presentInChild: string[];
  presentInParent: PresentInParent;
  phenoToolMeasure: PhenoToolMeasureState;
  pedigreeSelector: PedigreeSelector;
  geneProfiles: GeneProfiles;
  regionsFilter: string[];
  genomicScores: GenomicScoreInterface[];
  uniqueFamilyVariantsFilter: boolean;
  familyTypeFilter: string[];
  studyTypes: string[];
}

export const initialState: State = {
  errors: [],
  familyIds: familyIdsInitialState,
  familyTags: familyTagsInitialState,
  personIds: personIdsInitialState,
  personFilters: personFiltersInitialState,
  studyFilters: studyFiltersInitialState,
  effectTypes: effectTypesInitialState,
  genders: genderInitialState,
  variantTypes: variantTypesInitialState,
  inheritanceTypes: inheritanceTypesInitialState,
  enrichmentModels: enrichmentModelsInitialState,
  geneSets: geneSetsInitialState,
  geneScores: geneScoresInitialState,
  geneSymbols: geneSymbolsInitialState,
  presentInChild: presentInChildInitialState,
  presentInParent: presentInParentInitialState,
  phenoToolMeasure: phenoToolMeasureInitialState,
  pedigreeSelector: pedigreeSelectorInitialState,
  geneProfiles: geneProfilesInitialState,
  regionsFilter: regionsFilterInitialState,
  genomicScores: genomicScoresInitialState,
  uniqueFamilyVariantsFilter: uniqueFamilyVariantsInitialState,
  familyTypeFilter: familyTypeFilterInitialState,
  studyTypes: studyTypesInitialState,
};

export const reducer = createReducer(
  initialState,
  on(reset, () => cloneDeep(initialState))
);
