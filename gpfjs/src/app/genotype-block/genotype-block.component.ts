import { Component, Input } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { Selector } from '@ngxs/store';

import { VarianttypesState, VarianttypeModel } from 'app/varianttypes/varianttypes.state';
import { EffecttypesState, EffectTypeModel } from 'app/effecttypes/effecttypes.state';
import { GenderState, GenderModel } from 'app/gender/gender.state';
import { InheritancetypesState, InheritancetypesModel } from 'app/inheritancetypes/inheritancetypes.state';
import { PresentInChildState, PresentInChildModel } from 'app/present-in-child/present-in-child.state';
import { PresentInParentState, PresentInParentModel } from 'app/present-in-parent/present-in-parent.state';
import { StudyTypesState, StudyTypesModel } from 'app/study-types/study-types.state';
import { PedigreeSelectorState, PedigreeSelectorModel } from 'app/pedigree-selector/pedigree-selector.state';
import { FamilyTypeFilterState, FamilyTypeFilterModel } from 'app/family-type-filter/family-type-filter.state';

@Component({
  selector: 'gpf-genotype-block',
  templateUrl: './genotype-block.component.html',
  styleUrls: ['./genotype-block.component.css'],
})
export class GenotypeBlockComponent {
  @Input()
  dataset: Dataset;

  constructor() { }

  @Selector([
    VarianttypesState, EffecttypesState, GenderState,
    InheritancetypesState, PresentInChildState,
    PresentInParentState.queryStateSelector, StudyTypesState,
    PedigreeSelectorState, FamilyTypeFilterState,
  ])
  static genotypeBlockQueryState(
    variantTypesState: VarianttypeModel,
    effectTypesState: EffectTypeModel,
    genderState: GenderModel,
    inheritanceTypesState: InheritancetypesModel,
    presentInChildState: PresentInChildModel,
    presentInParentState,
    studyTypesState: StudyTypesModel,
    pedigreeSelectorState: PedigreeSelectorModel,
    familyTypeFilterState: FamilyTypeFilterModel,
  ) {
    return {
      'variantTypes': variantTypesState.variantTypes,
      'effectTypes': effectTypesState.effectTypes,
      'gender': genderState.genders,
      'inheritanceTypeFilter': inheritanceTypesState.inheritanceTypes,
      'presentInChild': presentInChildState.presentInChild,
      'presentInParent': presentInParentState,
      'studyTypes': studyTypesState.studyTypes,
      'peopleGroup': pedigreeSelectorState,
      'familyTypes': familyTypeFilterState.familyTypes,
    };
  }
}
