import { TestBed, waitForAsync } from '@angular/core/testing';

import { HttpClient, provideHttpClient } from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { UsersService } from 'app/users/users.service';
import { RouterTestingModule } from '@angular/router/testing';
import { Dataset, GeneBrowser, PersonSet, PersonSetCollection, PersonSetCollections } from './datasets';
import { lastValueFrom, of, take } from 'rxjs';
import { APP_BASE_HREF } from '@angular/common';
import { StoreModule } from '@ngrx/store';
import { UserGroup } from 'app/users-groups/users-groups';

const datasetMock = new Dataset(
  'id1',
  'name1',
  ['parent1', 'parent2'],
  false,
  ['study1', 'study2'],
  ['studyName1', 'studyName2'],
  ['studyType1', 'studyType2'],
  'phenotypeData1',
  false,
  true,
  true,
  false,
  {enabled: true},
  null,
  new PersonSetCollections(
    [
      new PersonSetCollection(
        'id1',
        'name1',
        [
          new PersonSet('id1', 'name1', 'color1'),
          new PersonSet('id1', 'name2', 'color3'),
          new PersonSet('id2', 'name3', 'color4')
        ]
      ),
      new PersonSetCollection(
        'id2',
        'name2',
        [
          new PersonSet('id2', 'name2', 'color2'),
          new PersonSet('id2', 'name3', 'color5'),
          new PersonSet('id3', 'name4', 'color6')
        ]
      )
    ]
  ),
  [
    new UserGroup(3, 'name1', ['user1', 'user2'], [{datasetName: 'dataset2', datasetId: 'dataset3'}]),
    new UserGroup(5, 'name2', ['user12', 'user5'], [{datasetName: 'dataset1', datasetId: 'dataset2'}])
  ],
  new GeneBrowser(true, 'frequencyCol1', 'frequencyName1', 'effectCol1', 'locationCol1', 5, 6, true),
  false,
  true,
  true,
  true
);

describe('DatasetService', () => {
  let service: DatasetsService;
  beforeEach(waitForAsync(() => {
    const configMock = { baseUrl: 'testUrl/' };
    TestBed.configureTestingModule({
      imports: [StoreModule.forRoot({}), RouterTestingModule],
      providers: [
        DatasetsService,
        UsersService,
        {provide: ConfigService, useValue: configMock},
        { provide: APP_BASE_HREF, useValue: '' },
        provideHttpClient(),
        provideHttpClientTesting()
      ],
      declarations: [],
    }).compileComponents();

    service = TestBed.inject(DatasetsService);
  }));

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should fetch datasets', async() => {
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of('fakeResponse'));

    await lastValueFrom(service.getDatasets());
    // eslint-disable-next-line jest/prefer-strict-equal
    expect(httpGetSpy.mock.calls).toEqual([['testUrl/datasets', {withCredentials: true}]]);
  });

  it('should get dataset', async() => {
    const datasetFromJsonSpy = jest.spyOn(Dataset, 'fromDataset');
    datasetFromJsonSpy.mockReturnValue(datasetMock);
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of(datasetMock));
    jest.clearAllMocks();

    const response = await lastValueFrom(service.getDataset('geneSymbol').pipe(take(1)));
    expect(response).toBe(datasetMock);
  });
});
