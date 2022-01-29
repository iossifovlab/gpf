import { Type, plainToClass } from 'class-transformer';
import 'reflect-metadata';
import * as YAML from 'yaml';

import { GenesBlockPage } from './genes-block-page';
import { EnrichmentModelsBockPage } from './enrichment-models-block-page';
import { GeneWeightsPage } from './gene-weights-page';

export class EnrichmentToolData {
  public name: string;
  public study: string;
  public target: string;

  @Type(() => Case)
  public cases: Case[];
}

class Case {
  public name: string;

  @Type(() => Params)
  public params: Params;

  @Type(() => Expected)
  public expected: Expected[];
}

class Expected {
  public rowId: string;
  public values: string[];
}

export class Params {
  public geneSymbols: string[];

  @Type(() => Models)
  public models: Models;

  @Type(() => GeneWeight)
  public geneWeight: GeneWeight;

  @Type(() => GeneSet)
  public geneSet: GeneSet;
}

class Models {
  public backgroundModel: string;
  public countingModel: string;
}

class GeneWeight {
  public id: string;
  public from: number;
  public to: number;
}

class GeneSet {
  public id: string

  @Type(() => GeneSetCollection)
  public collection: GeneSetCollection;
}

class GeneSetCollection {
  public id: string;

  @Type(() => GeneSetCollectionAffectedStatus)
  public affectedStatus: GeneSetCollectionAffectedStatus[];
}

class GeneSetCollectionAffectedStatus {
  public studyId: string;
  public affected: boolean;
  public unaffected: boolean
}

// Pass path to yaml file using the '--env' flag in the cypress command:
// npx cypress open --config baseUrl=http://172.20.0.5/gpf/ --env yamlPath=cypress/iossifov.data.expected.yaml
export function parseYamlData(filePath: string): EnrichmentToolData[] {
  if (filePath === undefined) {
    return;
  }

  return plainToClass(EnrichmentToolData, YAML.parse(filePath) as EnrichmentToolData[]);
}

export function applyData(params: Params): void {
  const genesBlockPage = new GenesBlockPage();
  const geneWeightsPage = new GeneWeightsPage();
  const enrichmentModelsBockPage = new EnrichmentModelsBockPage();

  if (params.geneSymbols) {
    genesBlockPage.geneSymbolsButton.click();
    genesBlockPage.geneSymbolsTextarea.clear().type(params.geneSymbols.join(','));
  } else if (params.geneSet) {
    genesBlockPage.geneSetsButton.click();

    genesBlockPage.geneSetsCollectionSelectorDropdownMenu.select(params.geneSet.collection.id, {force: true});

    genesBlockPage.geneSetsSearchbox.click();
    genesBlockPage.geneSetsSearchbox.type(params.geneSet.id);
    genesBlockPage.findGeneSetsSearchboxDropdownOptionsByText(params.geneSet.id).click();

    if (params.geneSet.collection.id === 'Denovo' && params.geneSet.collection.affectedStatus) {
      // TODO
    }
  } else if (params.geneWeight) {
    genesBlockPage.geneWeightsButton.click();
    geneWeightsPage.dropdownButton.select(params.geneWeight.id);

    if (params.geneWeight.from) {
      geneWeightsPage.fromInputField.clear();
      geneWeightsPage.fromInputField.type(params.geneWeight.from.toString())
    }

    if (params.geneWeight.to) {
      geneWeightsPage.fromInputField.clear();
      geneWeightsPage.fromInputField.type(params.geneWeight.to.toString())
    }
  }

  if (params.models) {
    enrichmentModelsBockPage.selectModelsButton.click();

    if (params.models.backgroundModel) {
      enrichmentModelsBockPage.backgroundModelsDropdown.select(params.models.backgroundModel);
    }

    if (params.models.countingModel) {
      enrichmentModelsBockPage.countingModelsDropdown.select(params.models.countingModel);
    }
  }
}