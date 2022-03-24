import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { MultipleSelectMenuComponent } from 'app/multiple-select-menu/multiple-select-menu.component';
import { AgpTableComponent } from './autism-gene-profiles-table.component';
import { AgpTableConfig, Column } from './autism-gene-profiles-table';
import { plainToClass } from 'class-transformer';
import { AgpTableService } from './autism-gene-profiles-table.service';
import { of, Subject } from 'rxjs';
import { clone, cloneDeep } from 'lodash';
import { FormsModule } from '@angular/forms';

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
}

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
}

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

const configMock = plainToClass(AgpTableConfig, {
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

class AgpTableServiceMock {
  public getGenes(pageIndex: number, geneInput: string, sortBy: string, orderBy: string) {
    const res = cloneDeep(genesMock);
    if (geneInput) {
      res.forEach(gene => {
        gene['search'] = geneInput;
      });
    }
    return of(res);
  }
}

fdescribe('AgpTableComponent', () => {
  let component: AgpTableComponent;
  let fixture: ComponentFixture<AgpTableComponent>;
  const agpTableServiceMock = new AgpTableServiceMock();

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [ AgpTableComponent, MultipleSelectMenuComponent],
      providers: [
        ConfigService,
        { provide: AgpTableService, useValue: agpTableServiceMock }
      ],
      imports: [HttpClientTestingModule, FormsModule]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(AgpTableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize', () => {
    component.sortBy = 'mockSort';

    component.ngOnInit();

    expect(component.defaultSortBy).toEqual('mockSort');
  });

  it('should update when change happens', () => {
    component.ngOnChanges();
    expect(component.leaves).toEqual(undefined);
    expect(component.pageIndex).toBe(0);
    expect(component.genes).toEqual([]);

    component.config = cloneDeep(configMock);
    component.ngOnChanges();

    component.leaves.forEach((leaf, index) => {
      expect(leaf.id).toEqual(gridData[index].id);
      expect(leaf.gridColumn).toEqual(gridData[index].gridColumn);
      expect(leaf.gridRow).toEqual(gridData[index].gridRow);
      expect(leaf.parent?.id).toEqual(gridData[index].parent);
      expect(leaf.depth).toEqual(gridData[index].depth);
    });
    expect(component.pageIndex > 1).toBeTrue();
    expect(component.genes[0]).toEqual(genesMock[0]);
    expect(component.genes[1]).toEqual(genesMock[1]);
    expect(component.genes[2]).toEqual(genesMock[2]);
  });

  it('should search', () => {
    component.config = cloneDeep(configMock);
    component.ngOnChanges();
    component.search('mockSearch');

    expect(component.geneInput).toEqual('mockSearch');
    expect(component.genes[0]).toEqual({search: 'mockSearch', ...genesMock[0]});
    expect(component.genes[1]).toEqual({search: 'mockSearch', ...genesMock[1]});
    expect(component.genes[2]).toEqual({search: 'mockSearch', ...genesMock[2]});
  });

  it('should update genes', () => {
    expect(component.genes).toEqual([]);
    expect(component.pageIndex).toEqual(0);
    component.updateGenes();
    expect(component.genes).toEqual(genesMock);
    expect(component.pageIndex).toEqual(1);
  });

  it('should reorder header', () => {
    component.config = cloneDeep(configMock);

    component.reorderHeader(['column3', 'column1', 'column2']);
    expect(component.config.columns[0].id).toEqual('column3');
    expect(component.config.columns[1].id).toEqual('column1');
    expect(component.config.columns[2].id).toEqual('column2');

    const sortedLeaves = ['column311', 'column312', 'column321', 'column322', 'column1', 'column21', 'column22'];
    const sortedGridData = cloneDeep(gridData);
    sortedGridData.sort((a, b) => sortedLeaves.indexOf(a.id) - sortedLeaves.indexOf(b.id));
    // Update gridColumns to new order
    sortedGridData.forEach((leaf, index) => {
      leaf.gridColumn = `${index + 1}`;
    });

    component.leaves.forEach((leaf, index) => {
      expect(leaf.id).toEqual(sortedGridData[index].id);
      expect(leaf.gridColumn).toEqual(sortedGridData[index].gridColumn);
      expect(leaf.gridRow).toEqual(sortedGridData[index].gridRow);
      expect(leaf.parent?.id).toEqual(sortedGridData[index].parent);
      expect(leaf.depth).toEqual(sortedGridData[index].depth);
    });
  });

  it('should sort genes', () => {
    component.config = cloneDeep(configMock);
    component.ngOnChanges();
    component.genes = undefined;

    component.sort('mockSortBy', 'mockOrderBy');
    expect(component.sortBy).toEqual('mockSortBy');
    expect(component.orderBy).toEqual('mockOrderBy');
    expect(component.genes[0]).toEqual(genesMock[0]);
    expect(component.genes[1]).toEqual(genesMock[1]);
    expect(component.genes[2]).toEqual(genesMock[2]);
  });

  it('should toggle highlighted genes', () => {
    component.highlightedGenes = new Set(['gene1', 'gene2', 'gene3', 'gene4']);

    component.toggleHighlightGene('gene3');
    expect(component.highlightedGenes.has('gene3')).toBeFalse();
    component.toggleHighlightGene('gene3');
    expect(component.highlightedGenes.has('gene3')).toBeTrue();
    component.toggleHighlightGene('gene5');
    expect(component.highlightedGenes.has('gene5')).toBeTrue();
  });
});
