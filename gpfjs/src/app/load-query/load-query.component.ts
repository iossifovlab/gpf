import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { QueryService } from '../query/query.service';
import { take } from 'rxjs/operators';
import { Store } from '@ngrx/store';
import { setEffectTypes } from 'app/effect-types/effect-types.state';
import { reset } from 'app/users/state-actions';
import { setGenders } from 'app/gender/gender.state';
import { setPedigreeSelector } from 'app/pedigree-selector/pedigree-selector.state';
import { setVariantTypes } from 'app/variant-types/variant-types.state';
import { State } from 'app/utils/gpf.state';
import { setFamilyTags } from 'app/family-tags/family-tags.state';
import { setPresentInChild } from 'app/present-in-child/present-in-child.state';
import { setPresentInParent } from 'app/present-in-parent/present-in-parent.state';
import { setGeneSetsValues } from 'app/gene-sets/gene-sets.state';
import { setGeneSymbols } from 'app/gene-symbols/gene-symbols.state';
import { setGeneScoreCategorical, setGeneScoreContinuous } from 'app/gene-scores/gene-scores.state';
import { setRegionsFilters } from 'app/regions-filter/regions-filter.state';
import { setStudyFilters } from 'app/study-filters/study-filters.state';
import { setGenomicScores } from 'app/genomic-scores-block/genomic-scores-block.state';
import { setUniqueFamilyVariantsFilter } from 'app/unique-family-variants-filter/unique-family-variants-filter.state';
import { setFamilyFilters, setPersonFilters } from 'app/person-filters/person-filters.state';
import { setPhenoToolMeasure } from 'app/pheno-tool-measure/pheno-tool-measure.state';
import { setFamilyIds } from 'app/family-ids/family-ids.state';
import { setPersonIds } from 'app/person-ids/person-ids.state';
import {
  setFamilyMeasureHistograms,
  setPersonMeasureHistograms
} from 'app/person-filters-selector/measure-histogram.state';
import { setAllZygosityFilters } from 'app/zygosity-filters/zygosity-filter.state';
import { setInheritanceTypes } from 'app/inheritancetypes/inheritancetypes.state';

const PAGE_TYPE_TO_NAVIGATE = {
  genotype: 'genotype-browser',
  phenotype: 'phenotype-browser',
  enrichment: 'enrichment-tool',
  phenotool: 'phenotype-tool',
};

@Component({
  selector: 'gpf-load-query',
  templateUrl: './load-query.component.html',
  styleUrls: ['./load-query.component.css'],
  standalone: false
})
export class LoadQueryComponent implements OnInit {
  public constructor(
    private store: Store,
    private queryService: QueryService,
    private route: ActivatedRoute,
    private router: Router
  ) { }

  public ngOnInit(): void {
    const uuid: string = this.route.snapshot.params.uuid as string;
    const preview: boolean = this.route.snapshot.queryParams.preview === 'true';
    if (!uuid) {
      this.router.navigate(['/']);
    } else {
      this.loadQuery(uuid, preview);
    }
  }

  private loadQuery(uuid: string, preview: boolean = false): void {
    this.queryService.loadQuery(uuid)
      .pipe(take(1))
      .subscribe(response => {
        this.restoreQuery(
          response['data'] as State,
          response['page'] as string,
          preview,
        );
      });
  }

  private restoreQuery(state: State, page: string, preview: boolean = false): void {
    if (page in PAGE_TYPE_TO_NAVIGATE) {
      const navigationParams: string[] = [
        'datasets',
        state['datasetId'],
        PAGE_TYPE_TO_NAVIGATE[page] as string
      ];
      this.store.dispatch(reset());

      this.store.dispatch(setEffectTypes({effectTypes: state.effectTypes}));
      this.store.dispatch(setGenders({genders: state.genders}));
      this.store.dispatch(setPedigreeSelector({pedigreeSelector: state.pedigreeSelector}));
      this.store.dispatch(setVariantTypes({variantTypes: state.variantTypes}));
      this.store.dispatch(setFamilyTags({
        selectedFamilyTags: state.familyTags.selectedFamilyTags,
        deselectedFamilyTags: state.familyTags.deselectedFamilyTags,
        tagIntersection: state.familyTags.tagIntersection,
      }));
      this.store.dispatch(setPresentInChild({presentInChild: state.presentInChild}));
      this.store.dispatch(setPresentInParent({presentInParent: state.presentInParent}));
      this.store.dispatch(setGeneSetsValues({
        geneSet: state.geneSets.geneSet,
        geneSetsCollection: state.geneSets.geneSetsCollection,
        geneSetsTypes: state.geneSets.geneSetsTypes
      }));
      this.store.dispatch(setGeneSymbols({geneSymbols: state.geneSymbols}));
      this.store.dispatch(setRegionsFilters({regionsFilter: state.regionsFilter}));
      this.store.dispatch(setStudyFilters({studyFilters: state.studyFilters}));
      this.store.dispatch(setGenomicScores({genomicScores: state.genomicScores}));
      this.store.dispatch(
        setUniqueFamilyVariantsFilter({uniqueFamilyVariantsFilter: state.uniqueFamilyVariantsFilter})
      );
      this.store.dispatch(setFamilyFilters({familyFilters: state.personFilters.familyFilters}));
      this.store.dispatch(setPersonFilters({personFilters: state.personFilters.personFilters}));
      this.store.dispatch(setPhenoToolMeasure({phenoToolMeasure: state.phenoToolMeasure}));
      this.store.dispatch(setFamilyIds({familyIds: state.familyIds}));
      this.store.dispatch(setPersonIds({personIds: state.personIds}));
      this.store.dispatch(setFamilyMeasureHistograms({familyMeasureHistograms: state.familyMeasureHistograms}));
      this.store.dispatch(setPersonMeasureHistograms({personMeasureHistograms: state.personMeasureHistograms}));
      this.store.dispatch(setAllZygosityFilters({ zygosityFilters: state.zygosityFilter }));

      if (state.geneScores.histogramType === 'categorical') {
        this.store.dispatch(setGeneScoreCategorical({
          score: state.geneScores.score,
          values: state.geneScores.values,
          categoricalView: state.geneScores.categoricalView,
        }));
      } else if (state.geneScores.histogramType === 'continuous') {
        this.store.dispatch(setGeneScoreContinuous({
          score: state.geneScores.score,
          rangeEnd: state.geneScores.rangeEnd,
          rangeStart: state.geneScores.rangeStart,
        }));
      }

      if (state.inheritanceTypes) {
        this.store.dispatch(setInheritanceTypes({inheritanceTypes: state.inheritanceTypes}));
      }

      const extras = {};
      if (preview) {
        extras['queryParams'] = { preview: true };
      }

      this.router.navigate(navigationParams, extras);
    }
  }
}
