import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';

import { FamilyFiltersBlockComponent } from './family-filters-block.component';

describe.skip('FamilyFiltersBlockComponent', () => {
  let component: FamilyFiltersBlockComponent;
  let fixture: ComponentFixture<FamilyFiltersBlockComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [FamilyFiltersBlockComponent],
      imports: [NgbNavModule]
    }).compileComponents();

    fixture = TestBed.createComponent(FamilyFiltersBlockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
