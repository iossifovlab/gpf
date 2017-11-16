import { Component, OnInit, Input, Output, EventEmitter, forwardRef } from '@angular/core';

import { Observable } from 'rxjs';

import {
  PHENO_TOOL_ALL, PHENO_TOOL_OTHERS, PHENO_TOOL_CNV, PHENO_TOOL_LGDS,
  PHENO_TOOL_INITIAL_VALUES
} from './pheno-tool-effect-types';
import { QueryStateProvider } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';
import { EffecttypesComponent } from '../effecttypes/effecttypes.component';

@Component({
  selector: 'gpf-pheno-tool-effect-types',
  templateUrl: './pheno-tool-effect-types.component.html',
  providers: [{
    provide: QueryStateProvider,
    useExisting: forwardRef(() => PhenoToolEffectTypesComponent)
  }]
})
export class PhenoToolEffectTypesComponent extends EffecttypesComponent  {
  phenoToolOthers: string[] = PHENO_TOOL_OTHERS;
  phenoToolCNV: string[] = PHENO_TOOL_CNV;
  phenoToolLGDs: string[] = PHENO_TOOL_LGDS;

  constructor(
    stateRestoreService: StateRestoreService
  ) {
    super(stateRestoreService);
    this.effectTypesButtons.set('PHENO_TOOL_ALL', PHENO_TOOL_ALL);
  }

  selectInitialValues() {
    this.selectEffectTypesSet(PHENO_TOOL_INITIAL_VALUES);
  }
}
