import { Component, Input, OnChanges } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { Selector } from '@ngxs/store';

import { VarianttypesState } from 'app/varianttypes/varianttypes.state';
import { EffecttypesState } from 'app/effecttypes/effecttypes.state';
import { GenderState } from 'app/gender/gender.state';
import { InheritancetypesState } from 'app/inheritancetypes/inheritancetypes.state';
import { PresentInChildState } from 'app/present-in-child/present-in-child.state';
import { PresentInParentState } from 'app/present-in-parent/present-in-parent.state';
import { StudyTypesState } from 'app/study-types/study-types.state';
import { PedigreeSelectorState } from 'app/pedigree-selector/pedigree-selector.state';
import { FamilyTypeFilterState } from 'app/family-type-filter/family-type-filter.state';

export class GenotypeBlockState {
  @Selector([
    VarianttypesState, EffecttypesState, GenderState,
    InheritancetypesState, PresentInChildState, PresentInParentState,
    StudyTypesState, PedigreeSelectorState, FamilyTypeFilterState,
  ])
  static genotypeBlockQueryState(
    variantTypesState, effectTypesState,
    genderState, inheritanceTypesState,
    presentInChildState, presentInParentState,
    studyTypesState, pedigreeSelectorState, familyTypeFilterState
  ) {
    return {
      'variantTypes': variantTypesState['variantTypes'],
      'effectTypes': effectTypesState['effectTypes'],
      'gender': genderState['genders'],
      'inheritanceTypes': inheritanceTypesState['inheritanceTypes'],
      'presentInChild': presentInChildState['presentInChild'],
      'presentInParent': presentInParentState,
      'studyTypes': studyTypesState['studyTypes'],
      'peopleGroup': pedigreeSelectorState,
      'familyTypes': familyTypeFilterState['familyTypes'],
    };
  }
}

@Component({
  selector: 'gpf-genotype-block',
  templateUrl: './genotype-block.component.html',
  styleUrls: ['./genotype-block.component.css'],
})
export class GenotypeBlockComponent implements OnChanges {
  @Input()
  dataset: Dataset;

  inheritanceTypes: Set<string>;
  selectedInheritanceTypes: Set<string>;

  constructor() { }

  ngOnChanges() {
    this.inheritanceTypes = new Set(this.dataset.genotypeBrowserConfig.inheritanceTypeFilter);
    this.selectedInheritanceTypes = new Set(this.dataset.genotypeBrowserConfig.selectedInheritanceTypeFilterValues);
  }
}
