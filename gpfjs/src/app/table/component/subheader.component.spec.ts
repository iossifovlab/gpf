import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { Component, NO_ERRORS_SCHEMA } from '@angular/core';
import { GpfTableSubheaderComponent } from './subheader.component';
import { GpfTableCellContentDirective } from './content.directive';

@Component({
  selector: 'gpf-twc',
  template: `
    <gpf-table-subheader caption="caption" field="field">
      <span *gpfTableCellContent="let data">
      </span>
    </gpf-table-subheader>
  `,
})
class TestWrapperComponent { }

describe('GpfTableSubheaderComponent', () => {
  let component: GpfTableSubheaderComponent;
  let fixture: ComponentFixture<TestWrapperComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      schemas: [NO_ERRORS_SCHEMA],
      declarations: [
        TestWrapperComponent,
        GpfTableSubheaderComponent,
        GpfTableCellContentDirective
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(TestWrapperComponent);
    component = fixture.debugElement.children[0].componentInstance;
    fixture.detectChanges();
  }));

  it('should be created', () => {
    expect(component).toBeTruthy();
  });

  it('should have content children', () => {
    expect(component.contentChildren).toHaveLength(1);

    expect(component.contentTemplateRef).toBe(component.contentChildren.first.templateRef);
  });

  it('should be sortable', () => {
    expect(component.sortable).toBe('field');
  });

  it('should have default comparator and sort data', () => {
    expect(component.defaultComparator).toBe(component.comparator);
    expect(component.defaultComparator({field: 1}, {field: 5})).toBe(-4);
    expect(component.defaultComparator({}, {})).toBe(0);
    expect(component.defaultComparator({}, {field: 5})).toBe(-1);
    expect(component.defaultComparator({field: 1}, {})).toBe(1);

    const data = [
      {field: 3, arrayPosition: 0},
      {field: 2, arrayPosition: 0},
      {field: 4, arrayPosition: 0},
      {field: -1, arrayPosition: 0},
      {field: 5, arrayPosition: 0},
      {field: 5, arrayPosition: 0}];

    component.sort(data, true);
    expect(data).toStrictEqual([
      {field: -1, arrayPosition: 3},
      {field: 2, arrayPosition: 1},
      {field: 3, arrayPosition: 0},
      {field: 4, arrayPosition: 2},
      {field: 5, arrayPosition: 4},
      {field: 5, arrayPosition: 5},
    ]);

    component.sort(data, false);
    expect(data).toStrictEqual([
      {field: 5, arrayPosition: 4},
      {field: 5, arrayPosition: 5},
      {field: 4, arrayPosition: 3},
      {field: 3, arrayPosition: 2},
      {field: 2, arrayPosition: 1},
      {field: -1, arrayPosition: 0}
    ]);
  });
});
