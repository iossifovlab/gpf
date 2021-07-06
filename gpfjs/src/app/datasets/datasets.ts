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
      json['values'],
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
    readonly values: Array<string>,
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

    for (const k of Object.keys(json)) {
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

export class PersonFilter {
  static fromJson(json: any): Array<PersonFilter> {
    const filters = [];

    for (const prop in json) {
      if (json.hasOwnProperty(prop)) {
        filters.push(
          new PersonFilter(
            json[prop]['name'],
            json[prop]['from'],
            json[prop]['source'],
            json[prop]['source_type'],
            json[prop]['filter_type'],
            json[prop]['role'],
          )
        );
      }
    }
    return filters;
  }

  constructor(
    readonly name: string,
    readonly from: string,
    readonly source: string,
    readonly sourceType: string,
    readonly filterType: string,
    readonly role: string,
  ) {}
}

export class Column {
  constructor(
    readonly name: string,
    readonly source: string,
    readonly format: string,
  ) {}

  static fromJson(json: any): Column {
    return new Column(
      json['name'],
      json['source'],
      json['format'],
    );
  }
}

export class ColumnGroup {
  constructor(
    readonly name: string,
    readonly columns: Array<Column>,
  ) {}

  static fromJson(json: any): ColumnGroup {
    return new ColumnGroup(
      json['name'],
      json['columns'].map(col => Column.fromJson(col)),
    );
  }
}

export class GenotypeBrowser {

  static tableColumnsFromJson(json: Array<any>): Array<Column | ColumnGroup> {
    const result = [];
    for (const column of json) {
      if ('columns' in column) {
        result.push(ColumnGroup.fromJson(column));
      } else {
        result.push(Column.fromJson(column));
      }
    }
    return result;
  }

  static fromJson(json: any): GenotypeBrowser {
    return new GenotypeBrowser(
      json['has_pedigree_selector'],
      json['has_present_in_child'],
      json['has_present_in_parent'],
      json['has_present_in_role'],
      json['has_family_filters'],
      json['has_family_structure_filter'],
      json['has_person_filters'],
      json['has_study_filters'],
      json['has_study_types'],
      json['has_graphical_preview'],
      GenotypeBrowser.tableColumnsFromJson(json['table_columns']),
      PersonFilter.fromJson(json['person_filters']),
      PersonFilter.fromJson(json['family_filters']),
      json['inheritance_type_filter'],
      json['selected_inheritance_type_filter_values'],
      new Set(json['variant_types']),
      new Set(json['selected_variant_types']),
      json['max_variants_count'],
    );
  }

  constructor(
    readonly hasPedigreeSelector: boolean,
    readonly hasPresentInChild: boolean,
    readonly hasPresentInParent: boolean,
    readonly hasPresentInRole: boolean,
    readonly hasFamilyFilters: boolean,
    readonly hasFamilyStructureFilter: boolean,
    readonly hasPersonFilters: boolean,
    readonly hasStudyFilters: boolean,
    readonly hasStudyTypes: boolean,
    readonly hasGraphicalPreview: boolean,
    readonly tableColumns: Array<Column | ColumnGroup>,
    readonly personFilters: Array<PersonFilter>,
    readonly familyFilters: Array<PersonFilter>,
    readonly inheritanceTypeFilter: string[],
    readonly selectedInheritanceTypeFilterValues: string[],
    readonly variantTypes: Set<string>,
    readonly selectedVariantTypes: Set<string>,
    readonly maxVariantsCount: number,
  ) { }

  get columnIds(): Array<string> {
    const result: Array<string> = [];
    for (const column of this.tableColumns) {
      if ('columns' in column) {
        result.push(...column['columns'].map(col => col['source']));
      } else {
        result.push(column['source']);
      }
    }
    return result;
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

  getLegend(collection: PedigreeSelector): Array<SelectorValue> {
    let result = [];
    const collectionId = collection ? collection.id : this.pedigreeSelectors[0].id;

    for (const ps of this.pedigreeSelectors) {
      if (ps.id === collectionId) {
        result = result.concat(ps.domain);
      }
    }
    result.push({'color': '#E0E0E0', 'id': 'missing-person', 'name': 'missing-person'}); // Default legend value
    return result;
  }
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
      json['parents'],
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
    readonly parents: string[],
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
      json.hasDenovo as boolean,
      json['genome']
    );
  }

  constructor(
    readonly hasDenovo: boolean,
    readonly genome: string,
  ) { }
}

