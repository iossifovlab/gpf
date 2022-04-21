import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { GenotypePreviewFieldComponent } from './genotype-preview-field.component';
import { PedigreeChartComponent } from 'app/pedigree-chart/pedigree-chart.component';
import { PedigreeChartMemberComponent } from 'app/pedigree-chart/pedigree-chart-member.component';
import { DatasetsService } from 'app/datasets/datasets.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ConfigService } from 'app/config/config.service';
import { UsersService } from 'app/users/users.service';
import { RouterTestingModule } from '@angular/router/testing';

describe('GenotypePreviewFieldComponent', () => {
  let component: GenotypePreviewFieldComponent;
  let fixture: ComponentFixture<GenotypePreviewFieldComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        GenotypePreviewFieldComponent,
        PedigreeChartComponent,
        PedigreeChartMemberComponent
      ],
      providers: [DatasetsService, ConfigService, UsersService],
      imports: [HttpClientTestingModule, RouterTestingModule]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GenotypePreviewFieldComponent);
    component = fixture.componentInstance;

    component.value = 3.14159;
    component.field = 'pi';
    component.format = '%.2f';

    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });

  it('should store format value', () => {
    component.ngOnChanges();
    expect(component.formattedValue).toBe('3.14');
  });

  it('should format value', () => {
    component.value = ['3.14159'];
    component.field = 'pi';
    component.format = '%.2f';
    expect(component.formatValue()).toEqual(['3.14']);

    component.value = 3.14159;
    component.field = 'pi';
    component.format = '%.2f';
    expect(component.formatValue()).toBe('3.14');

    component.value = '3.14159';
    component.field = 'pi';
    component.format = '%.2f';
    expect(component.formatValue()).toBe('3.14159');

    component.value = null;
    component.field = 'pi';
    component.format = '%.2f';
    expect(component.formatValue()).toBe('');

    component.value = '3.14159';
    component.field = null;
    component.format = '%.2f';
    expect(component.formatValue()).toBe('3.14159');

    component.value = '3.14159';
    component.field = 'pi';
    component.format = null;
    expect(component.formatValue()).toBe('3.14159');
  });
});
