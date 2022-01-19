import { Type } from 'class-transformer';
import 'reflect-metadata';
import { plainToClass } from 'class-transformer';
import * as YAML from 'yaml';

import { GenesBlockPage } from './genes-block-page';
import { EnrichmentModelsBockPage } from './enrichment-models-block-page';
import { GeneWeightsPage } from './gene-weights-page';

export class EnrichmentToolData {
  name: string;
  study: string;
  target: string;

  @Type(() => Case)
  cases: Case[];
}

class Case {
  name: string;

  @Type(() => Params)
  params: Params;

  @Type(() => Expected)
  expected: Expected[];
}

class Expected {
  rowId: string;
  values: string[];
}

export class Params {
  geneSymbols: string[];

  @Type(() => Models)
  models: Models;

  @Type(() => GeneWeight)
  geneWeight: GeneWeight;

  @Type(() => GeneSet)
  geneSet: GeneSet;
}

class Models {
  backgroundModel: string;
  countingModel: string;
}

class GeneWeight {
  id: string;
  from: number;
  to: number;
}

class GeneSet {
  id: string

  @Type(() => GeneSetCollection)
  collection: GeneSetCollection;
}

class GeneSetCollection {
  id: string;

  @Type(() => GeneSetCollectionAffectedStatus)
  affectedStatus: GeneSetCollectionAffectedStatus[];
}

class GeneSetCollectionAffectedStatus {
  studyId: string;
  affected: boolean;
  unaffected: boolean
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
      // ...
      // ..
    }

  } else if (params.geneWeight) {
    genesBlockPage.geneWeightsButton.click();
    geneWeightsPage.dropdownButton.select(params.geneWeight.id);

    if (params.geneWeight.from) {
      geneWeightsPage.fromInputField.type(params.geneWeight.from.toString())
    }

    if (params.geneWeight.to) {
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