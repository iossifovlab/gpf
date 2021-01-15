import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { AutismGeneProfilesComponent } from './autism-gene-profiles.component';

describe('AutismGeneProfilesComponent', () => {
  let component: AutismGeneProfilesComponent;
  let fixture: ComponentFixture<AutismGeneProfilesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ AutismGeneProfilesComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AutismGeneProfilesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
