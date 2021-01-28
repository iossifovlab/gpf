import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MultipleSelectMenuComponent } from './multiple-select-menu.component';

describe('MultipleSelectMenuComponent', () => {
  let component: MultipleSelectMenuComponent;
  let fixture: ComponentFixture<MultipleSelectMenuComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MultipleSelectMenuComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MultipleSelectMenuComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
