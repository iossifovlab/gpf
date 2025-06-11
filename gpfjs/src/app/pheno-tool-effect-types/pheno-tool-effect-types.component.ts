import { Component, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { EffectTypesComponent } from '../effect-types/effect-types.component';
import {
  PHENO_TOOL_ALL, PHENO_TOOL_OTHERS,
  PHENO_TOOL_CNV, PHENO_TOOL_LGDS,
  PHENO_TOOL_INITIAL_VALUES
} from './pheno-tool-effect-types';
import { take } from 'rxjs';
import { selectEffectTypes, setEffectTypes } from 'app/effect-types/effect-types.state';

@Component({
  selector: 'gpf-pheno-tool-effect-types',
  templateUrl: './pheno-tool-effect-types.component.html',
  providers: [{ provide: Store, useClass: Store }]
})
export class PhenoToolEffectTypesComponent extends EffectTypesComponent implements OnInit {
  public phenoToolOthers: Set<string> = PHENO_TOOL_OTHERS;
  public phenoToolCNV: Set<string> = PHENO_TOOL_CNV;
  public phenoToolLGDs: Set<string> = PHENO_TOOL_LGDS;
  public effectTypes: Set<string>;

  public ngOnInit(): void {
    this.store.select(selectEffectTypes).pipe(take(1)).subscribe(effectTypesState => {
      if (!effectTypesState) {
        this.effectTypes = PHENO_TOOL_INITIAL_VALUES;
        this.store.dispatch(
          setEffectTypes({effectTypes: [...PHENO_TOOL_INITIAL_VALUES.values()]})
        );
      } else {
        this.effectTypes = new Set(effectTypesState);
      }
      super.ngOnInit();
    });
  }

  public constructor(store: Store) {
    super(store);
    this.effectTypesButtons.set('PHENO_TOOL_ALL', PHENO_TOOL_ALL);
  }
}
