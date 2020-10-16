import { HttpClientTestingModule } from '@angular/common/http/testing';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { FamilyCountersComponent } from './family-counters.component';
import { FamilyCountersService } from './family-counters.service';

describe('FamilyCountersComponent', () => {
  let component: FamilyCountersComponent;
  let fixture: ComponentFixture<FamilyCountersComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [FamilyCountersComponent],
      providers: [FamilyCountersService, ConfigService],
      imports: [HttpClientTestingModule, RouterTestingModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FamilyCountersComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
