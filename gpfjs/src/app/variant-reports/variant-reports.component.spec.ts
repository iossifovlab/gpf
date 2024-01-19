import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PeopleCounterRowPipe, VariantReportsComponent } from './variant-reports.component';
import { FormsModule } from '@angular/forms';
import { VariantReportsService } from './variant-reports.service';
import { Observable, lastValueFrom, of } from 'rxjs';
import { ActivatedRoute, Router } from '@angular/router';
import { DatasetsService } from 'app/datasets/datasets.service';
import { PerfectlyDrawablePedigreeService } from 'app/perfectly-drawable-pedigree/perfectly-drawable-pedigree.service';
import { ResizeService } from 'app/table/resize.service';
import { DenovoReport, FamilyCounter, PedigreeCounter, PedigreeTable } from './variant-reports';
import { PedigreeData } from 'app/genotype-preview-model/genotype-preview';
import { HttpResponse } from '@angular/common/http';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { ConfigService } from 'app/config/config.service';

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
    this.params = {dataset: this.datasetId, get: () => ''};
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
            getChildrenCounter: function() {
              return 0;
            }
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
        ConfigService,
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
    component['chunkPedigrees'] = function(a, b) {
      return null;
    };
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should not have denovo', () => {
    expect(component).toBeTruthy();
    expect(component.currentDenovoReport).toBeUndefined();
  });

  it('should initialize pedigree tags', async() => {
    component.ngOnInit();
    const tags = await lastValueFrom(variantReportsServiceMock.getTags());
    expect(component.tags).toStrictEqual(tags);
    expect(component.orderedTagList).toStrictEqual(tags);
    expect(component.tagsModalsNumberOfCols).toBe(2);
    expect(component.tagsModalsNumberOfRows).toBe(5);
  });

  it('should update selected pedigree tags', () => {
    component.selectedTags = ['tag1', 'tag2', 'tag3'];
    const updatePedigreesTable = jest.spyOn(component, 'updateTagFilters')
      .mockImplementation(() => null);

    const updateFamiliesCountMock = jest.spyOn(component, 'updateFamiliesCount')
      .mockImplementation(() => null);

    const updateSelectedTagsListMock = jest.spyOn(component, 'updateSelectedTagsList');

    component.selectFilter('tag4');
    expect(component.filtersButtonsState['tag4']).toBe(1);
    expect(updateSelectedTagsListMock).toHaveBeenCalledWith('tag4');
    expect(updatePedigreesTable).toHaveBeenCalledWith();
    expect(updateFamiliesCountMock).toHaveBeenCalledWith();
    expect(component.selectedTags).toStrictEqual(['tag1', 'tag2', 'tag3', 'tag4']);
    expect(component.tagsHeader).toBe('tag1 and tag2 and tag3 and tag4');

    component.selectFilter('tag4');
    expect(component.filtersButtonsState['tag4']).toBe(0);
    expect(updateSelectedTagsListMock).toHaveBeenCalledWith('tag4');
    expect(updatePedigreesTable).toHaveBeenCalledWith();
    expect(updateFamiliesCountMock).toHaveBeenCalledWith();
    expect(component.selectedTags).toStrictEqual(['tag1', 'tag2', 'tag3']);
    expect(component.tagsHeader).toBe('tag1 and tag2 and tag3');
  });

  it('should update deselected pedigree tags', () => {
    component.deselectedTags = ['tag1', 'tag2'];
    const updatePedigreesTable = jest.spyOn(component, 'updateTagFilters')
      .mockImplementation(() => null);

    const updateFamiliesCountMock = jest.spyOn(component, 'updateFamiliesCount')
      .mockImplementation(() => null);

    const updateDeselectedTagsListMock = jest.spyOn(component, 'updateDeselectedTagsList');

    component.deselectFilter('tag3');
    expect(component.filtersButtonsState['tag3']).toBe(-1);
    expect(updateDeselectedTagsListMock).toHaveBeenCalledWith('tag3');
    expect(updatePedigreesTable).toHaveBeenCalledWith();
    expect(updateFamiliesCountMock).toHaveBeenCalledWith();
    expect(component.deselectedTags).toStrictEqual(['tag1', 'tag2', 'tag3']);
    expect(component.tagsHeader).toBe('not tag1 and not tag2 and not tag3');

    component.deselectFilter('tag3');
    expect(component.filtersButtonsState['tag3']).toBe(0);
    expect(updateDeselectedTagsListMock).toHaveBeenCalledWith('tag3');
    expect(updatePedigreesTable).toHaveBeenCalledWith();
    expect(updateFamiliesCountMock).toHaveBeenCalledWith();
    expect(component.deselectedTags).toStrictEqual(['tag1', 'tag2']);
    expect(component.tagsHeader).toBe('not tag1 and not tag2');
  });

  it('should test mixing selecting and deselecting pedigree tags', () => {
    const updatePedigreesTable = jest.spyOn(component, 'updateTagFilters')
      .mockImplementation(() => null);

    const updateFamiliesCountMock = jest.spyOn(component, 'updateFamiliesCount')
      .mockImplementation(() => null);

    component.selectFilter('tag1');
    component.deselectFilter('tag2');
    component.selectFilter('tag3');
    component.deselectFilter('tag4');
    expect(component.selectedTags).toStrictEqual(['tag1', 'tag3']);
    expect(component.deselectedTags).toStrictEqual(['tag2', 'tag4']);
    expect(component.tagsHeader).toBe('tag1 and tag3 and not tag2 and not tag4');
  });

  it('should test mode "Or" and "And"', () => {
    const pedigreeCounters: PedigreeCounter[] = [];
    pedigreeCounters.push(new PedigreeCounter(null, null, null, null, ['tag1', 'tag2', 'tag3', 'tag4']));
    pedigreeCounters.push(new PedigreeCounter(null, null, null, null, ['tag2', 'tag3']));
    pedigreeCounters.push(new PedigreeCounter(null, null, null, null, ['tag1', 'tag5']));

    component.familiesCounters = [new FamilyCounter(pedigreeCounters, null, null, null)];

    component.pedigreeTables = [
      new PedigreeTable([pedigreeCounters], null, null, null)];

    component.currentPedigreeTable = new PedigreeTable([pedigreeCounters], null, null, null);

    const updatePedigreesMock = jest.spyOn(component, 'updatePedigrees');

    // mode And
    component.selectFilter('tag1');
    expect(updatePedigreesMock).toHaveBeenCalledWith(
      {
        null: [
          new PedigreeCounter(null, null, null, null, ['tag1', 'tag2', 'tag3', 'tag4']),
          new PedigreeCounter(null, null, null, null, ['tag1', 'tag5'])
        ]
      }
    );

    component.deselectFilter('tag4');
    expect(updatePedigreesMock).toHaveBeenLastCalledWith(
      {
        null: [new PedigreeCounter(null, null, null, null, ['tag1', 'tag5'])]
      }
    );

    // mode Or
    component.clearFilters();
    component.tagIntersection = false;
    component.selectFilter('tag5');
    expect(updatePedigreesMock).toHaveBeenCalledWith(
      {
        null: [
          new PedigreeCounter(null, null, null, null, ['tag1', 'tag5'])
        ]
      }
    );

    component.deselectFilter('tag4');
    expect(updatePedigreesMock).toHaveBeenLastCalledWith(
      {
        null: [
          new PedigreeCounter(null, null, null, null, ['tag2', 'tag3']),
          new PedigreeCounter(null, null, null, null, ['tag1', 'tag5'])

        ]
      }
    );
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

  it('should remove all filters in modal with pedigree tags', () => {
    const updatePedigreesTable = jest.spyOn(component, 'updateTagFilters')
      .mockImplementation(() => null);

    const pedigreeCounters: PedigreeCounter[] = [];
    pedigreeCounters.push(new PedigreeCounter(null, null, null, null, ['tag1', 'tag2', 'tag3', 'tag4']));
    pedigreeCounters.push(new PedigreeCounter(null, null, null, null, ['tag2', 'tag3']));
    pedigreeCounters.push(new PedigreeCounter(null, null, null, null, ['tag1', 'tag5']));

    component.familiesCounters = [new FamilyCounter(pedigreeCounters, null, null, null)];

    component.pedigreeTables = [
      new PedigreeTable([pedigreeCounters], null, null, null)];

    component.currentPedigreeTable = new PedigreeTable([pedigreeCounters], null, null, null);

    component.selectedTags = ['tag1', 'tag2'];
    component.deselectedTags = ['tag3', 'tag4'];
    component.tagsHeader = 'tag1 and tag2 and not tag3 and not tag4';
    component.clearFilters();

    expect(component.selectedTags).toHaveLength(0);
    expect(component.tagsHeader).toBe('');
    expect(updatePedigreesTable).toHaveBeenCalledWith();
  });

  it('should test count of families in families by pedigree', () => {
    component.ngOnInit();
    const pedigresMock = [
      [new PedigreeCounter(1, 'mock1', [], 12, [])],
      [null],
      [new PedigreeCounter(2, 'mock2', [], 8, [])]
    ];
    const currentTableMock = new PedigreeTable(pedigresMock, [], '', undefined);

    component.currentPedigreeTable = currentTableMock;
    component.updateFamiliesCount();
    expect(component.familiesCount).toBe(20);
  });
});
