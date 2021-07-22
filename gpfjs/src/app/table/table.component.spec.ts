import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { ViewContainerRef, ChangeDetectorRef, NO_ERRORS_SCHEMA, Component } from '@angular/core';

import { GpfTableComponent, SortInfo } from './table.component';
import { GpfTableHeaderComponent } from './view/header/header.component';
import { GpfTableCellComponent } from './view/cell.component';
import { GpfTableEmptyCellComponent } from './view/empty-cell.component';
import { GpfTableSubheaderComponent } from './component/subheader.component';

@Component({
  selector: 'gpf-twc',
  template: `
    <gpf-table-subheader caption="caption" field="field">
      <span *gpfTableCellContent="let data">
      </span>
    </gpf-table-subheader>
  `,
})
class TestGpfTableSubheaderComponent { }

describe('GpfTableComponent', () => {
  let component: GpfTableComponent;
  let fixture: ComponentFixture<GpfTableComponent>;
  let testComponent: GpfTableSubheaderComponent;
  let testFixture: ComponentFixture<TestGpfTableSubheaderComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      schemas: [ NO_ERRORS_SCHEMA ],
      declarations: [
        GpfTableComponent,
        GpfTableHeaderComponent,
        GpfTableCellComponent,
        GpfTableEmptyCellComponent,
        TestGpfTableSubheaderComponent,
        GpfTableSubheaderComponent
      ],
      providers: [
        ViewContainerRef,
        ChangeDetectorRef,
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    testFixture = TestBed.createComponent(TestGpfTableSubheaderComponent);
    testComponent = testFixture.debugElement.children[0].componentInstance;
    testFixture.detectChanges();

    fixture = TestBed.createComponent(GpfTableComponent);
    component = fixture.componentInstance;

    component.dataSource = [
      {field: 3, arrayPosition: 0},
      {field: 2, arrayPosition: 0},
      {field: 4, arrayPosition: 0},
      {field: -1, arrayPosition: 0},
      {field: 5, arrayPosition: 0},
    ];

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should support window scroll', () => {
    component.onWindowScroll(null);
    expect(component.showFloatingHeader).toBe(false);
    expect(component.tableTop()).toBe(false);
  });

  it('should sort data sources', () => {
    const sortingInfo = new SortInfo(testComponent, true);
    component.sortingInfo = sortingInfo;
    expect(component.sortingInfo).toBe(sortingInfo);

    expect(component.dataSource).toEqual([
      {field: -1, arrayPosition: 3},
      {field: 2, arrayPosition: 1},
      {field: 3, arrayPosition: 0},
      {field: 4, arrayPosition: 2},
      {field: 5, arrayPosition: 4},
    ]);
  });

  it('should give scroll indices ', () => {
    expect(component.getScrollIndices()).toEqual([0, 10 + Math.ceil(window.innerHeight / 80.0)]);

    expect(component.beforeDataCellHeight).toBe(0);
    expect(component.afterDataCellHeight).toBe((-5 - Math.ceil(window.innerHeight / 80.0)) * 80);

    expect(component.visibleData).toEqual([
      {field: 3, arrayPosition: 0},
      {field: 2, arrayPosition: 0},
      {field: 4, arrayPosition: 0},
      {field: -1, arrayPosition: 0},
      {field: 5, arrayPosition: 0},
    ]);

    component.noScrollOptimization = true;

    expect(component.beforeDataCellHeight).toBe(0);
    expect(component.afterDataCellHeight).toBe(0);

    expect(component.visibleData).toEqual([
      {field: 3, arrayPosition: 0},
      {field: 2, arrayPosition: 0},
      {field: 4, arrayPosition: 0},
      {field: -1, arrayPosition: 0},
      {field: 5, arrayPosition: 0},
    ]);
    component.dataSource = null;

    expect(component.getScrollIndices()).toEqual([0, 0]);
    expect(component.visibleData).toEqual([]);
  });
});
