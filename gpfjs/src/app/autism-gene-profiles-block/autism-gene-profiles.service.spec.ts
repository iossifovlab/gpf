import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
// tslint:disable-next-line:import-blacklist
import { of } from 'rxjs';

import { AutismGeneProfilesService } from './autism-gene-profiles.service';
import * as deepEqual from 'deep-equal';
const util = require('util');

const configurationMockJson = {
  'default_dataset': 'defaultDataset',
  'gene_sets': [
    {'category': 'first_gene_sets',
      'display_name': 'First_Gene_Sets',
      'sets': [
        {'set_id': 'set11', 'collection_id': 'main11'},
        {'set_id': 'set12', 'collection_id': 'main12'}
      ]
    },
    {'category': 'second_gene_sets',
      'display_name': 'Second_Gene_Sets',
      'sets': [
        {'set_id': 'set21', 'collection_id': 'main21'},
        {'set_id': 'set22', 'collection_id': 'main22'}
      ]
    }
  ],
  'genomic_scores': [
    {'category': 'first_genomic_scores',
      'display_name': 'First_Genomic_Scores',
      'scores': [
        {'score_name': 'score11', 'format': '%s'},
        {'score_name': 'score12', 'format': '%s'}
      ]
    },
    {'category': 'second_genomic_scores',
      'display_name': 'Second_Genomic_Scores',
      'scores': [
        {'score_name': 'score21', 'format': '%s'},
        {'score_name': 'score22', 'format': '%s'}
      ]
    }
  ],
  'datasets': {
    'mockDataset': {
      'effects': [
        'effect1',
        'effect2',
        'effect3'
      ],
      'person_sets': [
        'personSet1',
        'personSet2'
      ]
    }
  }
};

const configurationMock = {
  defaultDataset : 'defaultDataset',
  geneSets : [
    {category : 'first_gene_sets',
      displayName : 'First_Gene_Sets',
      sets : [
        {setId : 'set11', collectionId : 'main11'},
        {setId : 'set12', collectionId : 'main12'}
      ]
    },
    {category : 'second_gene_sets',
      displayName : 'Second_Gene_Sets',
      sets : [
        {setId : 'set21', collectionId : 'main21'},
        {setId : 'set22', collectionId : 'main22'}
      ]
    }
  ],
  genomicScores : [
    {category : 'first_genomic_scores',
      displayName : 'First_Genomic_Scores',
      scores : [
        {scoreName : 'score11', format : '%s'},
        {scoreName : 'score12', format : '%s'}
      ]
    },
    {category : 'second_genomic_scores',
      displayName : 'Second_Genomic_Scores',
      scores : [
        {scoreName : 'score21', format : '%s'},
        {scoreName : 'score22', format : '%s'}
      ]
    }
  ],
  datasets : [
    {name: 'mockDataset',
      effects : [
        'effect1',
        'effect2',
        'effect3'
      ],
      personSets : [
        'personSet1',
        'personSet2'
      ]
    }
  ]
};

const geneMockJson1 = {
  'gene_symbol': 'mockGene1',
  'gene_sets': [
    'set11'
  ],
  'genomic_scores': {
    'first_genomic_scores': {
      'score11': { 'value': 11, 'format': '%s'},
      'score12': { 'value': 12, 'format': '%s'},
    }
  },
  'studies': {
    'mockDataset': {
      'personSet1': {
        'effect1': 1,
        'effect2': 2,
      },
      'personSet2': {
        'effect3': 3,
        'effect4': 4,
      }
    }
  }
};

const geneMock1 = {
  geneSymbol: 'mockGene1',
  geneSets: [ 'set11' ],
  genomicScores: [ { category: 'first_genomic_scores', scores: {} } ],
  studies: [
    {name: 'mockDataset',
      personSets: [
        { name: 'personSet1', effectTypes: {} },
        { name: 'personSet2', effectTypes: {} }
      ]
    }
  ]
};

const geneMockJson2 = {
  'gene_symbol': 'mockGene2',
  'gene_sets': [
    'set21'
  ],
  'genomic_scores': {
    'second_genomic_scores': {
      'score21': { 'value': 21, 'format': '%s'},
      'score22': { 'value': 22, 'format': '%s'},
    }
  },
  'studies': {
    'mockDataset': {
      'personSet1': {
        'effect1': 5,
        'effect2': 6,
      },
      'personSet2': {
        'effect3': 7,
        'effect4': 8,
      }
    }
  }
};

const geneMock2 = {
  geneSymbol: 'mockGene2',
  geneSets: [ 'set21' ],
  genomicScores: [ { category: 'second_genomic_scores', scores: {} } ],
  studies: [
    {name: 'mockDataset',
      personSets: [
        { name: 'personSet1', effectTypes: {} },
        { name: 'personSet2', effectTypes: {} }
      ]
    }
  ]
};

describe('AutismGeneProfilesService', () => {
  let service: AutismGeneProfilesService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ConfigService],
      imports: [HttpClientTestingModule]
    });
    service = TestBed.inject(AutismGeneProfilesService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get config', () => {
    const getConfigSpy = spyOn(service['http'], 'get');

    getConfigSpy.and.returnValue(of(configurationMockJson));
    const resultConfig = service.getConfig();
    expect(getConfigSpy).toHaveBeenCalledWith(service['config'].baseUrl + service['configUrl']);
    resultConfig.take(1).subscribe(res => {
      expect(deepEqual(res, configurationMock)).toBeTrue();
    });
  });

  it('should get single gene', () => {
    const getGeneSpy = spyOn(service['http'], 'get');
    getGeneSpy.and.returnValue(of(geneMockJson1));

    const resultGene = service.getGene('geneMock1');
    expect(getGeneSpy).toHaveBeenCalledWith(service['config'].baseUrl + service['genesUrl'] + 'geneMock1');
    resultGene.take(1).subscribe(res => {
      expect(deepEqual(res, geneMock1)).toBeTrue();
      expect(res['genomicScores'][0]['scores'].get('score11')).toBe('11');
      expect(res['genomicScores'][0]['scores'].get('score12')).toBe('12');
    });
  });

  it('should get genes', () => {
    const getGenesSpy = spyOn(service['http'], 'get');

    getGenesSpy.and.returnValue(of({}));
    service.getGenes(1);
    service.getGenes(1, 'mockSearch');
    service.getGenes(1, 'mockSearch', 'mockSort', 'desc');
    expect(getGenesSpy.calls.allArgs()).toEqual([
      [service['config'].baseUrl + service['genesUrl'] + '?page=1'],
      [service['config'].baseUrl + service['genesUrl'] + '?page=1' + '&symbol=mockSearch'],
      [service['config'].baseUrl + service['genesUrl'] + '?page=1' + '&symbol=mockSearch' + '&sortBy=mockSort&order=desc']
    ]);

    getGenesSpy.and.returnValue(of([geneMockJson1, geneMockJson2]));
    const resultGenes = service.getGenes(1);
    resultGenes.take(1).subscribe(res => {
      expect(deepEqual(res[0], geneMock1)).toBeTrue();
      expect(res[0]['genomicScores'][0]['scores'].get('score11')).toBe('11');
      expect(res[0]['genomicScores'][0]['scores'].get('score12')).toBe('12');
      expect(deepEqual(res[1], geneMock2)).toBeTrue();
      expect(res[1]['genomicScores'][0]['scores'].get('score21')).toBe('21');
      expect(res[1]['genomicScores'][0]['scores'].get('score22')).toBe('22');
    });
  });
});
