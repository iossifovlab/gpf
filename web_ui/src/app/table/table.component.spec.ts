import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { ViewContainerRef, ChangeDetectorRef, NO_ERRORS_SCHEMA } from '@angular/core';

import { GpfTableComponent, SortInfo } from './table.component';
import { GpfTableHeaderComponent } from './view/header/header.component';
import { GpfTableCellComponent } from './view/cell.component';
import { GpfTableEmptyCellComponent } from './view/empty-cell.component';
import { GpfTableSubheaderComponent } from './component/subheader.component';

describe('GpfTableComponent', () => {
  let component: GpfTableComponent;
  let fixture: ComponentFixture<GpfTableComponent>;
  let testComponent: GpfTableSubheaderComponent;
  let testFixture: ComponentFixture<GpfTableSubheaderComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      schemas: [NO_ERRORS_SCHEMA],
      declarations: [
        GpfTableComponent,
        GpfTableHeaderComponent,
        GpfTableCellComponent,
        GpfTableEmptyCellComponent,
        GpfTableSubheaderComponent
      ],
      providers: [
        ViewContainerRef,
        ChangeDetectorRef,
      ]
    }).compileComponents();

    testFixture = TestBed.createComponent(GpfTableSubheaderComponent);
    testComponent = testFixture.componentInstance;
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
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should support window scroll', () => {
    component.onWindowScroll();
    expect(component.showFloatingHeader).toBe(false);
    expect(component.tableTop()).toBe(false);
  });

  it('should sort data sources by array position', () => {
    const sortingInfo = new SortInfo(testComponent, true);
    component.sortingInfo = sortingInfo;
    expect(component.sortingInfo).toBe(sortingInfo);

    expect(component.dataSource).toStrictEqual([
      {field: 3, arrayPosition: 0},
      {field: 2, arrayPosition: 1},
      {field: 4, arrayPosition: 2},
      {field: -1, arrayPosition: 3},
      {field: 5, arrayPosition: 4},
    ]);
  });

  it('should give scroll indices', () => {
    expect(component.getScrollIndices()).toStrictEqual([0, 10 + Math.ceil(window.innerHeight / 80.0)]);

    expect(component.beforeDataCellHeight).toBe(0);
    expect(component.afterDataCellHeight).toBe(0);

    expect(component.getVisibleData()).toStrictEqual([
      {field: 3, arrayPosition: 0},
      {field: 2, arrayPosition: 0},
      {field: 4, arrayPosition: 0},
      {field: -1, arrayPosition: 0},
      {field: 5, arrayPosition: 0},
    ]);

    component.noScrollOptimization = true;

    expect(component.beforeDataCellHeight).toBe(0);
    expect(component.afterDataCellHeight).toBe(0);

    expect(component.getVisibleData()).toStrictEqual([
      {field: 3, arrayPosition: 0},
      {field: 2, arrayPosition: 0},
      {field: 4, arrayPosition: 0},
      {field: -1, arrayPosition: 0},
      {field: 5, arrayPosition: 0},
    ]);
    component.dataSource = null;

    expect(component.getScrollIndices()).toStrictEqual([0, 0]);
    expect(component.getVisibleData()).toStrictEqual([]);
  });
});
