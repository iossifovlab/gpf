import { Component } from '@angular/core';

import { Store } from '@ngrx/store';

import { EffectTypesComponent } from '../effect-types/effect-types.component';
import {
  PHENO_TOOL_ALL, PHENO_TOOL_OTHERS,
  PHENO_TOOL_CNV, PHENO_TOOL_LGDS,
  PHENO_TOOL_INITIAL_VALUES
} from './pheno-tool-effect-types';

@Component({
  selector: 'gpf-pheno-tool-effect-types',
  templateUrl: './pheno-tool-effect-types.component.html',
  providers: [{ provide: Store, useClass: Store }]
})
export class PhenoToolEffectTypesComponent extends EffectTypesComponent {
  public phenoToolOthers: Set<string> = PHENO_TOOL_OTHERS;
  public phenoToolCNV: Set<string> = PHENO_TOOL_CNV;
  public phenoToolLGDs: Set<string> = PHENO_TOOL_LGDS;

  public constructor(store: Store) {
    super(store);
    this.effectTypesButtons.set('PHENO_TOOL_ALL', PHENO_TOOL_ALL);
  }

  public selectInitialValues(): void {
    this.setEffectTypes(PHENO_TOOL_INITIAL_VALUES);
  }
}
