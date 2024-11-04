import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { GenotypePreviewFieldComponent } from './genotype-preview-field.component';
import { PedigreeChartComponent } from 'app/pedigree-chart/pedigree-chart.component';
import { PedigreeChartMemberComponent } from 'app/pedigree-chart/pedigree-chart-member.component';
import { DatasetsService } from 'app/datasets/datasets.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ConfigService } from 'app/config/config.service';
import { UsersService } from 'app/users/users.service';
import { RouterTestingModule } from '@angular/router/testing';
import { FullEffectDetails } from './genotype-preview-field';

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
    fixture = TestBed.createComponent(GenotypePreviewFieldComponent);
    component = fixture.componentInstance;

    component.value = 3.14159;
    component.field = 'pi';
    component.format = '%.2f';

    fixture.detectChanges();
  }));

  it('should be created', () => {
    expect(component).toBeTruthy();
  });

  it('should format effect details', () => {
    const getUCSCLinkSpy = jest.spyOn(component, 'getUCSCLink').mockReturnValue('link');
    const fromGenotypeValueSpy = jest.spyOn(FullEffectDetails, 'fromGenotypeValue')
      .mockReturnValue(new FullEffectDetails('', '', [], [], true));
    component.field = 'full_effect_details';

    component.ngOnInit();

    expect(getUCSCLinkSpy).toHaveBeenCalledWith();
    expect(component.UCSCLink).toBe('link');
    expect(fromGenotypeValueSpy).toHaveBeenCalledWith(component.value);
    expect(component.fullEffectDetails).toStrictEqual(new FullEffectDetails('', '', [], [], true));
  });

  it('should store format value', () => {
    component.ngOnChanges();
    expect(component.formattedValue).toBe('3.14');
  });

  it('should format value', () => {
    component.value = ['3.14159'];
    component.field = 'pi';
    component.format = '%.2f';
    expect(component.formatValue()).toStrictEqual(['3.14']);

    component.value = ['-', 'nan'];
    component.field = 'pi';
    component.format = '%.2f';
    expect(component.formatValue()).toStrictEqual(['-', 'nan']);

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

  it('should get UCSCLink depending on the genome', () => {
    component.genome = 'hg19';
    let link = component.getUCSCLink();
    expect(link).toBe(`http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr${component.value}`);

    component.genome = 'hg38';
    link = component.getUCSCLink();
    expect(link).toBe(`http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg38&position=${component.value}`);
  });
});
