import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { compact } from 'lodash';
// tslint:disable-next-line:import-blacklist
import { of } from 'rxjs';

import { AutismGeneProfilesService } from './autism-gene-profiles.service';

const configurationMock = {
  'gene_sets': [
      'mockSet'
  ],
  'protection_scores': [
      'protectionScore1',
      'protectionScore2',
  ],
  'autism_scores': [
      'autismScore1',
      'autismScore2',
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

const geneMock = {
  'gene_symbol': 'mockGene',
  'gene_sets': [
      'mockSet'
  ],
  'protection_scores': {
      'protectionScore1': 1,
      'protectionScore2': 2,
  },
  'autism_scores': {
      'autismScore1': 3,
      'autismScore2': 4,
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
  'gene_symbol': 'mockGene2',
  'gene_sets': [
      'mockSet'
  ],
  'protection_scores': {
      'protectionScore1': 9,
      'protectionScore2': 10,
  },
  'autism_scores': {
      'autismScore1': 11,
      'autismScore2': 12,
  },
  'studies': {
      'mockDataset': {
          'personSet1': {
              'effect1': 13,
              'effect2': 14,
          },
          'personSet2': {
              'effect3': 15,
              'effect4': 16,
          }
      }
  }
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

    getConfigSpy.and.returnValue(of(configurationMock));
    const resultConfig = service.getConfig();
    expect(getConfigSpy).toHaveBeenCalledWith(service['config'].baseUrl + service['configUrl']);
    resultConfig.take(1).subscribe(res => {
      expect(res['geneSets']).toEqual(['mockSet']);
      expect(res['autismScores']).toEqual(['autismScore1', 'autismScore2']);
      expect(res['protectionScores']).toEqual( [ 'protectionScore1', 'protectionScore2' ]);
      expect(res['datasets'][0]['effects']).toEqual(['effect1', 'effect2', 'effect3']);
      expect(res['datasets'][0]['personSets']).toEqual(['personSet1', 'personSet2']);
    });
  });

  it('should get single gene', () => {
    const getGeneSpy = spyOn(service['http'], 'get');

    getGeneSpy.and.returnValue(of(geneMock));
    const resultGene = service.getGene('mockGene');
    expect(getGeneSpy).toHaveBeenCalledWith(service['config'].baseUrl + service['genesUrl'] + 'mockGene');
    resultGene.take(1).subscribe(res => {
      expect(res['geneSymbol']).toEqual('mockGene');
      expect(res['geneSets']).toEqual(['mockSet']);
      expect(res['protectionScores'].get('protectionScore1')).toBe(1);
      expect(res['protectionScores'].get('protectionScore2')).toBe(2);
      expect(res['autismScores'].get('autismScore1')).toBe(3);
      expect(res['autismScores'].get('autismScore2')).toBe(4);
      expect(Number(res['studies'][0]['personSets'][0]['effectTypes'].get('effect1'))).toBe(5);
      expect(Number(res['studies'][0]['personSets'][0]['effectTypes'].get('effect2'))).toBe(6);
      expect(Number(res['studies'][0]['personSets'][1]['effectTypes'].get('effect3'))).toBe(7);
      expect(Number(res['studies'][0]['personSets'][1]['effectTypes'].get('effect4'))).toBe(8);
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

    getGenesSpy.and.returnValue(of([geneMock, geneMock2]));
    const resultGenes = service.getGenes(1);
    resultGenes.take(1).subscribe(res => {
      expect(res[0]['geneSymbol']).toEqual('mockGene');
      expect(res[0]['geneSets']).toEqual(['mockSet']);
      expect(res[0]['protectionScores'].get('protectionScore1')).toBe(1);
      expect(res[0]['protectionScores'].get('protectionScore2')).toBe(2);
      expect(res[0]['autismScores'].get('autismScore1')).toBe(3);
      expect(res[0]['autismScores'].get('autismScore2')).toBe(4);
      expect(Number(res[0]['studies'][0]['personSets'][0]['effectTypes'].get('effect1'))).toBe(5);
      expect(Number(res[0]['studies'][0]['personSets'][0]['effectTypes'].get('effect2'))).toBe(6);
      expect(Number(res[0]['studies'][0]['personSets'][1]['effectTypes'].get('effect3'))).toBe(7);
      expect(Number(res[0]['studies'][0]['personSets'][1]['effectTypes'].get('effect4'))).toBe(8);
      expect(res[1]['geneSymbol']).toEqual('mockGene2');
      expect(res[1]['geneSets']).toEqual(['mockSet']);
      expect(res[1]['protectionScores'].get('protectionScore1')).toBe(9);
      expect(res[1]['protectionScores'].get('protectionScore2')).toBe(10);
      expect(res[1]['autismScores'].get('autismScore1')).toBe(11);
      expect(res[1]['autismScores'].get('autismScore2')).toBe(12);
      expect(Number(res[1]['studies'][0]['personSets'][0]['effectTypes'].get('effect1'))).toBe(13);
      expect(Number(res[1]['studies'][0]['personSets'][0]['effectTypes'].get('effect2'))).toBe(14);
      expect(Number(res[1]['studies'][0]['personSets'][1]['effectTypes'].get('effect3'))).toBe(15);
      expect(Number(res[1]['studies'][0]['personSets'][1]['effectTypes'].get('effect4'))).toBe(16);
    });
  });
});
