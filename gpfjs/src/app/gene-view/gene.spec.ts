import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule, NgModel } from '@angular/forms';

import { Exon, Transcript, Gene, GeneViewSummaryVariant, GeneViewSummaryVariantsArray, DomainRange } from './gene';

describe('Exon', () => {
  it('Should have working getters', () => {
    const exon = new Exon('testChrom', 1, 11);
    expect(exon.start).toBe(1);
    expect(exon.stop).toBe(11);
  });

  it('Should have working setters', () => {
    const exon = new Exon('testChrom', 0, 0);
    exon.start = 1;
    exon.stop = 11;
    expect(exon.start).toBe(1);
    expect(exon.stop).toBe(11);
  });

  it('Should calculate length', () => {
    const exon = new Exon('testChrom', 1, 11);
    expect(exon.length).toBe(10);
  });

  it('Should create from json', () => {
    const exon = Exon.fromJson('testChrom', {'start': 1, 'stop': 11});
    expect(exon.chrom).toBe('testChrom');
    expect(exon.start).toBe(1);
    expect(exon.stop).toBe(11);
  });

  it('Should create from json array', () => {
    const exons = Exon.fromJsonArray('testChrom', [{'start': 1, 'stop': 11}, {'start': 2, 'stop': 12}]);
    expect(exons[0].chrom).toBe('testChrom');
    expect(exons[0].start).toBe(1);
    expect(exons[0].stop).toBe(11);
    expect(exons[1].start).toBe(2);
    expect(exons[1].stop).toBe(12);
  });
});
