import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { Component, NO_ERRORS_SCHEMA, ViewContainerRef } from '@angular/core';

import { GpfTableHeaderCellComponent } from './header-cell.component';
import { GpfTableContentComponent } from 'app/table/component/content.component';
import { GpfTableContentHeaderComponent } from 'app/table/component/header.component';
import { GenotypePreviewFieldComponent } from 'app/genotype-preview-field/genotype-preview-field.component';
import { GpfTableSubheaderComponent } from 'app/table/component/subheader.component';
import { GpfTableCellContentDirective } from 'app/table/component/content.directive';
import { SortInfo } from 'app/table/table.component';

@Component({
    selector: 'gpf-tgtchc',
    template: `
      <gpf-table-header>
        <gpf-table-subheader caption="caption" field="fieldH">
          <span *gpfTableCellContent="let data">
          </span>
        </gpf-table-subheader>
      </gpf-table-header>
    `,
  })
  class TestGpfTableContentHeaderComponent { }

describe('GpfTableHeaderCellComponent', () => {
  let component: GpfTableHeaderCellComponent;
  let fixture: ComponentFixture<GpfTableHeaderCellComponent>;
  let testComponent: GpfTableContentHeaderComponent;
  let testFixture: ComponentFixture<TestGpfTableContentHeaderComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      schemas: [ NO_ERRORS_SCHEMA ],
      declarations: [
        GpfTableHeaderCellComponent,
        TestGpfTableContentHeaderComponent,
        GpfTableContentHeaderComponent,
        GenotypePreviewFieldComponent,
        GpfTableContentComponent,
        GpfTableSubheaderComponent,
        GpfTableCellContentDirective
      ],
      providers: [ ViewContainerRef ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    testFixture = TestBed.createComponent(TestGpfTableContentHeaderComponent);
    testComponent = testFixture.debugElement.children[0].componentInstance;
    testFixture.detectChanges();

    fixture = TestBed.createComponent(GpfTableHeaderCellComponent);
    component = fixture.componentInstance;

    component.columnInfo = testComponent;

    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });

  it('should give image path prefix', () => {
    expect(component.imgPathPrefix).toBe('assets/');
  });

  it('should sort on click', () => {
    spyOn(component.sortingInfoChange, 'emit');

    expect(testComponent.subcolumnsChildren.length).toBe(1);
    expect(component.onSortClick(testComponent.subcolumnsChildren.first)).toBe(true);

    expect(component.sortingInfoChange.emit).toHaveBeenCalledWith(
      new SortInfo(testComponent.subcolumnsChildren.first, false)
    );
  });
});
