import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { MeasuresService } from 'app/measures/measures.service';

import { ContinuousFilterComponent } from './continuous-filter.component';

describe('ContinuousFilterComponent', () => {
  let component: ContinuousFilterComponent;
  let fixture: ComponentFixture<ContinuousFilterComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ContinuousFilterComponent],
      providers: [MeasuresService, ConfigService],
      imports: [HttpClientTestingModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContinuousFilterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
