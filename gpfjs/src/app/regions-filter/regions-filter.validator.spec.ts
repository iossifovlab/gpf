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

  it('should check general regions filter input', () => {
    expect(component.validate('')).toBeNull();
    expect(component.validate('   ')).toBe(false);
    expect(component.validate('false')).toBe(false);
  });

  it('should check if regions filter input is valid for hg19', () => {
    DatasetsService.currentGenome = 'hg19';
    expect(DatasetsService.currentGenome).toBe('hg19');

    expect(component.validate('0')).toBe(true);
    expect(component.validate('14')).toBe(true);
    expect(component.validate('X')).toBe(true);
    expect(component.validate('Y')).toBe(true);
    expect(component.validate('  X:76710815 ')).toBe(true);
    expect(component.validate('  Y:76710815 ')).toBe(true);
    expect(component.validate('  9:76710815 ')).toBe(true);
    expect(component.validate('  9:76710815-76710830 ')).toBe(true);
    expect(component.validate('  9:76710815-76710830 \n11:10169163-10169314  \n\n\n12:50344524-50352664')).toBe(true);
    expect(component.validate('  9:76710815-76710830, X:10169163-10169314, Y:50344524-50352664')).toBe(true);
    expect(component.validate('  9:76710815-76710830, 11:10169163-10169314, 12:50344524-50352664')).toBe(true);
    expect(component.validate('  9:76710833-76710830 ')).toBe(false);
    expect(component.validate('  9:76710833-76710830:420-345 ')).toBe(false);
    expect(component.validate('23')).toBe(false);
    expect(component.validate('9:')).toBe(false);
    expect(component.validate('X12')).toBe(false);
    expect(component.validate('Y1')).toBe(false);
    expect(component.validate('chr9:76710815-76710830 ')).toBe(false);
  });

  it('should check if regions filter input is valid for hg38', () => {
    DatasetsService.currentGenome = 'hg38';
    expect(DatasetsService.currentGenome).toBe('hg38');

    expect(component.validate('chr0')).toBe(true);
    expect(component.validate('chr17')).toBe(true);
    expect(component.validate('chrX')).toBe(true);
    expect(component.validate('chrY')).toBe(true);
    expect(component.validate('  chrX:76710815 ')).toBe(true);
    expect(component.validate('  chrY:76710815 ')).toBe(true);
    expect(component.validate('  chr9:76710815 ')).toBe(true);
    expect(component.validate('  chr9:76710815-76710830 ')).toBe(true);
    expect(component.validate('chr9')).toBe(true);
    expect(component.validate('  chr9:76710815-76710830 \nchr11:10169163-10169314  ' +
        '\nchr12:50344524-50352664')).toBe(true);
    expect(component.validate('  chr9:76710815-76710830 , chrX:10169163-10169314,  ' +
        'chrY:50344524-50352664')).toBe(true);
    expect(component.validate('  chr9:76710815-76710830 \n11:10169163-10169314  ' +
        '\nchr12:50344524-50352664')).toBe(false);
    expect(component.validate('  chr9:76710844-76710830 ')).toBe(false);
    expect(component.validate('chr23')).toBe(false);
    expect(component.validate('chr9:')).toBe(false);
    expect(component.validate('chrX12')).toBe(false);
    expect(component.validate('chrY1')).toBe(false);
    expect(component.validate('9:76710815-76710830 ')).toBe(false);
  });
});

