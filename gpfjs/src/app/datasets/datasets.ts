import { IdName } from '../common/idname';
import { UserGroup } from '../users-groups/users-groups';
import * as _ from 'lodash';

export class SelectorValue extends IdName {
  static fromJson(json: any): SelectorValue {
    if (!json) {
      return undefined;
    }

    return new SelectorValue(
      json['id'],
      json['name'],
      json['color'],
    );
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<SelectorValue> {
    if (!jsonArray) {
      return undefined;
    }
    return jsonArray.map((json) => SelectorValue.fromJson(json));
  }

  constructor(
    readonly id: string,
    readonly name: string,
    readonly color: string,
  ) {
    super(id, name);
  }
}

export class PedigreeSelector extends IdName {
  static fromJson(json: any): PedigreeSelector[] {
    if (!json) {
      return undefined;
    }

    const pedigreeSelectors: PedigreeSelector[] = [];

    for (const k in json) {
      const v = json[k];
      pedigreeSelectors.push(new PedigreeSelector(
        k,
        v['name'],
        k,
        SelectorValue.fromJson(v['default']),
        SelectorValue.fromJsonArray(v['domain']),
      ));
    }

    return pedigreeSelectors;

  }

  constructor(
    readonly id: string,
    readonly name: string,
    readonly source: string,
    readonly defaultValue: SelectorValue,
    readonly domain: SelectorValue[]
  ) {
    super(id, name);
  }
}

export class PresentInRole {
  static fromJson(json: any): PresentInRole {
    if (!json) {
      return undefined;
    }

    return new PresentInRole(
      json['id'],
      json['name'],
      json['roles'],
    );
  }
  static fromJsonArray(jsonArray: Array<Object>): Array<PresentInRole> {
    if (!jsonArray) {
      return undefined;
    }

    return jsonArray.map((json) => PresentInRole.fromJson(json));
  }

  constructor(
    readonly id: string,
    readonly name: string,
    readonly roles: string[]
  ) {
  }
}

export class AdditionalColumnSlot {
  static fromJson(json: any): Array<AdditionalColumnSlot> {
    const res = [];
    for (const column_id in json) {
      const column = json[column_id];
      res.push(new AdditionalColumnSlot(column_id, column['name'], column['source'], column['format']));
    }
    return res;
  }

  constructor(
    readonly id: string,
    readonly name: string,
    readonly source: string,
    readonly format: string,
  ) {}
}

export class AdditionalColumn {
  static fromJson(json: any): Array<AdditionalColumn> {
    const res = [];
    for (const column_id in json) {
      const column = json[column_id];
      res.push(new AdditionalColumn(column_id, column['name'], column['source'], AdditionalColumnSlot.fromJson(column['slots'])));
    }
    return res;
  }

  constructor(
    readonly id: string,
    readonly name: string,
    readonly source: string,
    readonly slots: Array<AdditionalColumnSlot>
  ) {}
}

export class PhenoFilter {
  static fromJson(json: any): Array<PhenoFilter> {
    const filters = [];

    for (const prop in json) {
      if (json.hasOwnProperty(prop)) {
        filters.push(
          new PhenoFilter(
            json[prop]['name'],
            json[prop]['measure_type'],
            json[prop]['role'],
            json[prop]['filter_type'],
            json[prop]['measure'],
            json[prop]['domain']
          )
        );
      }
    }
    return filters;
  }

  constructor(
    readonly name: string,
    readonly measureType: string,
    readonly role: string,
    readonly filterType: string,
    readonly measure: string,
    readonly domain: Array<string>
  ) {}
}

export class GenotypeBrowser {

  readonly columns: Array<AdditionalColumn>;

  static fromJson(json: any): GenotypeBrowser {
    return new GenotypeBrowser(
      json['has_pedigree_selector'],
      json['has_present_in_child'],
      json['has_present_in_parent'],
      json['has_present_in_role'],
      json['has_family_filters'],
      json['has_study_filters'],
      json['has_study_types'],
      json['has_graphical_preview'],
      json['preview_columns'],
      [...AdditionalColumn.fromJson(json['columns'])],
      PhenoFilter.fromJson(json['pheno_filters']),
      PhenoFilter.fromJson(json['family_filters']),
      PresentInRole.fromJsonArray(json['present_in_role']),
      json['inheritance_type_filter'],
      json['selected_inheritance_type_filter_values'],
      new Set(json['variant_types']),
      new Set(json['selected_variant_types']),
    );
  }

  constructor(
    readonly hasPedigreeSelector: boolean,
    readonly hasPresentInChild: boolean,
    readonly hasPresentInParent: boolean,
    readonly hasPresentInRole: boolean,
    readonly hasFamilyFilters: boolean,
    readonly hasStudyFilters: boolean,
    readonly hasStudyTypes: boolean,
    readonly hasGraphicalPreview: boolean,
    readonly previewColumnsIds: string[],
    readonly allColumns: Array<AdditionalColumn>,
    readonly phenoFilters: Array<PhenoFilter>,
    readonly familyFilters: Array<PhenoFilter>,
    readonly presentInRole: PresentInRole[],
    readonly inheritanceTypeFilter: string[],
    readonly selectedInheritanceTypeFilterValues: string[],
    readonly variantTypes: Set<string>,
    readonly selectedVariantTypes: Set<string>,
  ) {
    this.columns = _.filter(this.allColumns,
      (column: AdditionalColumn) => this.previewColumnsIds.indexOf(column.id) > -1);
  }
}

export class GeneBrowser {
  static fromJson(json: any): GeneBrowser {
    return new GeneBrowser(
      json['enabled'],
      json['frequency_column'],
      json['frequency_name'],
      json['effect_column'],
      json['location_column'],
      json['domain_min'],
      json['domain_max'],
    );
  }

  constructor(
    readonly enabled: boolean,
    readonly frequencyColumn: string,
    readonly frequencyName: string,
    readonly effectColumn: string,
    readonly locationColumn: string,
    readonly domainMin: number,
    readonly domainMax: number,
  ) { }
}

export class PeopleGroup {

  static fromJson(json: any): PeopleGroup {
    return new PeopleGroup(
      PedigreeSelector.fromJson(json)
    );
  }

  constructor(
    readonly pedigreeSelectors: PedigreeSelector[],
  ) { }
}

export class Dataset extends IdName {
  static fromJson(json: any): Dataset {
    if (!json) {
      return undefined;
    }
    return new Dataset(
      json['id'],
      json['description'],
      json['name'],
      json['access_rights'],
      json['studies'],
      json['study_names'],
      json['study_types'],
      json['phenotype_data'],
      json['genotype_browser'],
      json['phenotype_tool'],
      json['enrichment_tool'],
      json['phenotype_browser'],
      json['common_report'],
      json['genotype_browser_config'] ? GenotypeBrowser.fromJson(json['genotype_browser_config']) : null,
      json['person_set_collections'] ? PeopleGroup.fromJson(json['person_set_collections']) : null,
      UserGroup.fromJsonArray(json['groups']),
      json['gene_browser'] ? GeneBrowser.fromJson(json['gene_browser']) : null,
    );
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<Dataset> {
    if (!jsonArray) {
      return undefined;
    }
    return jsonArray.map((json) => Dataset.fromJson(json));
  }

  getDefaultGroups() {
    return ['any_dataset', this.id];
  }

  constructor(
    readonly id: string,
    readonly description: string,
    readonly name: string,
    readonly accessRights: boolean,
    readonly studies: string[],
    readonly studyNames: string[],
    readonly studyTypes: string[],
    readonly phenotypeData: string,
    readonly genotypeBrowser: boolean,
    readonly phenotypeTool: boolean,
    readonly enrichmentTool: boolean,
    readonly phenotypeBrowser: boolean,
    readonly commonReport: boolean,
    readonly genotypeBrowserConfig: GenotypeBrowser,
    readonly peopleGroupConfig: PeopleGroup,
    readonly groups: UserGroup[],
    readonly geneBrowser: GeneBrowser,
  ) {
    super(id, name);
  }
}

export class DatasetDetails {
  static fromJson(json: any): DatasetDetails {
    return new DatasetDetails(
      json.hasDenovo as boolean
    );
  }

  constructor(
    readonly hasDenovo: boolean
  ) { }
}

