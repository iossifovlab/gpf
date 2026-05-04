import { Component, Input } from '@angular/core';
import { EnrichmentEffectResult } from '../enrichment-query/enrichment-result';
import { QueryService } from '../query/query.service';
import { BrowserQueryFilter } from 'app/genotype-browser/genotype-browser';
import { Store } from '@ngrx/store';
import { setPedigreeSelector } from 'app/pedigree-selector/pedigree-selector.state';
import { take } from 'rxjs/operators';
import { cloneDeep } from 'lodash';
import { setEffectTypes } from 'app/effect-types/effect-types.state';
import { setGenders } from 'app/gender/gender.state';
import { setVariantTypes } from 'app/variant-types/variant-types.state';
import { setStudyTypes } from 'app/study-types/study-types.state';

@Component({
  selector: '[gpf-enrichment-table-row]',
  templateUrl: './enrichment-table-row.component.html',
  styleUrls: ['./enrichment-table-row.component.css'],
  standalone: false
})
export class EnrichmentTableRowComponent {
  @Input() public label: string;
  @Input() public effectResult: EnrichmentEffectResult;

  public constructor(
    private queryService: QueryService,
    private store: Store,
  ) {}

  public goToQuery(browserQueryFilter: BrowserQueryFilter, skipGenes = false): void {
    // Create new window now because we are in a 'click' event callback, update
    // it's url later. Otherwise this window.open is treated as a pop-up and
    // being blocked by most browsers.
    // https://stackoverflow.com/a/22470171/2316754
    const newWindow = window.open('', '_blank');

    this.store.dispatch(setEffectTypes({effectTypes: browserQueryFilter.effectTypes}));
    this.store.dispatch(setGenders({genders: browserQueryFilter.gender}));
    this.store.dispatch(setVariantTypes({variantTypes: browserQueryFilter.variantTypes}));
    this.store.dispatch(setPedigreeSelector({
      pedigreeSelector: {
        id: browserQueryFilter.personSetCollection.id,
        checkedValues: browserQueryFilter.personSetCollection.checkedValues
      }
    }));
    this.store.dispatch(setStudyTypes({studyTypes: browserQueryFilter['studyTypes']}));

    this.store.subscribe(state => {
      const queryData = cloneDeep(state);

      const datasetId = browserQueryFilter['datasetId'];
      queryData['datasetId'] = datasetId;

      if (skipGenes) {
        delete queryData['geneSymbolsState'];
        delete queryData['geneSetsState'];
        delete queryData['geneScoresState'];
      }
      this.queryService.saveQuery(queryData, 'genotype', 'system')
        .pipe(take(1))
        .subscribe((urlObject: {uuid: string}) => {
          const url = this.queryService.getLoadUrl(urlObject.uuid);
          newWindow.location.assign(url);
        });
    });
  }
}
