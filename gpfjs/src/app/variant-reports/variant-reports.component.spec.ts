import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PeopleCounterRowPipe, VariantReportsComponent } from './variant-reports.component';
import { FormsModule } from '@angular/forms';
import { VariantReportsService } from './variant-reports.service';
import { Observable, lastValueFrom, of } from 'rxjs';
import { ActivatedRoute, Router } from '@angular/router';
import { DatasetsService } from 'app/datasets/datasets.service';
import { PerfectlyDrawablePedigreeService } from 'app/perfectly-drawable-pedigree/perfectly-drawable-pedigree.service';
import { ResizeService } from 'app/table/resize.service';
import { DenovoReport, PedigreeCounter } from './variant-reports';
import { PedigreeData } from 'app/genotype-preview-model/genotype-preview';
import { HttpResponse } from '@angular/common/http';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import * as lodash from 'lodash';

class MockDatasetsService {
  public getSelectedDataset(): object {
    return {accessRights: true, commonReport: {enabled: true}};
  }
  public getSelectedDatasetObservable(): object {
    return of({accessRights: true, commonReport: {enabled: true}});
  }
  public getDatasetsLoadedObservable = function() {
    return of();
  };
  public getDataset(): Observable<any> {
    return of({accessRights: true, commonReport: {enabled: true}});
  }
}

class MockDatasetsDenovoService {
  public getSelectedDataset(): object {
    return {id: 'Denovo', accessRights: true, commonReport: {enabled: true}};
  }
  public getSelectedDatasetObservable(): object {
    return of({id: 'Denovo', accessRights: true, commonReport: {enabled: true}});
  }
  public getDatasetsLoadedObservable = function() {
    return of();
  };
  public getDataset(): Observable<any> {
    return of({id: 'Denovo', accessRights: true, commonReport: {enabled: true}});
  }
}

class ResizeServiceMock {
  public addResizeEventListener(): null {
    return null;
  }
  public removeResizeEventListener(): null {
    return null;
  }
}

class MockActivatedRoute {
  private datasetId: string;

  public params: object;
  public parent: object;
  public queryParamMap: Observable<object>;

  public constructor(datasetId: string = 'test_dataset') {
    this.datasetId = datasetId;
    this.params = {dataset: this.datasetId, get: () => { return '' }};
    this.parent = {params: of(this.params)};
    this.queryParamMap = of(this.params);
  }
}

class VariantReportsServiceMock {
  private variantsUrl = 'common_reports/studies/';
  private downloadUrl = 'common_reports/families_data/';
  private datasetId: string;

  public constructor(datasetId: string = 'test_dataset') {
    this.datasetId = datasetId;
  }

  public getVariantReport(datasetId: string): Observable<any> {
    const pedigreeCounter: PedigreeCounter = new PedigreeCounter(1, 'groupName',
      [
        new PedigreeData('identifier', 'id', 'mother', 'father',
          'gender', 'role', 'color', [1, 2], true, 'label', 'smallLabel')
      ], 1, ['tag1', 'tag2']);
    const denovoReport: DenovoReport | null = null;

    const variantReport = {
      id: this.datasetId,
      studyName: this.datasetId,
      studyDescription: '',
      familyReport: {
        familiesCounters: [
          {
            familyCounter: [
              {
                pedigreeCounters: pedigreeCounter
              }
            ],
            groupName: 'test',
            phenotypes: ['unaffected', 'affected'],
            legend: {
              legendItems: [
                {
                  id: 'affected',
                  name: 'affected',
                  color: '#e35252'
                },
                {
                  id: 'unaffected',
                  name: 'unaffected',
                  color: '#ffffff'
                },
                {
                  id: 'unspecified',
                  name: 'unspecified',
                  color: '#aaaaaa'
                },
                {
                  id: 'missing-person',
                  name: 'missing-person',
                  color: '#e0e0e0'
                },
              ]
            }
          }
        ],
        familiesTotal: 1,
      },
      peopleReport: {
        peopleCounters: [
          {
            groupCounters: [
              {
                column: 'prb',
                childrenCounters: [
                  {
                    row: 'people_male',
                    column: 'prb',
                    children: 5
                  },
                  {
                    row: 'people_female',
                    column: 'prb',
                    children: 0
                  },
                  {
                    row: 'people_total',
                    column: 'prb',
                    children: 5
                  },
                ]
              },
              {
                column: 'mom',
                childrenCounters: [
                  {
                    row: 'people_male',
                    column: 'mom',
                    children: 5
                  },
                  {
                    row: 'people_female',
                    column: 'mom',
                    children: 0
                  },
                  {
                    row: 'people_total',
                    column: 'mom',
                    children: 5
                  },
                ]
              },
              {
                column: 'sib',
                childrenCounters: [
                  {
                    row: 'people_male',
                    column: 'sib',
                    children: 5
                  },
                  {
                    row: 'people_female',
                    column: 'sib',
                    children: 0
                  },
                  {
                    row: 'people_total',
                    column: 'sib',
                    children: 5
                  },
                ]
              },
              {
                column: 'dad',
                childrenCounters: [
                  {
                    row: 'people_male',
                    column: 'dad',
                    children: 5
                  },
                  {
                    row: 'people_female',
                    column: 'dad',
                    children: 0
                  },
                  {
                    row: 'people_total',
                    column: 'dad',
                    children: 5
                  },
                ]
              },
            ],
            groupName: 'Role',
            rows: ['people_male', 'people_female', 'people_total'],
            columns: ['prb', 'mom', 'sib', 'dad'],
            getChildrenCounter: function() { return 0 }
          }
        ],
      },
      denovoReport: denovoReport
    };

    if (datasetId === 'Denovo') {
      variantReport.denovoReport = {
        tables: [
          {
            rows: [
              {
                effectType: 'nonsynonymous',
                data: [
                  {
                    column: 'prb',
                    numberOfObservedEvents: 2,
                    numberOfChildrenWithEvent: 2,
                    observedRatePerChild: 0.4,
                    percentOfChildrenWithEvents: 0.4
                  }
                ]
              },
              {
                effectType: 'Missense',
                data: [
                  {
                    column: 'prb',
                    numberOfObservedEvents: 2,
                    numberOfChildrenWithEvent: 2,
                    observedRatePerChild: 0.4,
                    percentOfChildrenWithEvents: 0.4
                  }
                ]
              },
              {
                effectType: 'Synonymous',
                data: [
                  {
                    column: 'prb',
                    numberOfObservedEvents: 3,
                    numberOfChildrenWithEvent: 2,
                    observedRatePerChild: 0.6,
                    percentOfChildrenWithEvents: 0.4
                  }
                ]
              },
            ],
            groupName: 'Role',
            columns: ['prb'],
            effectGroups: ['nonsynonymous'],
            effectTypes: ['Missense', 'Synonymous'],
          }
        ]
      };
    }
    return of(variantReport);
  }

  public getDownloadLink(): string {
    return '';
  }

  public getDownloadLinkTags(): string {
    return '';
  }

  public getTags(): Observable<string[]> {
    return of(['tag1', 'tag2', 'tag3', 'tag4', 'tag5', 'tag6', 'tag7', 'tag8', 'tag9', 'tag10']);
  }

  public downloadFamilies(): Observable<HttpResponse<Blob>> {
    return of([] as any);
  }
}

describe('VariantReportsComponent', () => {
  let component: VariantReportsComponent;
  let fixture: ComponentFixture<VariantReportsComponent>;
  const variantReportsServiceMock = new VariantReportsServiceMock();

  beforeEach(() => {
    const activatedRouteMock = new MockActivatedRoute();
    const datasetsServiceMock = new MockDatasetsService();
    TestBed.configureTestingModule({
      declarations: [VariantReportsComponent, PeopleCounterRowPipe],
      imports: [FormsModule],
      providers: [
        { provide: VariantReportsService, useValue: variantReportsServiceMock },
        { provide: ActivatedRoute, useValue: activatedRouteMock },
        { provide: Router, useValue: {} },
        { provide: DatasetsService, useValue: datasetsServiceMock },
        { provide: PerfectlyDrawablePedigreeService },
        { provide: ResizeService, useClass: ResizeServiceMock },
        NgbModal
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(VariantReportsComponent);
    component = fixture.componentInstance;

    //Stubbing the function to reduce mock test data
    component['chunkPedigrees'] = function(a, b) { return null; };
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should not have denovo', () => {
    expect(component).toBeTruthy();
    expect(component.currentDenovoReport).toBeUndefined();
  });

  it.todo('should test download');

  it('should initialize pedigree tags', async() => {
    component.ngOnInit();
    const tags = await lastValueFrom(variantReportsServiceMock.getTags());
    expect(component.tags).toStrictEqual(tags);
    expect(component.orderedTagList).toStrictEqual(tags);
    expect(component.tagsModalsNumberOfCols).toBe(2);
    expect(component.tagsModalsNumberOfRows).toBe(5);
  });

  it('should update selected pedigree tags', () => {
    component.selectedItems = ['tag1', 'tag2', 'tag3', 'tag4', 'tag5'];
    const updatePedigreesTable = jest.spyOn(component, 'updateTagFilters')
      .mockImplementation(() => null);

    component.updateSelectedTags('tag6');
    expect(component.selectedItems).toStrictEqual(['tag1', 'tag2', 'tag3', 'tag4', 'tag5', 'tag6']);
    expect(component.selectedTagsHeader).toBe('tag1, tag2, tag3, tag4, tag5, tag6');
    expect(updatePedigreesTable).toHaveBeenCalledWith();

    component.updateSelectedTags('tag3');
    expect(component.selectedItems).toStrictEqual(['tag1', 'tag2', 'tag4', 'tag5', 'tag6']);
    expect(component.selectedTagsHeader).toBe('tag1, tag2, tag4, tag5, tag6');
    expect(updatePedigreesTable).toHaveBeenCalledWith();
  });

  it('should open modal with pedigree tags', () => {
    const openModalSpy = jest.spyOn(component.modalService, 'open')
      .mockImplementation(() => null);

    component.openModal();
    expect(openModalSpy).toHaveBeenCalledWith(
      component.tagsModal,
      {animation: false, centered: true, windowClass: 'tags-modal'}
    );
  });

  it('should search in modal with pedigree tags', () => {
    const tagsArr = ['ABC', 'BCA', 'CAB'];
    component.tags = lodash.cloneDeep(tagsArr);
    component.search(' ab   ');
    expect(component.searchValue).toBe('ab');
    expect(component.tags).toStrictEqual(tagsArr);
    expect(component.orderedTagList).toStrictEqual(['ABC', 'CAB', 'BCA']);

    component.search(' bc   ');
    expect(component.searchValue).toBe('bc');
    expect(component.tags).toStrictEqual(tagsArr);
    expect(component.orderedTagList).toStrictEqual(['ABC', 'BCA', 'CAB']);

    component.search(' ca   ');
    expect(component.searchValue).toBe('ca');
    expect(component.tags).toStrictEqual(tagsArr);
    expect(component.orderedTagList).toStrictEqual(['BCA', 'CAB', 'ABC']);

    component.search('    ');
    expect(component.searchValue).toBe('');
    expect(component.tags).toStrictEqual(tagsArr);
    expect(component.orderedTagList).toStrictEqual(['ABC', 'BCA', 'CAB']);
  });

  it('should uncheck all checked tags in modal with pedigree tags', () => {
    const updatePedigreesTable = jest.spyOn(component, 'updateTagFilters')
      .mockImplementation(() => null);
    component.selectedItems = ['tag1', 'tag2', 'tag3'];
    component.selectedTagsHeader = 'tag1, tag2, tag3';
    component.uncheckAll();

    expect(component.selectedItems).toHaveLength(0);
    expect(component.selectedTagsHeader).toBe('');
    expect(updatePedigreesTable).toHaveBeenCalledWith();
  });
});
