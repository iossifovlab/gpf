import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
// eslint-disable-next-line no-restricted-imports
import { of } from 'rxjs';
import { AgpTableService } from './autism-gene-profiles-table.service';

describe('AgpTableService', () => {
  let service: AgpTableService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ConfigService],
      imports: [HttpClientTestingModule]
    });
    service = TestBed.inject(AgpTableService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get genes', () => {
    const getGenesSpy = jest.spyOn(service['http'], 'get');

    getGenesSpy.mockReturnValue(of({}));
    service.getGenes(1);
    service.getGenes(1, 'mockSearch');
    service.getGenes(1, 'mockSearch', 'mockSort', 'desc');
    expect(getGenesSpy.mock.calls).toEqual([ // eslint-disable-line
      [service['config'].baseUrl + service['genesUrl'] + '?page=1'],
      [service['config'].baseUrl + service['genesUrl'] + '?page=1&symbol=mockSearch'],
      [service['config'].baseUrl + service['genesUrl'] + '?page=1&symbol=mockSearch&sortBy=mockSort&order=desc']
    ]);
  });
});
