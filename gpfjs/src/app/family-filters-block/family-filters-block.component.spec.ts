import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { FamilyFiltersBlockComponent } from './family-filters-block.component';
import { DenovoReport, FamilyCounter, PedigreeCounter } from 'app/variant-reports/variant-reports';
import { Observable, of } from 'rxjs';
import { PedigreeData } from 'app/genotype-preview-model/genotype-preview';
import { VariantReportsService } from 'app/variant-reports/variant-reports.service';
import { HttpResponse } from '@angular/common/http';
import { DatasetsService } from 'app/datasets/datasets.service';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ConfigService } from 'app/config/config.service';
import { UsersService } from 'app/users/users.service';
import { APP_BASE_HREF } from '@angular/common';
import { Dataset, GenotypeBrowser } from 'app/datasets/datasets';
import { Store, StoreModule } from '@ngrx/store';
import { datasetIdReducer } from 'app/datasets/datasets.state';
import { familyIdsReducer, resetFamilyIds } from 'app/family-ids/family-ids.state';
import { familyTagsReducer, resetFamilyTags } from 'app/family-tags/family-tags.state';
import { personFiltersReducer, resetFamilyFilterStates } from 'app/person-filters/person-filters.state';
import { PersonFilterState, CategoricalSelection } from 'app/person-filters/person-filters';

const pedigreeCounters: PedigreeCounter[] = [
  new PedigreeCounter(1, 'groupName',
    [
      new PedigreeData('identifier', 'id', 'mother', 'father',
        'gender', 'role', 'color', [1, 2], true, 'label', 'smallLabel')
    ],
    253,
    ['tag1', 'tag2']
  ),
  new PedigreeCounter(2, 'groupName',
    [
      new PedigreeData('identifier', 'id', 'mother', 'father',
        'gender', 'role', 'color', [1, 2], true, 'label', 'smallLabel')
    ],
    100,
    ['tag2', 'tag3']
  )
];

class VariantReportsServiceMock {
  private variantsUrl = 'common_reports/studies/';
  private downloadUrl = 'common_reports/families_data/';
  private datasetId: string;

  public constructor(datasetId: string = 'test_dataset') {
    this.datasetId = datasetId;
  }

  public getVariantReport(datasetId: string): Observable<object> {
    const denovoReport: DenovoReport | null = null;

    const variantReport = {
      id: this.datasetId,
      studyName: this.datasetId,
      studyDescription: '',
      familyReport: {
        familiesCounters: [
          {
            pedigreeCounters: pedigreeCounters,
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
            getChildrenCounter: (): number => 0
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

  public getTags(): Observable<object> {
    return of(['tag1', 'tag2', 'tag3', 'tag4', 'tag5', 'tag6', 'tag7', 'tag8', 'tag9', 'tag10']);
  }

  public downloadFamilies(): Observable<HttpResponse<Blob>> {
    return of([] as any);
  }
}

describe('FamilyFiltersBlockComponent', () => {
  let component: FamilyFiltersBlockComponent;
  let fixture: ComponentFixture<FamilyFiltersBlockComponent>;
  const variantReportsServiceMock = new VariantReportsServiceMock();
  let store: Store;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [FamilyFiltersBlockComponent],
      imports: [
        NgbNavModule,
        StoreModule.forRoot({
          datasetId: datasetIdReducer,
          familyIds: familyIdsReducer,
          familyTags: familyTagsReducer,
          personFilters: personFiltersReducer
        })
      ],
      providers: [
        DatasetsService,
        ConfigService,
        UsersService,
        { provide: VariantReportsService, useValue: variantReportsServiceMock },
        { provide: APP_BASE_HREF, useValue: '' },
        provideHttpClientTesting()
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(FamilyFiltersBlockComponent);
    component = fixture.componentInstance;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);

    // eslint-disable-next-line @stylistic/max-len
    const genotypeBrowserMock = new GenotypeBrowser(true, true, true, true, true, true, true, true, true, [], [], [], null, null, null, null, 0, false, false);
    // eslint-disable-next-line @stylistic/max-len
    const datasetMock = new Dataset('datasetId', 'dataset', [], true, [], [], [], '', true, true, true, true, {enabled: true}, genotypeBrowserMock, null, null, null, true, null, false);
    component.dataset = datasetMock;

    jest.useFakeTimers();
    const timer: ReturnType<typeof setTimeout> = setTimeout(() => '');
    jest.spyOn(global, 'setTimeout').mockImplementationOnce((fn) => {
      fn();
      return timer;
    });
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should test count of families in families by pedigree', () => {
    component.ngOnInit();
    component.setFamiliesCount();
    expect(component.selectedFamiliesCount).toBe(353);
  });

  it('should get family tags', () => {
    const onResizeSpy = jest.spyOn(component, 'onResize');
    const setFamiliesCountSpy = jest.spyOn(component, 'setFamiliesCount');
    component.ngOnInit();

    expect(component.showAdvancedButton).toBe(true);
    expect(component.tags).toStrictEqual(
      ['tag1', 'tag2', 'tag3', 'tag4', 'tag5', 'tag6', 'tag7', 'tag8', 'tag9', 'tag10']
    );

    expect(component.orderedTagList).toStrictEqual(
      ['tag1', 'tag2', 'tag3', 'tag4', 'tag5', 'tag6', 'tag7', 'tag8', 'tag9', 'tag10']
    );

    expect(component.familiesCounters).toStrictEqual(
      [
        {
          pedigreeCounters: pedigreeCounters,
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
      ]
    );

    expect(onResizeSpy).toHaveBeenCalledWith();
    expect(setFamiliesCountSpy).toHaveBeenCalledWith();
  });

  it('should get family ids from state and open Family ids tab', () => {
    fixture.detectChanges();
    const rxjs = jest.requireActual<typeof import('rxjs')>('rxjs');
    jest.spyOn(rxjs, 'combineLatest').mockReturnValueOnce(of([
      ['familyId1', 'familyId2'],
      {
        selectedFamilyTags: [],
        deselectedFamilyTags: [],
        tagIntersection: true,
      },
      {
        familyFilters: null,
        personFilters: null,
      }
    ]));

    const selectNavSpy = jest.spyOn(component.ngbNav, 'select').mockImplementation();

    component.ngAfterViewInit();
    jest.runAllTimers();

    expect(component.hasContent).toBe(true);
    expect(selectNavSpy).toHaveBeenCalledWith('familyIds');
    jest.useRealTimers();
  });

  it('should get family tags from state and open Family tags tab', () => {
    fixture.detectChanges();
    const rxjs = jest.requireActual<typeof import('rxjs')>('rxjs');
    jest.spyOn(rxjs, 'combineLatest').mockReturnValueOnce(of([
      [],
      {
        selectedFamilyTags: ['selectedTag1'],
        deselectedFamilyTags: [],
        tagIntersection: true,
      },
      {
        familyFilters: null,
        personFilters: null,
      }
    ]));

    const selectNavSpy = jest.spyOn(component.ngbNav, 'select').mockImplementation();

    component.ngAfterViewInit();
    jest.runAllTimers();

    expect(component.hasContent).toBe(true);
    expect(selectNavSpy).toHaveBeenCalledWith('familyTags');
    jest.useRealTimers();
  });

  it('should get person filters from state and open Advanced tab', () => {
    fixture.detectChanges();
    const rxjs = jest.requireActual<typeof import('rxjs')>('rxjs');
    jest.spyOn(rxjs, 'combineLatest').mockReturnValueOnce(of([
      [],
      {
        selectedFamilyTags: [],
        deselectedFamilyTags: [],
        tagIntersection: true,
      },
      {
        familyFilters: [
          new PersonFilterState(
            'familyName1',
            'categorical',
            'familyRole1',
            'familySource1',
            'familyFrom1',
            new CategoricalSelection(['selection1'])
          ),
          new PersonFilterState(
            'familyName2',
            'categorical',
            'familyRole2',
            'familySource2',
            'familyFrom2',
            new CategoricalSelection(['selection2'])
          )
        ],
        personFilters: null,
      }
    ]));

    const selectNavSpy = jest.spyOn(component.ngbNav, 'select').mockImplementation();

    component.ngAfterViewInit();
    jest.runAllTimers();

    expect(component.hasContent).toBe(true);
    expect(selectNavSpy).toHaveBeenCalledWith('advanced');
    jest.useRealTimers();
  });

  it('should clear all states when switching tab', () => {
    fixture.detectChanges();
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.onNavChange();

    expect(dispatchSpy).toHaveBeenCalledWith(resetFamilyTags());
    expect(dispatchSpy).toHaveBeenCalledWith(resetFamilyIds());
    expect(dispatchSpy).toHaveBeenCalledWith(resetFamilyFilterStates());
  });

  it('should update current family tags', () => {
    fixture.detectChanges();
    const setFamiliesCountSpy = jest.spyOn(component, 'setFamiliesCount');
    component.selectedTags = ['tag1'];
    component.deselectedTags = ['tag2'];
    component.updateTags({selected: ['tag3'], deselected: ['tag4']});

    expect(component.selectedTags).toStrictEqual(['tag3']);
    expect(component.deselectedTags).toStrictEqual(['tag4']);
    expect(setFamiliesCountSpy).toHaveBeenCalledWith();
  });

  it('should update intersection mode in family tags', () => {
    fixture.detectChanges();
    const setFamiliesCountSpy = jest.spyOn(component, 'setFamiliesCount');
    component.tagIntersection = false;
    component.updateMode(true);

    expect(component.tagIntersection).toBe(true);
    expect(setFamiliesCountSpy).toHaveBeenCalledWith();
  });

  it('should set families count when there are family counters and tag intersection', () => {
    component.tagIntersection = true;
    component.selectedTags = ['tag3'];
    component.deselectedTags = ['tag1'];
    component.familiesCounters = [new FamilyCounter(pedigreeCounters, 'groupName', [], null)];
    component.setFamiliesCount();
    expect(component.selectedFamiliesCount).toBe(100);
  });

  it('should set families count when there are family counters and no tag intersection', () => {
    component.tagIntersection = false;
    component.selectedTags = ['tag1'];
    component.deselectedTags = ['tag2'];
    component.familiesCounters = [new FamilyCounter(pedigreeCounters, 'groupName', [], null)];
    component.setFamiliesCount();
    expect(component.selectedFamiliesCount).toBe(253);
  });

  it('should not set families count when there are no family counters', () => {
    jest.clearAllMocks();
    component.familiesCounters = undefined;
    component.setFamiliesCount();
    expect(component.selectedFamiliesCount).toBeUndefined();
  });
});
