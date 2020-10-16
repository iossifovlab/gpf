/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { PedigreeSelectorComponent } from './pedigree-selector.component';
import { StateRestoreService } from 'app/store/state-restore.service';


describe('PedigreeselectorComponent', () => {
  let component: PedigreeSelectorComponent;
  let fixture: ComponentFixture<PedigreeSelectorComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [PedigreeSelectorComponent],
      imports: [],
      providers: [StateRestoreService]

    })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PedigreeSelectorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
