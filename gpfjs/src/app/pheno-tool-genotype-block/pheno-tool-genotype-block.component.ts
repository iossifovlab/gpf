import { Component, Input, OnInit } from '@angular/core';
import { PresentInParentState, PresentInParentModel } from 'app/present-in-parent/present-in-parent.state';
import { EffecttypesState, EffectTypeModel } from 'app/effecttypes/effecttypes.state';
import { Selector } from '@ngxs/store';

@Component({
  selector: 'gpf-pheno-tool-genotype-block',
  templateUrl: './pheno-tool-genotype-block.component.html',
  styleUrls: ['./pheno-tool-genotype-block.component.css'],
})
export class PhenoToolGenotypeBlockComponent {

  @Input()
  variantTypes: Set<string> = new Set([]);

  @Selector([PresentInParentState.queryStateSelector, EffecttypesState])
  static phenoToolGenotypeBlockQueryState(
    presentInParentState,
    phenoEffectTypesState: EffectTypeModel,
  ) {
    return {
      'presentInParent': presentInParentState,
      'effectTypes': phenoEffectTypesState.effectTypes,
    };
  }

}
