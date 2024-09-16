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
import { State } from 'app/users/tmp.state';
import { setFamilyTags } from 'app/family-tags/family-tags.state';
import { setPresentInChild } from 'app/present-in-child/present-in-child.state';
import { setPresentInParent } from 'app/present-in-parent/present-in-parent.state';
import { setGeneSetsValues } from 'app/gene-sets/gene-sets.state';
import { setGeneSymbols } from 'app/gene-symbols/gene-symbols.state';
import { setGeneScore } from 'app/gene-scores/gene-scores.state';
import { setRegionsFilters } from 'app/regions-filter/regions-filter.state';
import { setStudyFilters } from 'app/study-filters/study-filters.state';
import { setGenomicScores } from 'app/genomic-scores-block/genomic-scores-block.state';
import { setUniqueFamilyVariantsFilter } from 'app/unique-family-variants-filter/unique-family-variants-filter.state';
import { setFamilyFilters, setPersonFilters } from 'app/person-filters/person-filters.state';
import { setPhenoToolMeasure } from 'app/pheno-tool-measure/pheno-tool-measure.state';

const PAGE_TYPE_TO_NAVIGATE = {
  genotype: (datasetId: string): string[] => ['datasets', datasetId, 'genotype-browser'],
  phenotype: (datasetId: string): string[] => ['datasets', datasetId, 'phenotype-browser'],
  enrichment: (datasetId: string): string[] => ['datasets', datasetId, 'enrichment-tool'],
  phenotool: (datasetId: string): string[] => ['datasets', datasetId, 'phenotype-tool']
};

@Component({
  selector: 'gpf-load-query',
  templateUrl: './load-query.component.html',
  styleUrls: ['./load-query.component.css']
})
export class LoadQueryComponent implements OnInit {
  public constructor(
    private store: Store,
    private queryService: QueryService,
    private route: ActivatedRoute,
    private router: Router
  ) { }

  public ngOnInit(): void {
    this.route.params.subscribe(
      params => {
        if (!params['uuid']) {
          this.router.navigate(['/']);
        } else {
          this.loadQuery(params['uuid'] as string);
        }
      });
  }

  private loadQuery(uuid: string): void {
    this.queryService.loadQuery(uuid)
      .pipe(take(1))
      .subscribe(response => {
        const queryData = response['data'] as State;
        const page = response['page'] as string;
        this.restoreQuery(queryData, page);
      });
  }

  private restoreQuery(state: State, page: string): void {
    if (page in PAGE_TYPE_TO_NAVIGATE) {
      const navigationParams: string[] = PAGE_TYPE_TO_NAVIGATE[page](state['datasetId']);
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
      this.store.dispatch(setGeneScore({
        score: state.geneScores.score,
        rangeEnd: state.geneScores.rangeEnd,
        rangeStart: state.geneScores.rangeStart,
      }));
      this.store.dispatch(setRegionsFilters({regionsFilter: state.regionsFilter}));
      this.store.dispatch(setStudyFilters({studyFilters: state.studyFilters}));
      this.store.dispatch(setGenomicScores({genomicScores: state.genomicScores}));
      this.store.dispatch(
        setUniqueFamilyVariantsFilter({uniqueFamilyVariantsFilter: state.uniqueFamilyVariantsFilter})
      );
      this.store.dispatch(setFamilyFilters({familyFilters: state.personFilters.familyFilters}));
      this.store.dispatch(setPersonFilters({personFilters: state.personFilters.personFilters}));
      this.store.dispatch(setPhenoToolMeasure({phenoToolMeasure: state.phenoToolMeasure}));
      this.router.navigate(navigationParams);
    }
  }
}
