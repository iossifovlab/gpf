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

    getConfigSpy.and.returnValue(of({}));
    let resultConfig = service.getConfig();
    resultConfig.take(1).subscribe(res => {
      expect(res).toEqual(undefined);
    });

    getConfigSpy.and.returnValue(of(configurationMock));
    resultConfig = service.getConfig();
    expect(getConfigSpy).toHaveBeenCalledWith(service['config'].baseUrl + service['configUrl']);
    resultConfig.take(1).subscribe(res => {
      expect(res['geneSets']).toEqual(['mockSet']);
      expect(res['autismScores']).toEqual(['autismScore1', 'autismScore2']);
      expect(res['protectionScores']).toEqual( [ 'protectionScore1', 'protectionScore2' ]);
      expect(res['datasets']['mockDataset']['effects']).toEqual(['effect1', 'effect2', 'effect3']);
      expect(res['datasets']['mockDataset']['personSets']).toEqual(['personSet1', 'personSet2']);
    });
  });

  it('should get single gene', () => {
    const getGeneSpy = spyOn(service['http'], 'get');

    getGeneSpy.and.returnValue(of({}));
    let resultGene = service.getGene('mockGene');
    resultGene.take(1).subscribe(res => {
      expect(res).toEqual(undefined);
    });

    getGeneSpy.and.returnValue(of(geneMock));
    resultGene = service.getGene('mockGene');
    expect(getGeneSpy).toHaveBeenCalledWith(service['config'].baseUrl + service['genesUrl'] + 'mockGene');
    resultGene.take(1).subscribe(res => {
      expect(res['geneSymbol']).toEqual('mockGene');
      expect(res['geneSets']).toEqual(['mockSet']);
      expect(res['protectionScores'].get('protectionScore1')).toBe(1);
      expect(res['protectionScores'].get('protectionScore2')).toBe(2);
      expect(res['autismScores'].get('autismScore1')).toBe(3);
      expect(res['autismScores'].get('autismScore2')).toBe(4);
      expect(res['studies']['mockDataset']['personSet1']['effect1']).toBe(5);
      expect(res['studies']['mockDataset']['personSet1']['effect2']).toBe(6);
      expect(res['studies']['mockDataset']['personSet2']['effect3']).toBe(7);
      expect(res['studies']['mockDataset']['personSet1']['effect4']).toBe(8);
    });
  });

  it('should get genes', () => {
    // to do
  });
});
