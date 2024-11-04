import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { MultipleSelectMenuComponent } from './multiple-select-menu.component';
import { GeneProfilesColumn } from 'app/gene-profiles-table/gene-profiles-table';

describe('MultipleSelectMenuComponent', () => {
  let component: MultipleSelectMenuComponent;
  let fixture: ComponentFixture<MultipleSelectMenuComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [MultipleSelectMenuComponent],
      imports: [FormsModule]
    }).compileComponents();

    fixture = TestBed.createComponent(MultipleSelectMenuComponent);
    component = fixture.componentInstance;
    component.columns = [];
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should toggle checking all', () => {
    const applySpy = jest.spyOn(component, 'apply');

    component.buttonLabel = 'Uncheck all';
    component.columns = [
      new GeneProfilesColumn('clickable', [], 'option', false, 'id', 'meta', true, true)
    ];
    component.toggleCheckingAll();
    expect(component.buttonLabel).toBe('Check all');
    expect(component.columns[0].visibility).toBe(false);

    component.toggleCheckingAll();
    expect(component.buttonLabel).toBe('Uncheck all');
    expect(component.columns[0].visibility).toBe(true);

    expect(applySpy).toHaveBeenLastCalledWith();
  });

  it('should refresh', () => {
    const column1 = new GeneProfilesColumn('clickable', [], 'option1', false, 'id1', 'meta1', true, true);
    const column2 = new GeneProfilesColumn('clickable', [], 'option2', false, 'id2', 'meta2', true, false);

    component.searchText = 'search value';
    component.buttonLabel = 'Check all';
    component.columns = [column1, column2];
    component.filteredColumns = [column2];

    component.refresh();

    expect(component.buttonLabel).toBe('Uncheck all');
    expect(component.searchText).toBe('');
    expect(component.filteredColumns).toStrictEqual([column1, column2]);
  });

  it('should refresh when changes are detected', () => {
    const refreshSpy = jest.spyOn(component, 'refresh');
    component.ngOnChanges();
    expect(refreshSpy).toHaveBeenCalledWith();
  });

  it('should filter items by substring', () => {
    const column1 = new GeneProfilesColumn('clickable', [], 'option1', false, 'id1', 'meta1', true, true);
    const column2 = new GeneProfilesColumn('clickable', [], 'option2', false, 'id2', 'meta2', true, false);

    component.columns = [column1, column2];
    component.filterItems('on2');
    expect(component.filteredColumns).toStrictEqual([column2]);
  });
});
