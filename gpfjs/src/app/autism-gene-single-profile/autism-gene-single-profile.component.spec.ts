import { HttpClientTestingModule } from '@angular/common/http/testing';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { GeneWeightsService } from 'app/gene-weights/gene-weights.service';

import { AutismGeneSingleProfileComponent } from './autism-gene-single-profile.component';

describe('AutismGeneSingleProfileComponent', () => {
  let component: AutismGeneSingleProfileComponent;
  let fixture: ComponentFixture<AutismGeneSingleProfileComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ AutismGeneSingleProfileComponent ],
      providers: [ConfigService, GeneWeightsService],
      imports: [HttpClientTestingModule]
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
