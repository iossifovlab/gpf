import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FamilyTagsComponent } from './family-tags.component';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { familyTagsReducer } from './family-tags.state';
import { errorsReducer } from 'app/common/errors.state';
import { StoreModule } from '@ngrx/store';

describe('FamilyTagsComponent', () => {
  let component: FamilyTagsComponent;
  let fixture: ComponentFixture<FamilyTagsComponent>;

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [FamilyTagsComponent],
      imports: [
        StoreModule.forRoot({errors: errorsReducer, familyTags: familyTagsReducer}),
        NgbNavModule
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(FamilyTagsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should test restoring family tags', () => {
    component.restoreFamilyTags(['tag1'], ['tag2'], false);
    expect(component.selectedTags).toStrictEqual(['tag1']);
    expect(component.deselectedTags).toStrictEqual(['tag2']);
    expect(component.tagIntersection).toBe(false);
    expect(component.filtersButtonsState['tag1']).toBe(1);
    expect(component.filtersButtonsState['tag2']).toBe(-1);
  });

  it('should test choosing mode and passing the updated mode', () => {
    jest.spyOn(component.chooseMode, 'emit');

    component.onChooseMode();
    expect(component.tagIntersection).toBe(true);
    expect(component.chooseMode.emit).toHaveBeenCalledWith(true);

    component.onChooseMode(false);
    expect(component.tagIntersection).toBe(false);
    expect(component.chooseMode.emit).toHaveBeenCalledWith(false);
  });

  it('should test passing updated tag lists', () => {
    jest.spyOn(component.updateTagsLists, 'next');

    component.selectedTags = ['tag1'];
    component.deselectedTags = ['tag2'];
    component.onUpdateTags();
    expect(component.updateTagsLists.next).toHaveBeenCalledWith(
      {
        selected: ['tag1'],
        deselected: ['tag2']
      }
    );
  });

  it('should test tags state when selecting', () => {
    const updateSelectedTagsListMock = jest.spyOn(component, 'updateSelectedTagsList')
      .mockImplementation(() => null);

    component.filtersButtonsState['tag1'] = 0;
    component.selectFilter('tag1');
    expect(component.filtersButtonsState['tag1']).toBe(1);
    expect(updateSelectedTagsListMock).toHaveBeenCalledWith('tag1');

    component.selectFilter('tag1');
    expect(component.filtersButtonsState['tag1']).toBe(0);
  });

  it('should test tags state when deselecting', () => {
    const updateDeselectedTagsListMock = jest.spyOn(component, 'updateDeselectedTagsList')
      .mockImplementation(() => null);

    component.filtersButtonsState['tag1'] = 0;
    component.deselectFilter('tag1');
    expect(component.filtersButtonsState['tag1']).toBe(-1);
    expect(updateDeselectedTagsListMock).toHaveBeenCalledWith('tag1');

    component.deselectFilter('tag1');
    expect(component.filtersButtonsState['tag1']).toBe(0);
  });
  it('should test clearing tags', () => {
    const updateTagsListMock = jest.spyOn(component, 'onUpdateTags')
      .mockImplementation(() => null);

    component.tags = ['tag1', 'tag2'];
    component.selectedTags = ['tag1'];
    component.deselectedTags = ['tag2'];
    component.filtersButtonsState['tag1'] = 1;
    component.filtersButtonsState['tag2'] = -1;

    component.clearFilters();
    expect(component.selectedTags).toStrictEqual([]);
    expect(component.deselectedTags).toStrictEqual([]);
    expect(component.filtersButtonsState['tag1']).toBe(0);
    expect(component.filtersButtonsState['tag2']).toBe(0);
    expect(updateTagsListMock).toHaveBeenCalledWith();
  });

  it('should test updating selected tag list', () => {
    const updateTagsListMock = jest.spyOn(component, 'onUpdateTags')
      .mockImplementation(() => null);

    component.selectedTags = ['tag1'];
    component.updateSelectedTagsList('tag2');
    expect(component.selectedTags).toStrictEqual(['tag1', 'tag2']);
    expect(updateTagsListMock).toHaveBeenCalledWith();

    component.selectedTags = ['tag1', 'tag2'];
    component.updateSelectedTagsList('tag1');
    expect(component.selectedTags).toStrictEqual(['tag2']);

    component.deselectedTags = ['tag2'];
    component.selectedTags = [];
    component.updateSelectedTagsList('tag2');
    expect(component.selectedTags).toStrictEqual(['tag2']);
    expect(component.deselectedTags).toStrictEqual([]);
  });

  it('should test updating deselected tag list', () => {
    const updateTagsListMock = jest.spyOn(component, 'onUpdateTags')
      .mockImplementation(() => null);

    component.deselectedTags = ['tag1'];
    component.updateDeselectedTagsList('tag2');
    expect(component.deselectedTags).toStrictEqual(['tag1', 'tag2']);
    expect(updateTagsListMock).toHaveBeenCalledWith();

    component.deselectedTags = ['tag1', 'tag2'];
    component.updateDeselectedTagsList('tag1');
    expect(component.deselectedTags).toStrictEqual(['tag2']);

    component.selectedTags = ['tag2'];
    component.deselectedTags = [];
    component.updateDeselectedTagsList('tag2');
    expect(component.deselectedTags).toStrictEqual(['tag2']);
    expect(component.selectedTags).toStrictEqual([]);
  });
});
