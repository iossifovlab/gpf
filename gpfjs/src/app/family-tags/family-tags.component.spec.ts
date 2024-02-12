import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FamilyTagsComponent } from './family-tags.component';

describe('FamilyTagsComponent', () => {
  let component: FamilyTagsComponent;
  let fixture: ComponentFixture<FamilyTagsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ FamilyTagsComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(FamilyTagsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
