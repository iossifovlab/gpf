/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

import { GenesBlockComponent } from './genes-block.component';
import { StateRestoreService } from 'app/store/state-restore.service';

describe('GenesBlockComponent', () => {
  let component: GenesBlockComponent;
  let fixture: ComponentFixture<GenesBlockComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [GenesBlockComponent],
      providers: [StateRestoreService],
      imports: [NgbModule],
    })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GenesBlockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
