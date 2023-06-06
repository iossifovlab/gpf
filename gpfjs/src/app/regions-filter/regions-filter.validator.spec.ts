import { waitForAsync } from '@angular/core/testing';
import { RegionsFilterValidator } from './regions-filter.validator';
import { DatasetsService } from 'app/datasets/datasets.service';

describe('RegionsFilterValidator', () => {
  let component: RegionsFilterValidator;

  beforeEach(waitForAsync(() => {
    component = new RegionsFilterValidator();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should check for invalid regions filter input', () => {
    expect(component.validate('')).toBeNull();
    expect(component.validate('false')).toBe(false);
    expect(component.validate('76710815')).toBe(false);
  });

  it('should check if regions filter input is valid for hg19', () => {
    DatasetsService.currentGenome = 'hg19';
    expect(DatasetsService.currentGenome).toBe('hg19');

    expect(component.validate('  9:76710815 ')).toBe(true);
    expect(component.validate('  9:76710815-76710830 ')).toBe(true);
    expect(component.validate('  9:76710815-76710830 \n11:10169163-10169314  \n\n\n12:50344524-50352664')).toBe(true);
    expect(component.validate('  9:76710815-76710830, 11:10169163-10169314, 12:50344524-50352664')).toBe(true);
    expect(component.validate('  99999999999999:76710815-76710830 ')).toBe(false);
    expect(component.validate('chr9:76710815-76710830 ')).toBe(false);
  });

  it('should check if regions filter input is valid for hg38', () => {
    DatasetsService.currentGenome = 'hg38';
    expect(DatasetsService.currentGenome).toBe('hg38');

    expect(component.validate('  chr9:76710815 ')).toBe(true);
    expect(component.validate('  chr9:76710815-76710830 ')).toBe(true);
    expect(component.validate('  chr9:76710815-76710830 \nchr11:10169163-10169314  ' +
        '\nchr12:50344524-50352664')).toBe(true);
    expect(component.validate('  chr9:76710815-76710830 \n11:10169163-10169314  ' +
        '\nchr12:50344524-50352664')).toBe(false);
    expect(component.validate('  chr99999999999999:76710815-76710830 ')).toBe(false);
    expect(component.validate('chr9')).toBe(false);
    expect(component.validate('9:76710815-76710830 ')).toBe(false);
  });
});

