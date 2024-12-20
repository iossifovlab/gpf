import { TestBed, waitForAsync } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsTreeService } from 'app/datasets/datasets-tree.service';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { UsersService } from 'app/users/users.service';
import { RouterTestingModule } from '@angular/router/testing';
import { APP_BASE_HREF } from '@angular/common';
import { Dataset } from './datasets';
import { DatasetNode } from 'app/dataset-node/dataset-node';
import { StoreModule } from '@ngrx/store';
import { provideHttpClient } from '@angular/common/http';

const datasetNodeMock1 = new DatasetNode(new Dataset('id1',
  null, ['id11', 'id12'], null, null, null, null, null,
  null, null, null, null, null, null, null, null, null, null, null, null
), [
  new Dataset(
    'id2',
    null, ['id1', 'parent2'], null, null, null, null, null,
    null, null, null, null, null, null, null, null, null, null, null, null
  ),
  new Dataset(
    'id3',
    null, ['id1', 'parent3'], null, null, null, null, null,
    null, null, null, null, null, null, null, null, null, null, null, null
  ),
  new Dataset(
    'id4',
    null, ['id4', 'parent4'], null, null, null, null, null,
    null, null, null, null, null, null, null, null, null, null, null, null
  )
]);

describe('DatasetService', () => {
  let service: DatasetsTreeService;
  beforeEach(waitForAsync(() => {
    const configMock = { baseUrl: 'testUrl/' };
    TestBed.configureTestingModule({
      imports: [StoreModule.forRoot({}), RouterTestingModule],
      providers: [
        DatasetsTreeService,
        UsersService,
        {provide: ConfigService, useValue: configMock},
        { provide: APP_BASE_HREF, useValue: '' },
        provideHttpClient(),
        provideHttpClientTesting()
      ],
      declarations: [],
    }).compileComponents();

    service = TestBed.inject(DatasetsTreeService);
  }));

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should test find node by id', () => {
    expect(service.findNodeById(datasetNodeMock1, 'id3')).toStrictEqual(new DatasetNode(
      new Dataset(
        'id3',
        null, ['id1', 'parent3'], null, null, null, null, null,
        null, null, null, null, null, null, null, null, null, null, null, null
      ), [
        new Dataset(
          'id2',
          null, ['id1', 'parent2'], null, null, null, null, null,
          null, null, null, null, null, null, null, null, null, null, null, null
        ),
        new Dataset(
          'id3',
          null, ['id1', 'parent3'], null, null, null, null, null,
          null, null, null, null, null, null, null, null, null, null, null, null
        ),
        new Dataset(
          'id4',
          null, ['id4', 'parent4'], null, null, null, null, null,
          null, null, null, null, null, null, null, null, null, null, null, null
        )]
    ));
  });
});
