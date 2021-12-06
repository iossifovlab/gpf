import { Component, Input } from '@angular/core';
import { EnrichmentEffectResult, EnrichmentTestResult } from '../enrichment-query/enrichment-result';
import { PValueIntensityPipe } from '../utils/p-value-intensity.pipe';
import { QueryService } from '../query/query.service';
import { BrowserQueryFilter } from 'app/genotype-browser/genotype-browser';
import { Store } from '@ngxs/store';
import { SetEffectTypes } from 'app/effect-types/effect-types.state';
import { SetGender } from 'app/gender/gender.state';
import { SetPedigreeSelector } from 'app/pedigree-selector/pedigree-selector.state';
import { SetStudyTypes } from 'app/study-types/study-types.state';
import { SetVariantTypes } from 'app/variant-types/variant-types.state';
import { take } from 'rxjs/operators';

@Component({
  selector: '[gpf-enrichment-table-row]',
  templateUrl: './enrichment-table-row.component.html',
  styleUrls: ['./enrichment-table-row.component.css']
})
export class EnrichmentTableRowComponent {
  @Input() label: string;
  @Input() effectResult: EnrichmentEffectResult;

  constructor(
    private pValueIntensityPipe: PValueIntensityPipe,
    private queryService: QueryService,
    private store: Store,
  ) {}

  goToQuery(browserQueryFilter: BrowserQueryFilter) {
    // Create new window now because we are in a 'click' event callback, update
    // it's url later. Otherwise this window.open is treated as a pop-up and
    // being blocked by most browsers.
    // https://stackoverflow.com/a/22470171/2316754
    const newWindow = window.open('', '_blank');

    this.store.dispatch([
      new SetEffectTypes(new Set(browserQueryFilter['effectTypes'])),
      new SetGender(browserQueryFilter['gender']),
      new SetPedigreeSelector(
        browserQueryFilter.personSetCollection.id,
        new Set(browserQueryFilter.personSetCollection.checkedValues)
      ),
      new SetStudyTypes(new Set(browserQueryFilter['studyTypes'])),
      new SetVariantTypes(new Set(browserQueryFilter['variantTypes'])),
    ]);

    this.store.selectOnce(state => state).subscribe(state => {
      state['datasetId'] = browserQueryFilter['datasetId'];
      this.queryService.saveQuery(state, 'genotype')
      .pipe(take(1))
      .subscribe(urlObject => {
        const url = this.queryService.getLoadUrlFromResponse(urlObject);
        newWindow.location.assign(url);
      });
    });
  }

  getBackgroundColor(testResult: EnrichmentTestResult) {
    const intensity = this.pValueIntensityPipe.transform(testResult.pvalue);

    if (testResult.overlapped > testResult.expected) {
      return `rgba(255, ${intensity}, ${intensity}, 0.8)`;
    } else {
      return `rgba(${intensity}, ${intensity}, 255, 0.8)`;
    }
  }
}
