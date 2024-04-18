import { GeneProfilesTableComponent } from './gene-profiles-table.component';
import { GeneProfilesTableConfig } from './gene-profiles-table';
import { plainToClass } from 'class-transformer';
import { Observable, of } from 'rxjs';
import { cloneDeep } from 'lodash';
import { GeneProfilesTableService } from './gene-profiles-table.service';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { NgxsModule } from '@ngxs/store';
import { GeneProfilesState } from './gene-profiles-table.state';

const column1 = {
  clickable: 'createTab',
  columns: [],
  displayName: 'column 1',
  displayVertical: false,
  id: 'column1',
  meta: null,
  sortable: false,
  visible: true
};

const column21 = {
  clickable: 'createTab',
  columns: [],
  displayName: 'column 21',
  displayVertical: false,
  id: 'column21',
  meta: null,
  sortable: false,
  visible: true
};
const column22 = {
  clickable: 'createTab',
  columns: [],
  displayName: 'column 22',
  displayVertical: false,
  id: 'column22',
  meta: null,
  sortable: false,
  visible: true
};

const column2 = {
  clickable: 'createTab',
  columns: [column21, column22],
  displayName: 'column 2',
  displayVertical: false,
  id: 'column2',
  meta: null,
  sortable: false,
  visible: true
};

const column311 = {
  clickable: 'createTab',
  columns: [],
  displayName: 'column 311',
  displayVertical: false,
  id: 'column311',
  meta: null,
  sortable: false,
  visible: true
};

const column312 = {
  clickable: 'createTab',
  columns: [],
  displayName: 'column 312',
  displayVertical: false,
  id: 'column312',
  meta: null,
  sortable: false,
  visible: true
};

const column31 = {
  clickable: 'createTab',
  columns: [column311, column312],
  displayName: 'column 31',
  displayVertical: false,
  id: 'column31',
  meta: null,
  sortable: false,
  visible: true
};

const column321 = {
  clickable: 'createTab',
  columns: [],
  displayName: 'column 321',
  displayVertical: false,
  id: 'column321',
  meta: null,
  sortable: false,
  visible: true
};

const column322 = {
  clickable: 'createTab',
  columns: [],
  displayName: 'column 322',
  displayVertical: false,
  id: 'column322',
  meta: null,
  sortable: false,
  visible: true
};

const column32 = {
  clickable: 'createTab',
  columns: [column321, column322],
  displayName: 'column 32',
  displayVertical: false,
  id: 'column32',
  meta: null,
  sortable: false,
  visible: true
};

const column3 = {
  clickable: 'createTab',
  columns: [column31, column32],
  displayName: 'column 3',
  displayVertical: false,
  id: 'column3',
  meta: null,
  sortable: false,
  visible: true
};

const configMock = plainToClass(GeneProfilesTableConfig, {
  defaultDataset: 'dataset1',
  pageSize: 3,
  columns: [
    column1,
    column2,
    column3
  ]
});

const gridData = [
  {
    id: 'column1',
    parent: undefined,
    gridColumn: '1',
    gridRow: '1 / 4',
    depth: 1
  },
  {
    id: 'column21',
    parent: 'column2',
    gridColumn: '2',
    gridRow: '2 / 4',
    depth: 2
  },
  {
    id: 'column22',
    parent: 'column2',
    gridColumn: '3',
    gridRow: '2 / 4',
    depth: 2
  },
  {
    id: 'column311',
    parent: 'column31',
    gridColumn: '4',
    gridRow: '3',
    depth: 3
  },
  {
    id: 'column312',
    parent: 'column31',
    gridColumn: '5',
    gridRow: '3',
    depth: 3
  },
  {
    id: 'column321',
    parent: 'column32',
    gridColumn: '6',
    gridRow: '3',
    depth: 3
  },
  {
    id: 'column322',
    parent: 'column32',
    gridColumn: '7',
    gridRow: '3',
    depth: 3
  }
];

/* eslint-disable */
const genesMock = [
  {
    'column1': 'value10',
    'column2.column21': 'value11',
    'column2.column22': 'value12',
    'column2.column23': 'value13',
    'column3.column31.column311': 'value14',
    'column3.column31.column312': 'value15',
    'column3.column32.column321': 'value16',
    'column3.column32.column322': 'value17',
    'column3.column33.column331': 'value18',
    'column3.column33.column332': 'value19'
  },
  {
    'column1': 'value20',
    'column2.column21': 'value21',
    'column2.column22': 'value22',
    'column2.column23': 'value23',
    'column3.column31.column311': 'value24',
    'column3.column31.column312': 'value25',
    'column3.column32.column321': 'value26',
    'column3.column32.column322': 'value27',
    'column3.column33.column331': 'value28',
    'column3.column33.column332': 'value29'
  },
  {
    'column1': 'value30',
    'column2.column21': 'value31',
    'column2.column22': 'value32',
    'column2.column23': 'value33',
    'column3.column31.column311': 'value34',
    'column3.column31.column312': 'value35',
    'column3.column32.column321': 'value36',
    'column3.column32.column322': 'value37',
    'column3.column33.column331': 'value38',
    'column3.column33.column332': 'value39'
  }
];
/* eslint-enable */

class GeneProfilesTableServiceMock {
  public getGenes(pageIndex: number, geneInput: string): Observable<Record<string, any>> {
    const res = cloneDeep(genesMock);
    if (geneInput) {
      res.forEach(gene => {
        gene['search'] = geneInput;
      });
    }
    return of(res);
  }
}

class MockActivatedRoute {
  public snapshot = {params: {genes: ''}};
}

describe('GeneProfilesTableComponent', () => {
  let component: GeneProfilesTableComponent;
  const geneProfilesTableServiceMock = new GeneProfilesTableServiceMock();
  const mockActivatedRoute = new MockActivatedRoute();
  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [GeneProfilesTableComponent],
      providers: [
        {provide: ActivatedRoute, useValue: mockActivatedRoute},
        {provide: GeneProfilesTableService, useValue: geneProfilesTableServiceMock}
      ],
      imports: [NgxsModule.forRoot([GeneProfilesState], {developmentMode: true})]
    }).compileComponents();

    const fixture = TestBed.createComponent(GeneProfilesTableComponent);
    component = fixture.componentInstance;

    component.sortingButtonsComponents = [];
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize', () => {
    component.sortBy = 'mockSort';

    component.ngOnInit();

    expect(component.defaultSortBy).toBe('mockSort');
  });

  it('should update when change happens', () => {
    component.ngOnChanges();
    expect(component.leaves).toBeUndefined();
    expect(component.pageIndex).toBe(0);
    expect(component.genes).toStrictEqual([]);

    component.config = cloneDeep(configMock);
    component.ngOnChanges();

    component.leaves.forEach((leaf, index) => {
      expect(leaf.id).toStrictEqual(gridData[index].id);
      expect(leaf.gridColumn).toStrictEqual(gridData[index].gridColumn);
      expect(leaf.gridRow).toStrictEqual(gridData[index].gridRow);
      expect(leaf.parent?.id).toStrictEqual(gridData[index].parent);
      expect(leaf.depth).toStrictEqual(gridData[index].depth);
    });
    expect(component.pageIndex > 1).toBeTruthy();
    expect(component.genes[0]).toStrictEqual(genesMock[0]);
    expect(component.genes[1]).toStrictEqual(genesMock[1]);
    expect(component.genes[2]).toStrictEqual(genesMock[2]);
  });

  it('should search', () => {
    component.config = cloneDeep(configMock);
    component.ngOnChanges();
    component.search('mockSearch');

    expect(component.geneInput).toBe('mockSearch');
    expect(component.genes[0]).toStrictEqual({search: 'mockSearch', ...genesMock[0]});
    expect(component.genes[1]).toStrictEqual({search: 'mockSearch', ...genesMock[1]});
    expect(component.genes[2]).toStrictEqual({search: 'mockSearch', ...genesMock[2]});
  });

  it('should update genes', () => {
    expect(component.genes).toStrictEqual([]);
    expect(component.pageIndex).toBe(0);
    component.updateGenes();
    expect(component.genes).toStrictEqual(genesMock);
    expect(component.pageIndex).toBe(1);
  });

  it('should reorder header', () => {
    component.config = cloneDeep(configMock);

    component.reorderHeader(['column3', 'column1', 'column2']);
    expect(component.config.columns[0].id).toBe('column3');
    expect(component.config.columns[1].id).toBe('column1');
    expect(component.config.columns[2].id).toBe('column2');

    const sortedLeaves = ['column311', 'column312', 'column321', 'column322', 'column1', 'column21', 'column22'];
    const sortedGridData = cloneDeep(gridData);
    sortedGridData.sort((a, b) => sortedLeaves.indexOf(a.id) - sortedLeaves.indexOf(b.id));
    // Update gridColumns to new order
    sortedGridData.forEach((leaf, index) => {
      leaf.gridColumn = `${index + 1}`;
    });

    component.leaves.forEach((leaf, index) => {
      expect(leaf.id).toBe(sortedGridData[index].id);
      expect(leaf.gridColumn).toBe(sortedGridData[index].gridColumn);
      expect(leaf.gridRow).toBe(sortedGridData[index].gridRow);
      expect(leaf.parent?.id).toBe(sortedGridData[index].parent);
      expect(leaf.depth).toBe(sortedGridData[index].depth);
    });
  });

  it('should sort genes', () => {
    component.config = cloneDeep(configMock);
    component.ngOnChanges();
    component.genes = undefined;

    component.sort('mockSortBy', 'mockOrderBy');
    expect(component.sortBy).toBe('mockSortBy');
    expect(component.orderBy).toBe('mockOrderBy');
    expect(component.genes[0]).toStrictEqual(genesMock[0]);
    expect(component.genes[1]).toStrictEqual(genesMock[1]);
    expect(component.genes[2]).toStrictEqual(genesMock[2]);
  });

  it('should toggle highlighted genes', () => {
    component.highlightedGenes = new Set(['gene1', 'gene2', 'gene3', 'gene4']);

    component.toggleHighlightGene('gene3');
    expect(component.highlightedGenes.has('gene3')).toBeFalsy();
    component.toggleHighlightGene('gene3');
    expect(component.highlightedGenes.has('gene3')).toBeTruthy();
    component.toggleHighlightGene('gene5');
    expect(component.highlightedGenes.has('gene5')).toBeTruthy();
  });

  it('should load single view tab for gene', () => {
    const openTabSpy = jest.spyOn(component, 'openTab');

    expect(component.hideTable).toBe(false);
    expect(component.currentTabString).toBe('all genes');

    component.loadSingleView('POGZ');
    expect(component.tabs).toStrictEqual(new Set(['POGZ']));

    expect(openTabSpy).toHaveBeenCalledWith('POGZ');

    component.closeTab('POGZ');
    expect(component.tabs).toStrictEqual(new Set([]));
  });

  it('should load single view tab when comparing', () => {
    const openTabSpy = jest.spyOn(component, 'openTab');

    expect(component.hideTable).toBe(false);
    expect(component.currentTabString).toBe('all genes');

    mockActivatedRoute.snapshot = {params: {genes: 'SPAST,DYRK1A,FOXP1'}};

    component.loadSingleView(new Set(['SPAST', 'DYRK1A', 'FOXP1']));
    expect(component.tabs).toStrictEqual(new Set(['DYRK1A,FOXP1,SPAST']));

    expect(openTabSpy).toHaveBeenCalledWith('DYRK1A,FOXP1,SPAST');
  });

  it('should go to already existing tab when opening single view', () => {
    const openTabSpy = jest.spyOn(component, 'openTab');

    mockActivatedRoute.snapshot = {params: {genes: 'SPAST,FOXP1,DYRK1A'}};

    component.loadSingleView(new Set(['SPAST', 'FOXP1', 'DYRK1A']));
    expect(component.tabs).toStrictEqual(new Set(['DYRK1A,FOXP1,SPAST']));
    expect(openTabSpy).toHaveBeenCalledWith('DYRK1A,FOXP1,SPAST');

    component.loadSingleView(new Set(['SPAST', 'DYRK1A', 'FOXP1']));
    expect(component.tabs).toStrictEqual(new Set(['DYRK1A,FOXP1,SPAST']));
    expect(openTabSpy).toHaveBeenCalledWith('DYRK1A,FOXP1,SPAST');
  });

  it('should open tab for single view', () => {
    component.openTab('POGZ');
    expect(component.hideTable).toBe(true);
    expect(component.currentTabGeneSet).toStrictEqual(new Set(['POGZ']));
    expect(component.currentTabString).toBe('POGZ');
    expect(window.location.pathname).toBe('/gene-profiles/POGZ');
  });

  it('should open tab for single view when comparing', () => {
    component.openTab('DYRK1A,FOXP1,SPAST');
    expect(component.hideTable).toBe(true);
    expect(component.currentTabGeneSet).toStrictEqual(new Set(['DYRK1A', 'FOXP1', 'SPAST']));
    expect(component.currentTabString).toBe('DYRK1A,FOXP1,SPAST');
    expect(window.location.pathname).toBe('/gene-profiles/DYRK1A,FOXP1,SPAST');
  });

  it('should close tab', () => {
    const backToTableSpy = jest.spyOn(component, 'backToTable');

    component.tabs = new Set(['DYRK1A,FOXP1,SPAST', 'POGZ']);
    component.closeTab('POGZ');
    expect(component.tabs).toStrictEqual(new Set(['DYRK1A,FOXP1,SPAST']));
    expect(backToTableSpy).toHaveBeenCalledWith();
  });

  it('should back to table when closing tab', () => {
    component.loadSingleView('POGZ');
    expect(component.currentTabString).toBe('POGZ');

    component.backToTable();
    expect(component.hideTable).toBe(false);
    expect(component.currentTabString).toBe('all genes');
    expect(window.location.pathname).toBe('/gene-profiles');
  });

  it('should new browser tab when middleclick', () => {
    const openTabSpy = jest.spyOn(component, 'openTab');
    const windowSpy = jest.spyOn(window, 'open');

    component.loadSingleView('PKD1', true);
    expect(component.tabs).not.toContain('PKD1');

    expect(openTabSpy).not.toHaveBeenCalledWith();

    expect(component.currentTabGeneSet).toStrictEqual(new Set(['PKD1']));
    expect(windowSpy).toHaveBeenCalledWith(`${window.location.href}/PKD1`, '_blank');
  });
});
