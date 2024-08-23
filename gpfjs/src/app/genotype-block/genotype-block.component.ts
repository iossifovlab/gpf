import { Component, Input, OnInit } from '@angular/core';
import { Dataset } from '../datasets/datasets';

import { InheritancetypesState, InheritancetypesModel } from 'app/inheritancetypes/inheritancetypes.state';
import { PresentInChildState, PresentInChildModel } from 'app/present-in-child/present-in-child.state';
import { PresentInParentState } from 'app/present-in-parent/present-in-parent.state';
import { StudyTypesState, StudyTypesModel } from 'app/study-types/study-types.state';
import { PedigreeSelectorState, PedigreeSelectorModel } from 'app/pedigree-selector/pedigree-selector.state';
import { FamilyTypeFilterState, FamilyTypeFilterModel } from 'app/family-type-filter/family-type-filter.state';

@Component({
  selector: 'gpf-genotype-block',
  templateUrl: './genotype-block.component.html',
  styleUrls: ['./genotype-block.component.css'],
})
export class GenotypeBlockComponent implements OnInit {
  @Input() public dataset: Dataset;
  public variantTypesSet = new Set<string>();
  public selectedVariantTypesSet = new Set<string>();
  public inheritanceTypeFilterSet = new Set<string>();
  public selectedInheritanceTypeFilterValuesSet = new Set<string>();

  public ngOnInit(): void {
    this.variantTypesSet = new Set(this.dataset.genotypeBrowserConfig.variantTypes);
    this.selectedVariantTypesSet = new Set(this.dataset.genotypeBrowserConfig.selectedVariantTypes);
    this.inheritanceTypeFilterSet = new Set(this.dataset.genotypeBrowserConfig.inheritanceTypeFilter);
    this.selectedInheritanceTypeFilterValuesSet =
      new Set(this.dataset.genotypeBrowserConfig.selectedInheritanceTypeFilterValues);
  }
  // @Selector([
  //   VarianttypesState, EffecttypesState, GenderState,
  //   InheritancetypesState, PresentInChildState,
  //   PresentInParentState.queryStateSelector, StudyTypesState,
  //   PedigreeSelectorState, FamilyTypeFilterState,
  // ])
  // public static genotypeBlockQueryState(
  //   variantTypesState: VarianttypeModel,
  //   effectTypesState: EffectTypeModel,
  //   genderState: GenderModel,
  //   inheritanceTypesState: InheritancetypesModel,
  //   presentInChildState: PresentInChildModel,
  //   presentInParentState: PresentInParentState,
  //   studyTypesState: StudyTypesModel,
  //   pedigreeSelectorState: PedigreeSelectorModel,
  //   familyTypeFilterState: FamilyTypeFilterModel,
  // ): object {
  //   return {
  //     variantTypes: variantTypesState.variantTypes,
  //     effectTypes: effectTypesState.effectTypes,
  //     gender: genderState.genders,
  //     inheritanceTypeFilter: inheritanceTypesState.inheritanceTypes,
  //     presentInChild: presentInChildState.presentInChild,
  //     presentInParent: presentInParentState,
  //     studyTypes: studyTypesState.studyTypes,
  //     personSetCollection: pedigreeSelectorState,
  //     familyTypes: familyTypeFilterState.familyTypes,
  //   };
  // }
}
