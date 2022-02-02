import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { MultipleSelectMenuComponent } from 'app/multiple-select-menu/multiple-select-menu.component';
import { AgpTableComponent } from './autism-gene-profiles-table.component';

describe('AgpTableComponent', () => {
  let component: AgpTableComponent;
  let fixture: ComponentFixture<AgpTableComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ AgpTableComponent, MultipleSelectMenuComponent],
      providers: [ConfigService],
      imports: [HttpClientTestingModule]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(AgpTableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
