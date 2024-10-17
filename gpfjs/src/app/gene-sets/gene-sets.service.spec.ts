import { HttpClient } from '@angular/common/http';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { of } from 'rxjs';
import { GeneSetsService } from './gene-sets.service';
import { APP_BASE_HREF } from '@angular/common';
import { SelectedDenovoTypes, SelectedPersonSetCollections } from './gene-sets';

describe('GeneSetsService', () => {
  let service: GeneSetsService;
  const configMock = { baseUrl: 'testUrl/' };
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        { provide: ConfigService, useValue: configMock },
        { provide: APP_BASE_HREF, useValue: '' },
        HttpClientTestingModule, GeneSetsService
      ],
      imports: [HttpClientTestingModule],
    });

    service = TestBed.inject(GeneSetsService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should getGeneSetsCollections', () => {
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of('fakeResponse'));
    service.getGeneSetsCollections();

    // eslint-disable-next-line jest/prefer-strict-equal
    expect(httpGetSpy.mock.calls).toEqual(
      [
        [
          'testUrl/gene_sets/gene_sets_collections',
          // eslint-disable-next-line @typescript-eslint/naming-convention
          { headers: {'Content-Type': 'application/json'}, withCredentials: true }
        ]
      ]
    );
  });

  it('should get the gene set download link', () => {
    const collectionName = 'denovo';
    const geneSetName = 'LGDs.Male';
    const geneSetTypes = [
      new SelectedDenovoTypes(
        'deNovo',
        [
          new SelectedPersonSetCollections('phenotype', ['autism', 'unaffected'])
        ])
    ];

    const downloadLink = service.getGeneSetDownloadLink(collectionName, geneSetName, geneSetTypes);

    expect(downloadLink).toBe(`${configMock.baseUrl}gene_sets/gene_set_download?` +
      `geneSetsCollection=denovo&` +
      `geneSet=LGDs.Male&` +
      `geneSetsTypes=` +
      `[{\"datasetId\":\"deNovo\",\"collections\":[{\"personSetId\":\"phenotype\",\"types\":[\"autism\",\"unaffected\"]}]}]`);
  });
});
