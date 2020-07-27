import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SavedQueriesTableComponent } from './saved-queries-table.component';

describe('SavedQueriesTableComponent', () => {
  let component: SavedQueriesTableComponent;
  let fixture: ComponentFixture<SavedQueriesTableComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SavedQueriesTableComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SavedQueriesTableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
