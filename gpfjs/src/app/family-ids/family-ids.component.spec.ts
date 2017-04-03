import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { FamilyIdsComponent } from './family-ids.component';

describe('FamilyIdsComponent', () => {
  let component: FamilyIdsComponent;
  let fixture: ComponentFixture<FamilyIdsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ FamilyIdsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FamilyIdsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
