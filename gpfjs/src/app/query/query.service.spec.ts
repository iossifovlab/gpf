import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { QueryService } from './query.service';
import { RouterModule, Routes } from '@angular/router';
import { APP_BASE_HREF } from '@angular/common';
import { environment } from '../../environments/environment';

describe('QueryService', () => {
  let service: QueryService;
  let httpController: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ConfigService, QueryService, { provide: APP_BASE_HREF, useValue: '' }],
      imports: [
        HttpClientTestingModule,
        RouterModule.forRoot([])
      ]
    });
    service = TestBed.inject(QueryService);
    httpController = TestBed.inject(HttpTestingController);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should test downloadVariants', () => {
    const response = new Blob();
    service.downloadVariants([]).subscribe();
    const req = httpController.expectOne({
      method: 'POST',
      url: `${environment.apiPath}genotype_browser/query`
    });
    req.flush(response);
  });
});
