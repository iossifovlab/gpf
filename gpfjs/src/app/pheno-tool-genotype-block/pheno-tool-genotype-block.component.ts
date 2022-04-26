import { Component, Input } from '@angular/core';
import { PresentInParentState } from 'app/present-in-parent/present-in-parent.state';
import { EffecttypesState, EffectTypeModel } from 'app/effect-types/effect-types.state';
import { Selector } from '@ngxs/store';

@Component({
  selector: 'gpf-pheno-tool-genotype-block',
  templateUrl: './pheno-tool-genotype-block.component.html',
  styleUrls: ['./pheno-tool-genotype-block.component.css'],
})
export class PhenoToolGenotypeBlockComponent {
  @Input() public variantTypes: Set<string> = new Set();

  @Selector([PresentInParentState.queryStateSelector, EffecttypesState])
  public static phenoToolGenotypeBlockQueryState(presentInParentState, phenoEffectTypesState: EffectTypeModel): object {
    return {
      presentInParent: presentInParentState,
      effectTypes: phenoEffectTypesState.effectTypes,
    };
  }
}
