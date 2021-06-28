import { Component, OnInit, Input, Output, EventEmitter, forwardRef } from '@angular/core';

import { Observable } from 'rxjs';
import { Store } from '@ngxs/store';

import {
  PHENO_TOOL_ALL, PHENO_TOOL_OTHERS, PHENO_TOOL_CNV, PHENO_TOOL_LGDS,
  PHENO_TOOL_INITIAL_VALUES
} from './pheno-tool-effect-types';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';
import { EffecttypesComponent } from '../effecttypes/effecttypes.component';

@Component({
  selector: 'gpf-pheno-tool-effect-types',
  templateUrl: './pheno-tool-effect-types.component.html',
  providers: [{
    provide: Store,
    useExisting: forwardRef(() => PhenoToolEffectTypesComponent)
  }]
})
export class PhenoToolEffectTypesComponent extends EffecttypesComponent  {
  phenoToolOthers: Set<string> = PHENO_TOOL_OTHERS;
  phenoToolCNV: Set<string> = PHENO_TOOL_CNV;
  phenoToolLGDs: Set<string> = PHENO_TOOL_LGDS;

  selectInitialValues() {
    this.setEffectTypes(PHENO_TOOL_INITIAL_VALUES);
  }
}
