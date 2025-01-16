import { TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { lastValueFrom, of } from 'rxjs';
import { GeneProfilesService } from './gene-profiles.service';
import {
  GeneProfilesSingleViewConfig,
  GeneProfilesGene
} from 'app/gene-profiles-single-view/gene-profiles-single-view';
import { take } from 'rxjs/operators';
import { provideHttpClient } from '@angular/common/http';

const mockConfigJson = {
  defaultDataset: 'ALL_genotypes',
  geneLinks: [
    {
      name: 'Gene Browser',
      url: 'datasets/ALL_genotypes/gene-browser/{gene}'
    }
  ],
  order: [
    {
      section: null,
      id: 'autism_gene_sets_rank'
    },
    {
      section: 'genomicScores',
      id: 'autism_scores'
    },
    {
      section: 'datasets',
      id: 'sequencing_de_novo'
    }
  ],
  geneSets: [
    {
      category: 'autism_gene_sets',
      displayName: 'Autism Gene Sets',
      sets: [
        {
          setId: 'SFARI ALL',
          collectionId: 'sfari',
          defaultVisible: true
        }
      ],
      defaultVisible: true
    }
  ],
  genomicScores: [
    {
      category: 'autism_scores',
      displayName: 'Autism Gene Scores',
      scores: [
        {
          scoreName: 'SFARI gene score',
          format: '%s',
          defaultVisible: true
        }
      ],
      defaultVisible: true
    }
  ],
  datasets: [
    {
      id: 'sequencing_de_novo',
      displayName: 'Sequencing de Novo',
      defaultVisible: true,
      statistics: [
        {
          id: 'denovo_lgds',
          description: 'de Novo LGDs',
          displayName: 'dn LGDs',
          effects: [
            'LGDs'
          ],
          category: 'denovo',
          defaultVisible: true
        }
      ],
      personSets: [
        {
          id: 'autism',
          displayName: 'autism',
          collectionId: 'phenotype',
          description: '',
          parentsCount: 0,
          childrenCount: 21795,
          statistics: [
            {
              id: 'denovo_lgds',
              description: 'de Novo LGDs',
              displayName: 'dn LGDs',
              effects: [
                'LGDs'
              ],
              category: 'denovo',
              defaultVisible: true
            }
          ]
        }
      ]
    },
  ],
  confDir: '/data',
  pageSize: 50
};

describe('GeneProfilesService', () => {
  let service: GeneProfilesService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ConfigService, provideHttpClient()],
      imports: []
    });
    service = TestBed.inject(GeneProfilesService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get config', async() => {
    const getConfigSpy = jest.spyOn(service['http'], 'get');
    getConfigSpy.mockReturnValue(of(mockConfigJson));

    const resultConfig = service.getConfig();

    expect(getConfigSpy).toHaveBeenCalledWith(service['config'].baseUrl + service['configUrl']);
    const config = await lastValueFrom(resultConfig.pipe(take(1)));
    expect(config).toBeInstanceOf(GeneProfilesSingleViewConfig);
    expect(config.geneLinkTemplates[0]).toStrictEqual({
      name: 'Gene Browser',
      url: 'datasets/ALL_genotypes/gene-browser/{gene}'
    });
    expect(config.order[1].id).toBe('autism_scores');
    expect(config.geneSets[0].displayName).toBe('Autism Gene Sets');
    expect(config.geneSets[0].sets[0].setId).toBe('SFARI ALL');
    expect(config.genomicScores[0].displayName).toBe('Autism Gene Scores');
    expect(config.genomicScores[0].scores[0].scoreName).toBe('SFARI gene score');
    expect(config.datasets[0].id).toBe('sequencing_de_novo');
    expect(config.datasets[0].statistics[0].id).toBe('denovo_lgds');
    expect(config.datasets[0].personSets[0].id).toBe('autism');
    expect(config.datasets[0].personSets[0].statistics[0].id).toBe('denovo_lgds');
  });

  it('should get invalid config response', async() => {
    const getConfigSpy = jest.spyOn(service['http'], 'get');
    getConfigSpy.mockReturnValue(of({ }));

    const resultConfig = service.getConfig();

    expect(getConfigSpy).toHaveBeenCalledWith(service['config'].baseUrl + service['configUrl']);
    const res = await lastValueFrom(resultConfig.pipe(take(1)));
    expect(res).toBeUndefined();
  });

  it('should get single gene', async() => {
    const getGeneSpy = jest.spyOn(service['http'], 'get');
    getGeneSpy.mockReturnValue(of({ mockGeneProperty: 'mockGeneValue' }));

    const resultGene = service.getGene('geneMock1');

    expect(getGeneSpy).toHaveBeenCalledWith(service['config'].baseUrl + service['genesUrl'] + 'geneMock1');
    const res = await lastValueFrom(resultGene.pipe(take(1)));
    expect(res['mockGeneProperty']).toBe('mockGeneValue');
    expect(res).toBeInstanceOf(GeneProfilesGene);
  });
});
