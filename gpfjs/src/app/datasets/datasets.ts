import { IdName } from '../common/idname';
import { UserGroup } from '../users-groups/users-groups';

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
  public constructor(
    public readonly id: string,
    public readonly name: string,
    // public readonly values: Array<string>,
    public readonly color: string,
  ) {
    super(id, name);
  }

  public static fromJson(json: object): PersonSet {
    if (!json) {
      return undefined;
    }

    return new PersonSet(
      json['id'] as string,
      json['name'] as string,
      // json['values'] as string[],
      json['color'] as string,
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
  public constructor(
    public readonly id: string,
    public readonly name: string,
    // public readonly source: string,
    // public readonly defaultValue: PersonSet,
    public readonly domain: PersonSet[]
  ) {
    super(id, name);
    // domain.push(defaultValue);
  }

  public static fromJson(json: object): PersonSetCollection[] {
    if (!json) {
      return undefined;
    }

    const collections: PersonSetCollection[] = [];

    for (const k of Object.keys(json)) {
      const v = json[k] as string;
      collections.push(new PersonSetCollection(
        k,
        v['name'] as string,
        // k,
        // PersonSet.fromJson(v['default'] as object),
        PersonSet.fromJsonArray(v['domain'] as object[]),
      ));
    }
    return collections;
  }
}

export class PersonSetCollections {
  public constructor(
    public readonly collections: PersonSetCollection[],
  ) { }

  public static fromJson(json: object): PersonSetCollections {
    return new PersonSetCollections(PersonSetCollection.fromJson(json));
  }

  public getLegend(collection: PersonSetCollection): Array<PersonSet> {
    let result: PersonSet[] = [];
    const collectionId = collection ? collection.id : this.collections[0].id;

    for (const ps of this.collections) {
      if (ps.id === collectionId) {
        result = result.concat(ps.domain);
      }
    }
    result.push({color: '#E0E0E0', id: 'missing-person', name: 'missing-person'} as PersonSet); // Default legend value
    return result;
  }
}

export class PersonFilter {
  public constructor(
    public readonly name: string,
    public readonly from: string,
    public readonly source: string,
    public readonly sourceType: string,
    public readonly filterType: string,
    public readonly role: string,
  ) {}

  public static fromJson(json: object): Array<PersonFilter> {
    if (!json) {
      return [];
    }
    return Object.values(json).map((filter: object) => new PersonFilter(
      filter['name'] as string, filter['from'] as string, filter['source'] as string,
      filter['source_type'] as string, filter['filter_type'] as string, filter['role'] as string
    ));
  }
}

export class Column {
  public constructor(
    public readonly name: string,
    public readonly source: string,
    public readonly format: string,
  ) {}

  public static fromJson(json: object): Column {
    return new Column(json['name'] as string, json['source'] as string, json['format'] as string);
  }
}

export class ColumnGroup {
  public constructor(
    public readonly name: string,
    public readonly columns: Array<Column>,
  ) {}

  public static fromJson(json: object): ColumnGroup {
    return new ColumnGroup(
      json['name'] as string,
      (json['columns'] as object[]).map((col: object) => Column.fromJson(col)),
    );
  }
}

export class GenotypeBrowser {
  public static tableColumnsFromJson(json: Array<object>): Array<object> {
    const result: object[] = [];
    for (const column of json) {
      if ('columns' in column) {
        result.push(ColumnGroup.fromJson(column));
      } else {
        result.push(Column.fromJson(column));
      }
    }
    return result;
  }

  public static fromJson(json: object): GenotypeBrowser {
    return new GenotypeBrowser(
      json['has_pedigree_selector'] as boolean,
      json['has_present_in_child'] as boolean,
      json['has_present_in_parent'] as boolean,
      json['has_present_in_role'] as boolean,
      json['has_family_filters'] as boolean,
      json['has_family_structure_filter'] as boolean,
      json['has_person_filters'] as boolean,
      json['has_study_filters'] as boolean,
      json['has_study_types'] as boolean,
      GenotypeBrowser.tableColumnsFromJson(json['table_columns'] as object[]),
      PersonFilter.fromJson(json['person_filters'] as object),
      PersonFilter.fromJson(json['family_filters'] as object),
      json['inheritance_type_filter'] as string[],
      json['selected_inheritance_type_filter_values'] as string[],
      json['variant_types'] as string[],
      json['selected_variant_types'] as string[],
      json['max_variants_count'] as number,
      json['has_family_filters_beta'] as boolean,
      json['has_person_filters_beta'] as boolean,

    );
  }

  public constructor(
    public readonly hasPedigreeSelector: boolean,
    public readonly hasPresentInChild: boolean,
    public readonly hasPresentInParent: boolean,
    public readonly hasPresentInRole: boolean,
    public readonly hasFamilyFilters: boolean,
    public readonly hasFamilyStructureFilter: boolean,
    public readonly hasPersonFilters: boolean,
    public readonly hasStudyFilters: boolean,
    public readonly hasStudyTypes: boolean,
    public readonly tableColumns: Array<object>,
    public readonly personFilters: Array<PersonFilter>,
    public readonly familyFilters: Array<PersonFilter>,
    public readonly inheritanceTypeFilter: string[],
    public readonly selectedInheritanceTypeFilterValues: string[],
    public readonly variantTypes: string[],
    public readonly selectedVariantTypes: string[],
    public readonly maxVariantsCount: number,
    public readonly hasFamilyFiltersBeta: boolean,
    public readonly hasPersonFiltersBeta: boolean,

  ) { }

  public get columnIds(): Array<string> {
    const result: Array<string> = [];
    for (const column of this.tableColumns) {
      if ('columns' in column) {
        result.push(...(column['columns'] as object[]).map(col => col['source'] as string));
      } else {
        result.push(column['source'] as string);
      }
    }
    return result;
  }
}

export class GeneBrowser {
  public static fromJson(json: object): GeneBrowser {
    return new GeneBrowser(
      json['enabled'] as boolean,
      json['frequency_column'] as string,
      json['frequency_name'] as string,
      json['effect_column'] as string,
      json['location_column'] as string,
      json['domain_min'] as number,
      json['domain_max'] as number,
      json['has_affected_status'] as boolean
    );
  }

  public constructor(
    public readonly enabled: boolean,
    public readonly frequencyColumn: string,
    public readonly frequencyName: string,
    public readonly effectColumn: string,
    public readonly locationColumn: string,
    public readonly domainMin: number,
    public readonly domainMax: number,
    public readonly hasAffectedStatus: boolean,
  ) { }
}

export class Dataset extends IdName {
  public static fromJson(json: object): Dataset {
    if (!json) {
      return undefined;
    }
    return new Dataset(
      json['id'] as string,
      json['name'] as string,
      json['parents'] as string[],
      json['access_rights'] as boolean,
      json['studies'] as string[],
      json['study_names'] as string[],
      json['study_types'] as string[],
      json['phenotype_data'] as string,
      json['genotype_browser'] as boolean,
      json['phenotype_tool'] as boolean,
      json['enrichment_tool'] as boolean,
      json['phenotype_browser'] as boolean,
      json['common_report'] as {enabled: boolean},
      json['genotype_browser_config'] ? GenotypeBrowser.fromJson(json['genotype_browser_config'] as object) : null,
      json['person_set_collections'] ? PersonSetCollections.fromJson(json['person_set_collections'] as object) : null,
      UserGroup.fromJsonArray(json['groups'] as object[]),
      json['gene_browser'] ? GeneBrowser.fromJson(json['gene_browser'] as object) : null,
      json['has_denovo'] as boolean,
      json['description_editable'] as boolean
    );
  }

  public static fromDataset(datasetJson: object): Dataset {
    return new Dataset(
      datasetJson['id'] as string,
      datasetJson['name'] as string,
      datasetJson['parents'] as string[],
      datasetJson['access_rights'] as boolean,
      datasetJson['studies'] as string[],
      datasetJson['study_names'] as string[],
      datasetJson['study_types'] as string[],
      datasetJson['phenotype_data'] as string,
      datasetJson['genotype_browser'] as boolean,
      datasetJson['phenotype_tool'] as boolean,
      datasetJson['enrichment_tool'] as boolean,
      datasetJson['phenotype_browser'] as boolean,
      datasetJson['common_report'] as {enabled: boolean},
      datasetJson['genotype_browser_config'] ?
        GenotypeBrowser.fromJson(datasetJson['genotype_browser_config'] as object) : null,
      datasetJson['person_set_collections'] ?
        PersonSetCollections.fromJson(datasetJson['person_set_collections'] as object) : null,
      UserGroup.fromJsonArray(datasetJson['groups'] as object[]),
      datasetJson['gene_browser'] ? GeneBrowser.fromJson(datasetJson['gene_browser'] as object) : null,
      datasetJson['has_denovo'] as boolean,
      datasetJson['description_editable'] as boolean
    );
  }

  public static fromJsonArray(jsonArray: Array<object>): Array<Dataset> {
    if (!jsonArray) {
      return undefined;
    }
    return jsonArray.map((json) => Dataset.fromJson(json));
  }

  public getDefaultGroups(): string[] {
    return ['any_dataset', this.id];
  }

  public get defaultPersonSetCollection(): PersonSetCollection {
    return this.personSetCollections.collections[0];
  }

  public constructor(
    public readonly id: string,
    public readonly name: string,
    public readonly parents: string[],
    public readonly accessRights: boolean,
    public readonly studies: string[],
    public readonly studyNames: string[],
    public readonly studyTypes: string[],
    public readonly phenotypeData: string,
    public readonly genotypeBrowser: boolean,
    public readonly phenotypeTool: boolean,
    public readonly enrichmentTool: boolean,
    public readonly phenotypeBrowser: boolean,
    public readonly commonReport: {enabled: boolean},
    public readonly genotypeBrowserConfig: GenotypeBrowser,
    public readonly personSetCollections: PersonSetCollections,
    public readonly groups: UserGroup[],
    public readonly geneBrowser: GeneBrowser,
    public readonly hasDenovo: boolean,
    public readonly descriptionEditable: boolean
  ) {
    super(id, name);
  }
}

export class DatasetHierarchy {
  public description;
  public visibility = false;

  public constructor(
    public id: string,
    public name: string,
    public accessRights: boolean,
    public children: DatasetHierarchy[],
  ) { }

  public static fromJson(json: object): DatasetHierarchy {
    if (!json) {
      return undefined;
    }

    let children: DatasetHierarchy[] = [];
    if (json['children']) {
      children = (json['children'] as object[])
        .map(child => DatasetHierarchy.fromJson(child));
    }

    return new DatasetHierarchy(
      json['dataset'] as string,
      json['name'] as string,
      json['access_rights'] as boolean,
      children
    );
  }
}
