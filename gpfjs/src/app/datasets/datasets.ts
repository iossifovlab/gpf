import { IdName } from '../common/idname';
import { UserGroup } from '../users-groups/users-groups';
import * as _ from 'lodash';

export const toolPageLinks = {
  datasetDescription: 'dataset-description',
  datasetStatistics: 'dataset-statistics',
  genotypeBrowser: 'genotype-browser',
  phenotypeBrowser: 'phenotype-browser',
  phenotypeTool: 'phenotype-tool',
  enrichmentTool: 'enrichment-tool',
  geneBrowser: 'gene-browser'
};

export class PersonSet extends IdName {
  constructor(
    readonly id: string,
    readonly name: string,
    readonly values: Array<string>,
    readonly color: string,
  ) {
    super(id, name);
  }

  public static fromJson(json: any): PersonSet {
    if (!json) {
      return undefined;
    }

    return new PersonSet(
      json['id'],
      json['name'],
      json['values'],
      json['color'],
    );
  }

  public static fromJsonArray(jsonArray: object[]): Array<PersonSet> {
    if (!jsonArray) {
      return undefined;
    }
    return jsonArray.map((json) => PersonSet.fromJson(json));
  }
}

export class PersonSetCollection extends IdName {
  constructor(
    readonly id: string,
    readonly name: string,
    readonly source: string,
    readonly defaultValue: PersonSet,
    readonly domain: PersonSet[]
  ) {
    super(id, name);
  }

  public static fromJson(json: any): PersonSetCollection[] {
    if (!json) {
      return undefined;
    }

    const collections: PersonSetCollection[] = [];

    for (const k of Object.keys(json)) {
      const v = json[k];
      collections.push(new PersonSetCollection(
        k,
        v['name'],
        k,
        PersonSet.fromJson(v['default']),
        PersonSet.fromJsonArray(v['domain']),
      ));
    }
    return collections;
  }
}

export class PersonSetCollections {
  constructor(
    readonly collections: PersonSetCollection[],
  ) { }

  public static fromJson(json: object): PersonSetCollections {
    return new PersonSetCollections(PersonSetCollection.fromJson(json));
  }

  public getLegend(collection: PersonSetCollection): Array<PersonSet> {
    let result = [];
    const collectionId = collection ? collection.id : this.collections[0].id;

    for (const ps of this.collections) {
      if (ps.id === collectionId) {
        result = result.concat(ps.domain);
      }
    }
    result.push({'color': '#E0E0E0', 'id': 'missing-person', 'name': 'missing-person'}); // Default legend value
    return result;
  }
}

export class PersonFilter {
  constructor(
    readonly name: string,
    readonly from: string,
    readonly source: string,
    readonly sourceType: string,
    readonly filterType: string,
    readonly role: string,
  ) {}

  public static fromJson(json: object): Array<PersonFilter> {
    if (!json) {
      return [];
    }
    return Object.values(json).map(filter => new PersonFilter(
      filter['name'], filter['from'], filter['source'],
      filter['source_type'], filter['filter_type'], filter['role']
    ));
  }
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
      json['columns'].map((col: any) => Column.fromJson(col)),
    );
  }
}

export class GenotypeBrowser {

  static tableColumnsFromJson(json: Array<any>): Array<Column & ColumnGroup> {
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
      new Set(json['inheritance_type_filter']),
      new Set(json['selected_inheritance_type_filter_values']),
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
    readonly tableColumns: Array<Column & ColumnGroup>,
    readonly personFilters: Array<PersonFilter>,
    readonly familyFilters: Array<PersonFilter>,
    readonly inheritanceTypeFilter: Set<string>,
    readonly selectedInheritanceTypeFilterValues: Set<string>,
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
      json['person_set_collections'] ? PersonSetCollections.fromJson(json['person_set_collections']) : null,
      UserGroup.fromJsonArray(json['groups']),
      json['gene_browser'] ? GeneBrowser.fromJson(json['gene_browser']) : null,
      json['has_denovo'],
      json['genome']
    );
  }

  static fromDatasetAndDetailsJson(datasetJson: any, detailsJson: any): Dataset {
    if (!datasetJson || !detailsJson) {
      return undefined;
    }
    return new Dataset(
      datasetJson['id'],
      datasetJson['description'],
      datasetJson['name'],
      datasetJson['parents'],
      datasetJson['access_rights'],
      datasetJson['studies'],
      datasetJson['study_names'],
      datasetJson['study_types'],
      datasetJson['phenotype_data'],
      datasetJson['genotype_browser'],
      datasetJson['phenotype_tool'],
      datasetJson['enrichment_tool'],
      datasetJson['phenotype_browser'],
      datasetJson['common_report'],
      datasetJson['genotype_browser_config'] ? GenotypeBrowser.fromJson(datasetJson['genotype_browser_config']) : null,
      datasetJson['person_set_collections'] ? PersonSetCollections.fromJson(datasetJson['person_set_collections']) : null,
      UserGroup.fromJsonArray(datasetJson['groups']),
      datasetJson['gene_browser'] ? GeneBrowser.fromJson(datasetJson['gene_browser']) : null,
      detailsJson['has_denovo'],
      detailsJson['genome']
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

  get defaultPersonSetCollection(): PersonSetCollection {
    return this.personSetCollections.collections[0];
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
    readonly commonReport: {enabled: boolean},
    readonly genotypeBrowserConfig: GenotypeBrowser,
    readonly personSetCollections: PersonSetCollections,
    readonly groups: UserGroup[],
    readonly geneBrowser: GeneBrowser,
    readonly hasDenovo: boolean,
    readonly genome: string
  ) {
    super(id, name);
  }
}
