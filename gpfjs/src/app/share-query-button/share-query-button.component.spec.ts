import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ShareQueryButtonComponent } from './share-query-button.component';

describe('ShareQueryButtonComponent', () => {
  let component: ShareQueryButtonComponent;
  let fixture: ComponentFixture<ShareQueryButtonComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ShareQueryButtonComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ShareQueryButtonComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
