import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { UsersService } from 'app/users/users.service';
import { MarkdownService } from 'ngx-markdown';
import { DatasetDescriptionComponent } from './dataset-description.component';
import { APP_BASE_HREF } from '@angular/common';
import { Store, StoreModule } from '@ngrx/store';
import { Observable, of } from 'rxjs';
import { Dataset, GeneBrowser, DatasetHierarchy } from 'app/datasets/datasets';
import { datasetIdReducer } from 'app/datasets/datasets.state';

class MarkdownServiceMock {
  public compile = (): void => null;
  public getSource = (): void => null;
  public highlight = (): void => null;
  public renderKatex = (): void => null;
}

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
  null,
  null,
  new GeneBrowser(true, 'frequencyCol1', 'frequencyName1', 'effectCol1', 'locationCol1', 5, 6, true),
  false,
  'genome1',
  true
);

const datasetHierarchyMock = new DatasetHierarchy('id1', 'hierarchy1', true, []);
const invisibleDatasetHierarchyMock = new DatasetHierarchy('id2', 'hierarchy2', true, []);
const visibleDatasetsMock = ['id1'];

class DatasetsServiceMock {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  public getDataset(datasetId: string): Observable<Dataset> {
    return of(datasetMock);
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  public getSingleDatasetHierarchy(datasetId: string): Observable<DatasetHierarchy> {
    return of(datasetHierarchyMock);
  }

  public getVisibleDatasets(): Observable<string[]> {
    return of(visibleDatasetsMock);
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  public getDatasetDescription(datasetId: string): Observable<string> {
    return of('## Dataset1\n description paragraph1\n\n description paragraph2');
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  public writeDatasetDescription(datasetId: string, text: string): Observable<object> {
    return of({});
  }
}

describe('DatasetDescriptionComponent', () => {
  let component: DatasetDescriptionComponent;
  let fixture: ComponentFixture<DatasetDescriptionComponent>;
  const datasetsServiceMock = new DatasetsServiceMock();
  let store: Store;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [DatasetDescriptionComponent],
      providers: [
        { provide: ActivatedRoute, useValue: new ActivatedRoute() },
        { provide: DatasetsService, useValue: datasetsServiceMock },
        UsersService,
        ConfigService,
        { provide: MarkdownService, useClass: MarkdownServiceMock },
        { provide: APP_BASE_HREF, useValue: '' }
      ],
      imports: [RouterTestingModule, HttpClientTestingModule, StoreModule.forRoot({datasetId: datasetIdReducer})]
    }).compileComponents();

    store = TestBed.inject(Store);
    jest.spyOn(store, 'select').mockReturnValue(of('id1'));

    fixture = TestBed.createComponent(DatasetDescriptionComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should set description hierarchy', () => {
    const getSingleDatasetHierarchySpy = jest.spyOn(datasetsServiceMock, 'getSingleDatasetHierarchy');
    const setDescriptionsAndVisibilitySpy = jest.spyOn(component, 'setDescriptionsAndVisibility')
      .mockImplementation(() => ({}));

    component.ngOnInit();
    expect(component.editable).toBe(true);
    expect(getSingleDatasetHierarchySpy).toHaveBeenCalledWith('id1');
    expect(setDescriptionsAndVisibilitySpy).toHaveBeenCalledWith(datasetHierarchyMock, visibleDatasetsMock);
    expect(component.descriptionHierarchy).toBe(datasetHierarchyMock);
  });

  it('should set descriptions and visibility', () => {
    const getDatasetDescriptionSpy = jest.spyOn(datasetsServiceMock, 'getDatasetDescription');

    component.setDescriptionsAndVisibility(datasetHierarchyMock, visibleDatasetsMock);
    expect(getDatasetDescriptionSpy).toHaveBeenCalledWith('id1');

    expect(datasetHierarchyMock.description).toBe('## Dataset1\n description paragraph1\n\n description paragraph2');
    expect(datasetHierarchyMock.visibility).toBe(true);
  });

  it('should not set descriptions and visibility', () => {
    const getDatasetDescriptionSpy = jest.spyOn(datasetsServiceMock, 'getDatasetDescription');

    component.setDescriptionsAndVisibility(invisibleDatasetHierarchyMock, visibleDatasetsMock);
    expect(getDatasetDescriptionSpy).toHaveBeenCalledWith('id2');

    expect(invisibleDatasetHierarchyMock.description).toBeUndefined();
    expect(invisibleDatasetHierarchyMock.visibility).toBe(false);
  });


  it('should get first paragraph', () => {
    const description = '## SSC CSHL WGS\n\n' +
    '*De novo* and transmitted substitutions and indel calls generated by the' +
    'Iossifov lab from the whole-genome sequencing from 2,379 SSC families.' +
    'NYGC generated the whole-genome data from DNA extracted from whole blood.' +
    '\n\n' +
    '### Disclaimer' +
    '\n\n' +
    'The use of the Simons Simplex and Simons Searchlight Collections is limited to' +
    'projects that advance the study of autism and related developmental disorders.' +
    'Questions on consents for the Simons Simplex Collection and the Simons' +
    'Searchlight should be directed to collections@sfari.org.';

    expect(component.getFirstParagraph(description)).toBe(
      '*De novo* and transmitted substitutions and indel calls generated by the' +
      'Iossifov lab from the whole-genome sequencing from 2,379 SSC families.' +
      'NYGC generated the whole-genome data from DNA extracted from whole blood.');
  });

  it('should get first paragraph when no title', () => {
    const description =
    '*De novo* and transmitted substitutions and indel calls generated by the' +
    'Iossifov lab from the whole-genome sequencing from 2,379 SSC families.' +
    'NYGC generated the whole-genome data from DNA extracted from whole blood.' +
    '\n\n' +
    '### Disclaimer' +
    '\n\n' +
    'The use of the Simons Simplex and Simons Searchlight Collections is limited to' +
    'projects that advance the study of autism and related developmental disorders.' +
    'Questions on consents for the Simons Simplex Collection and the Simons' +
    'Searchlight should be directed to collections@sfari.org.';

    expect(component.getFirstParagraph(description)).toBe(
      '*De novo* and transmitted substitutions and indel calls generated by the' +
      'Iossifov lab from the whole-genome sequencing from 2,379 SSC families.' +
      'NYGC generated the whole-genome data from DNA extracted from whole blood.');
  });

  it('should write description', () => {
    const writeDatasetDescriptionSpy = jest.spyOn(datasetsServiceMock, 'writeDatasetDescription');

    component.writeDataset('id1', 'description');
    expect(writeDatasetDescriptionSpy).toHaveBeenCalledWith('id1', 'description');
  });
});
