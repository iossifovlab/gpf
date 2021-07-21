import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';

import { FamilyFiltersBlockComponent } from './family-filters-block.component';

xdescribe('FamilyFiltersBlockComponent', () => {
  let component: FamilyFiltersBlockComponent;
  let fixture: ComponentFixture<FamilyFiltersBlockComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [FamilyFiltersBlockComponent],
      imports: [NgbNavModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FamilyFiltersBlockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
