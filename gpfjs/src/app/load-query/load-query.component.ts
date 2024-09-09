import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { QueryService } from '../query/query.service';
import { take } from 'rxjs/operators';
import { Store } from '@ngrx/store';
import { setEffectTypes } from 'app/effect-types/effect-types.state';
import { logout } from 'app/users/actions';
import { setGenders } from 'app/gender/gender.state';
import { setPedigreeSelector } from 'app/pedigree-selector/pedigree-selector.state';
import { setVariantTypes } from 'app/variant-types/variant-types.state';
import { State } from 'app/users/tmp.state';

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
      console.log(state);
      const navigationParams: string[] = PAGE_TYPE_TO_NAVIGATE[page](state['datasetId']);
      this.store.dispatch(logout());

      this.store.dispatch(setEffectTypes({effectTypes: state.effectTypes}));
      this.store.dispatch(setGenders({genders: state.genders}));
      this.store.dispatch(setPedigreeSelector({pedigreeSelector: state.pedigreeSelector}))
      this.store.dispatch(setVariantTypes({variantTypes: state.variantTypes}));

      this.router.navigate(navigationParams);
    }
  }
}
