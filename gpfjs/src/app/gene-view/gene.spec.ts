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
    const exons = Exon.fromJsonArray('testChrom', [{'start': 1, 'stop': 11}, {'start': 12, 'stop': 22}]);
    expect(exons[0].chrom).toBe('testChrom');
    expect(exons[0].start).toBe(1);
    expect(exons[0].stop).toBe(11);
    expect(exons[1].chrom).toBe('testChrom');
    expect(exons[1].start).toBe(12);
    expect(exons[1].stop).toBe(22);
  });
});

describe('Transcript', () => {
  const testExon1 = new Exon('testChrom1', 1, 11);
  const testExon2 = new Exon('testChrom2', 12, 23);

  it('Should have working getters', () => {
    const testTranscript = new Transcript('testTranscriptId', 'testStrand', 'testChrom', [1, 100], [testExon1, testExon2]);
    expect(testTranscript.transcript_id).toBe('testTranscriptId');
    expect(testTranscript.strand).toBe('testStrand');
    expect(testTranscript.chrom).toBe('testChrom');
    expect(testTranscript.cds).toEqual([1, 100]);
    expect(testTranscript.exons).toEqual([testExon1, testExon2]);
    expect(testTranscript.start).toBe(1);
    expect(testTranscript.stop).toBe(23);
  });

  it('Should calculate length', () => {
    const testTranscript = new Transcript('testTranscriptId', 'testStrand', 'testChrom', [1, 100], [testExon1, testExon2]);
    expect(testTranscript.length).toBe(22);
  });

  it('Should calculate median exon length', () => {
    const testTranscript = new Transcript('testTranscriptId', 'testStrand', 'testChrom', [1, 100], [testExon1, testExon2]);
    expect(testTranscript.medianExonLength).toBe(11);
  });

  it('Should create from json', () => {
    const testTranscript = Transcript.fromJson({
      'transcript_id': 'testTranscriptId',
      'strand': 'testStrand',
      'chrom': 'testChrom',
      'cds': [1, 100],
      'exons': [{'start': 1, 'stop': 11}, {'start': 12, 'stop': 23}]
    });
    expect(testTranscript.transcript_id).toBe('testTranscriptId');
    expect(testTranscript.strand).toBe('testStrand');
    expect(testTranscript.chrom).toBe('testChrom');
    expect(testTranscript.cds).toEqual([1, 100]);
    expect(testTranscript.exons).toEqual([new Exon('testChrom', 1, 11), new Exon('testChrom', 12, 23)]);
    expect(testTranscript.start).toBe(1);
    expect(testTranscript.stop).toBe(23);
  });

  it('Should create from json array', () => {
    const testTranscripts = Transcript.fromJsonArray([{
        'transcript_id': 'testTranscriptId1',
        'strand': 'testStrand1',
        'chrom': 'testChrom1',
        'cds': [1, 100],
        'exons': [{'start': 1, 'stop': 11}, {'start': 12, 'stop': 22}]
      }, {
        'transcript_id': 'testTranscriptId2',
        'strand': 'testStrand2',
        'chrom': 'testChrom2',
        'cds': [20, 50],
        'exons': [{'start': 23, 'stop': 33}, {'start': 34, 'stop': 44}]
      }
    ]);
    expect(testTranscripts[0].transcript_id).toBe('testTranscriptId1');
    expect(testTranscripts[0].strand).toBe('testStrand1');
    expect(testTranscripts[0].chrom).toBe('testChrom1');
    expect(testTranscripts[0].cds).toEqual([1, 100]);
    expect(testTranscripts[0].exons).toEqual([new Exon('testChrom1', 1, 11), new Exon('testChrom1', 12, 22)]);
    expect(testTranscripts[1].transcript_id).toBe('testTranscriptId2');
    expect(testTranscripts[1].strand).toBe('testStrand2');
    expect(testTranscripts[1].chrom).toBe('testChrom2');
    expect(testTranscripts[1].cds).toEqual([20, 50]);
    expect(testTranscripts[1].exons).toEqual([new Exon('testChrom2', 23, 33), new Exon('testChrom2', 34, 44)]);
  });
});
