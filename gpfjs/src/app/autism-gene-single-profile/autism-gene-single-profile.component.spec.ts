import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { AutismGeneSingleProfileComponent } from './autism-gene-single-profile.component';

describe('AutismGeneSingleProfileComponent', () => {
  let component: AutismGeneSingleProfileComponent;
  let fixture: ComponentFixture<AutismGeneSingleProfileComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ AutismGeneSingleProfileComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AutismGeneSingleProfileComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
