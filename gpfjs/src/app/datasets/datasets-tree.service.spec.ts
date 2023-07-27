import { TestBed, waitForAsync } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsTreeService } from 'app/datasets/datasets-tree.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { UsersService } from 'app/users/users.service';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { APP_BASE_HREF } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { lastValueFrom } from 'rxjs/internal/lastValueFrom';
import { of } from 'rxjs/internal/observable/of';
import { Dataset } from './datasets';
import { DatasetNode } from 'app/dataset-node/dataset-node';

const datasetNodeMock1 = new DatasetNode(new Dataset('id1',
  null, null, ['id11', 'id12'], null, null, null, null, null,
  null, null, null, null, null, null, null, null, null, null, null
), [
  new Dataset(
    'id2',
    null, null, ['id1', 'parent2'], null, null, null, null, null,
    null, null, null, null, null, null, null, null, null, null, null
  ),
  new Dataset(
    'id3',
    null, null, ['id1', 'parent3'], null, null, null, null, null,
    null, null, null, null, null, null, null, null, null, null, null
  ),
  new Dataset(
    'id4',
    null, null, ['id4', 'parent4'], null, null, null, null, null,
    null, null, null, null, null, null, null, null, null, null, null
  )
]);

/* eslint-disable @typescript-eslint/naming-convention */
const hierarchyMock1 = {
  data: [
    {
      dataset: 'dataset1', name: 'id1', access_rights: false, children: [
        {dataset: 'datasetChild1', name: 'id2', access_rights: true, children: null},
        {
          dataset: 'datasetChild2', name: 'id3', access_rights: false, children: [
            {dataset: 'datasetSubChild1', name: 'id4', access_rights: true, children: null},
          ]
        },
      ]
    }
  ]
};
/* eslint-enable @typescript-eslint/naming-convention */

describe('DatasetService', () => {
  let service: DatasetsTreeService;
  beforeEach(waitForAsync(() => {
    const configMock = { baseUrl: 'testUrl/' };
    TestBed.configureTestingModule({
      imports: [NgxsModule.forRoot([], {developmentMode: true}), RouterTestingModule, HttpClientTestingModule],
      providers: [
        DatasetsTreeService,
        UsersService,
        {provide: ConfigService, useValue: configMock},
        { provide: APP_BASE_HREF, useValue: '' }
      ],
      declarations: [],
    }).compileComponents();

    service = TestBed.inject(DatasetsTreeService);
  }));

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should test get datasets hierarchy', async() => {
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of(hierarchyMock1));

    const response = await lastValueFrom(service.getDatasetHierarchy());
    expect(httpGetSpy.mock.calls.toString()).toBe('testUrl/datasets/hierarchy');
    expect(response).toStrictEqual({
      data: [
        {
          dataset: 'dataset1', children: [
            {dataset: 'datasetChild1', children: null},
            {dataset: 'datasetChild2', children: [
              {dataset: 'datasetSubChild1', children: null},
            ]},
          ]
        }
      ]
    });
  });

  it('should test find node by id', () => {
    expect(service.findNodeById(datasetNodeMock1, 'id3')).toStrictEqual(new DatasetNode(
      new Dataset(
        'id3',
        null, null, ['id1', 'parent3'], null, null, null, null, null,
        null, null, null, null, null, null, null, null, null, null, null
      ), [
        new Dataset(
          'id2',
          null, null, ['id1', 'parent2'], null, null, null, null, null,
          null, null, null, null, null, null, null, null, null, null, null
        ),
        new Dataset(
          'id3',
          null, null, ['id1', 'parent3'], null, null, null, null, null,
          null, null, null, null, null, null, null, null, null, null, null
        ),
        new Dataset(
          'id4',
          null, null, ['id4', 'parent4'], null, null, null, null, null,
          null, null, null, null, null, null, null, null, null, null, null
        )]
    ));
  });
});
