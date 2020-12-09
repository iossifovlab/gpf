import { GenotypePreview } from 'app/genotype-preview-model/genotype-preview';

import { Exon, Transcript, Gene, GeneViewSummaryVariant, GeneViewSummaryVariantsArray } from './gene';

describe('Exon', () => {
  it('should have working getters', () => {
    const exon = new Exon('testChrom', 1, 11);
    expect(exon.start).toBe(1);
    expect(exon.stop).toBe(11);
  });

  it('should have working setters', () => {
    const exon = new Exon('testChrom', 0, 0);
    exon.start = 1;
    exon.stop = 11;
    expect(exon.start).toBe(1);
    expect(exon.stop).toBe(11);
  });

  it('should calculate length', () => {
    const exon = new Exon('testChrom', 1, 11);
    expect(exon.length).toBe(10);
  });

  it('should create from json', () => {
    const exon = Exon.fromJson('testChrom', {'start': 1, 'stop': 11});
    expect(exon.chrom).toBe('testChrom');
    expect(exon.start).toBe(1);
    expect(exon.stop).toBe(11);
  });

  it('should create from json array', () => {
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

  it('should have working getters', () => {
    const testTranscript = new Transcript('testTranscriptId', 'testStrand', 'testChrom', [1, 100], [testExon1, testExon2]);
    expect(testTranscript.transcript_id).toBe('testTranscriptId');
    expect(testTranscript.strand).toBe('testStrand');
    expect(testTranscript.chrom).toBe('testChrom');
    expect(testTranscript.cds).toEqual([1, 100]);
    expect(testTranscript.exons).toEqual([testExon1, testExon2]);
    expect(testTranscript.start).toBe(1);
    expect(testTranscript.stop).toBe(23);
  });

  it('should calculate length', () => {
    const testTranscript = new Transcript('testTranscriptId', 'testStrand', 'testChrom', [1, 100], [testExon1, testExon2]);
    expect(testTranscript.length).toBe(22);
  });

  it('should calculate median exon length', () => {
    const testTranscript = new Transcript('testTranscriptId', 'testStrand', 'testChrom', [1, 100], [testExon1, testExon2]);
    expect(testTranscript.medianExonLength).toBe(11);
  });

  it('should calculate isAreaInCDS', () => {
    const exon = new Exon('1', 1, 10);
    const exon1 = new Exon('1', 15, 25);
    const transcript = new Transcript('NM_001130045_1', '+', '1', [100, 200], [exon, exon1]);

    expect(transcript.isAreaInCDS(1, 10)).toBe(false);
    expect(transcript.isAreaInCDS(120, 180)).toBe(true);
  });

  it('should create from json', () => {
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

  it('should create from json array', () => {
    const testTranscripts = Transcript.fromJsonArray([{
        'transcript_id': 'testTranscriptId1',
        'strand': 'testStrand1',
        'chrom': 'testChrom1',
        'cds': [1, 30],
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
    expect(testTranscripts[0].cds).toEqual([1, 30]);
    expect(testTranscripts[0].exons).toEqual([new Exon('testChrom1', 1, 11), new Exon('testChrom1', 12, 22)]);
    expect(testTranscripts[1].transcript_id).toBe('testTranscriptId2');
    expect(testTranscripts[1].strand).toBe('testStrand2');
    expect(testTranscripts[1].chrom).toBe('testChrom2');
    expect(testTranscripts[1].cds).toEqual([20, 50]);
    expect(testTranscripts[1].exons).toEqual([new Exon('testChrom2', 23, 33), new Exon('testChrom2', 34, 44)]);
  });
});

describe('Gene', () => {
  it('should have working getters', () => {
    const testTranscript1 = new Transcript(
      'testTranscriptId1',
      'testStrand1',
      'testChrom1',
      [1, 100],
      [new Exon('testChrom1', 1, 11), new Exon('testChrom1', 12, 22)]
    );
    const testTranscript2 = new Transcript(
      'testTranscriptId2',
      'testStrand2',
      'testChrom2',
      [1, 100],
      [new Exon('testChrom2', 23, 33), new Exon('testChrom2', 34, 44)]
    );
    const testGene = new Gene('testGene', [testTranscript1, testTranscript2]);

    expect(testGene.gene).toBe('testGene');
    expect(testGene.transcripts).toEqual([testTranscript1, testTranscript2]);
  });

  it('should create from json', () => {
    const testGene = Gene.fromJson({
      'gene': 'testGene',
      'transcripts':
        [{
          'transcript_id': 'testTranscriptId1',
          'strand': 'testStrand1',
          'chrom': 'testChrom1',
          'cds': [1, 30],
          'exons': [{'start': 1, 'stop': 11}, {'start': 12, 'stop': 22}]
        }, {
          'transcript_id': 'testTranscriptId2',
          'strand': 'testStrand2',
          'chrom': 'testChrom2',
          'cds': [20, 50],
          'exons': [{'start': 23, 'stop': 33}, {'start': 34, 'stop': 44}]
        }]
    });
    expect(testGene.gene).toBe('testGene');
    expect(testGene.transcripts[0].transcript_id).toBe('testTranscriptId1');
    expect(testGene.transcripts[0].strand).toBe('testStrand1');
    expect(testGene.transcripts[0].chrom).toBe('testChrom1');
    expect(testGene.transcripts[0].cds).toEqual([1, 30]);
    expect(testGene.transcripts[0].exons).toEqual([new Exon('testChrom1', 1, 11), new Exon('testChrom1', 12, 22)]);
    expect(testGene.transcripts[1].transcript_id).toBe('testTranscriptId2');
    expect(testGene.transcripts[1].strand).toBe('testStrand2');
    expect(testGene.transcripts[1].chrom).toBe('testChrom2');
    expect(testGene.transcripts[1].cds).toEqual([20, 50]);
    expect(testGene.transcripts[1].exons).toEqual([new Exon('testChrom2', 23, 33), new Exon('testChrom2', 34, 44)]);
  });

  it('should create from json array', () => {
    const testGenes = Gene.fromJsonArray([{
        'gene': 'testGene1',
        'transcripts': [{
            'transcript_id': 'testTranscriptId1',
            'strand': 'testStrand1',
            'chrom': 'testChrom1',
            'cds': [1, 30],
            'exons': [{'start': 1, 'stop': 11}, {'start': 12, 'stop': 22}]
          }, {
            'transcript_id': 'testTranscriptId2',
            'strand': 'testStrand2',
            'chrom': 'testChrom2',
            'cds': [20, 50],
            'exons': [{'start': 23, 'stop': 33}, {'start': 34, 'stop': 44}]
          }]
      }, {
        'gene': 'testGene2',
        'transcripts': [{
            'transcript_id': 'testTranscriptId3',
            'strand': 'testStrand3',
            'chrom': 'testChrom3',
            'cds': [40, 70],
            'exons': [{'start': 45, 'stop': 55}, {'start': 56, 'stop': 66}]
          }, {
            'transcript_id': 'testTranscriptId4',
            'strand': 'testStrand4',
            'chrom': 'testChrom4',
            'cds': [60, 90],
            'exons': [{'start': 67, 'stop': 77}, {'start': 78, 'stop': 88}]
          }]
      }
    ]);

    expect(testGenes[0].gene).toBe('testGene1');
    expect(testGenes[0].transcripts[0].transcript_id).toBe('testTranscriptId1');
    expect(testGenes[0].transcripts[0].strand).toBe('testStrand1');
    expect(testGenes[0].transcripts[0].chrom).toBe('testChrom1');
    expect(testGenes[0].transcripts[0].cds).toEqual([1, 30]);
    expect(testGenes[0].transcripts[0].exons).toEqual([new Exon('testChrom1', 1, 11), new Exon('testChrom1', 12, 22)]);
    expect(testGenes[0].transcripts[1].transcript_id).toBe('testTranscriptId2');
    expect(testGenes[0].transcripts[1].strand).toBe('testStrand2');
    expect(testGenes[0].transcripts[1].chrom).toBe('testChrom2');
    expect(testGenes[0].transcripts[1].cds).toEqual([20, 50]);
    expect(testGenes[0].transcripts[1].exons).toEqual([new Exon('testChrom2', 23, 33), new Exon('testChrom2', 34, 44)]);
    expect(testGenes[1].gene).toBe('testGene2');
    expect(testGenes[1].transcripts[0].transcript_id).toBe('testTranscriptId3');
    expect(testGenes[1].transcripts[0].strand).toBe('testStrand3');
    expect(testGenes[1].transcripts[0].chrom).toBe('testChrom3');
    expect(testGenes[1].transcripts[0].cds).toEqual([40, 70]);
    expect(testGenes[1].transcripts[0].exons).toEqual([new Exon('testChrom3', 45, 55), new Exon('testChrom3', 56, 66)]);
    expect(testGenes[1].transcripts[1].transcript_id).toBe('testTranscriptId4');
    expect(testGenes[1].transcripts[1].strand).toBe('testStrand4');
    expect(testGenes[1].transcripts[1].chrom).toBe('testChrom4');
    expect(testGenes[1].transcripts[1].cds).toEqual([60, 90]);
    expect(testGenes[1].transcripts[1].exons).toEqual([new Exon('testChrom4', 67, 77), new Exon('testChrom4', 78, 88)]);
  });

  it('should create collapsed transcript', () => {
    const testGene = Gene.fromJson({
      'gene': 'testGene',
      'transcripts':
        [{
          'transcript_id': 'testTranscriptId1',
          'strand': 'testStrand1',
          'chrom': 'testChrom1',
          'cds': [1, 30],
          'exons': [{'start': 1, 'stop': 11}, {'start': 12, 'stop': 22}]
        }, {
          'transcript_id': 'testTranscriptId2',
          'strand': 'testStrand2',
          'chrom': 'testChrom2',
          'cds': [20, 50],
          'exons': [{'start': 23, 'stop': 33}, {'start': 34, 'stop': 44}]
        }]
    });

    const expectedTranscript = new Transcript(
      'collapsed',
      'testStrand1',
      'testChrom1',
      [1, 44],
      [
        new Exon('testChrom1', 1, 11),
        new Exon('testChrom1', 12, 22),
        new Exon('testChrom2', 23, 33),
        new Exon('testChrom2', 34, 44),
      ]
    );
    expect(testGene.collapsedTranscript()).toEqual(expectedTranscript);
  });
});

describe('GeneViewSummaryVariant', () => {
  // it('should create from preview variant', () => {
  //   const mockRow = {
  //     location: '1:999',
  //     position: 999,
  //     chrom: '1',
  //     variant: 'testVariant',
  //     effect: 'test effect',
  //     frequency: 2,
  //     family_variants_count: 1,
  //     is_denovo: true,
  //     seen_in_affected: true,
  //     seen_in_unaffected: false,
  //     end_position: 1000
  //   };
  //   const expectedResult = GeneViewSummaryVariant.fromRow(mockRow);

  //   const mockConfig = {
  //     locationColumn: 'location',
  //     frequencyColumn: 'frequency',
  //     effectColumn: 'effect'
  //   };
  //   const testGenotypePreview = new GenotypePreview();
  //   testGenotypePreview.data = new Map<string, any>([
  //     ['location', '1:999'],
  //     ['frequency', 2],
  //     ['effect', 'TEST EFFECT'],
  //     ['variant.variant', 'testVariant'],
  //     ['variant.is denovo', true],
  //     ['genotype', [{label: 1, color: '#color'}]]
  //   ]);

  //   expect(GeneViewSummaryVariant.fromPreviewVariant(mockConfig, testGenotypePreview)).toEqual(expectedResult);
  // });

  it('should check if its LGDs', () => {
    const testSummaryVariant = new GeneViewSummaryVariant();
    testSummaryVariant.effect = 'lgds';
    expect(testSummaryVariant.isLGDs()).toBeTruthy();
  });

  it('should check if its Missense', () => {
    const testSummaryVariant = new GeneViewSummaryVariant();
    testSummaryVariant.effect = 'missense';
    expect(testSummaryVariant.isMissense()).toBeTruthy();
  });

  it('should check if its Synonymous', () => {
    const testSummaryVariant = new GeneViewSummaryVariant();
    testSummaryVariant.effect = 'synonymous';
    expect(testSummaryVariant.isSynonymous()).toBeTruthy();
  });

  it('should create correct comparison value', () => {
    const correctOrder = [
      [false, 'synonymous', true, true],
      [false, 'synonymous', false, true],
      [false, 'synonymous', true, false],
      [false, 'missense', true, true],
      [false, 'missense', false, true],
      [false, 'missense', true, false],
      [false, 'lgds', true, true],
      [false, 'lgds', false, true],
      [false, 'lgds', true, false],
      [true, 'synonymous', true, true],
      [true, 'synonymous', false, true],
      [true, 'synonymous', true, false],
      [true, 'missense', true, true],
      [true, 'missense', false, true],
      [true, 'missense', true, false],
      [true, 'lgds', true, true],
      [true, 'lgds', false, true],
      [true, 'lgds', true, false],
    ];

    const length = 18;
    const testSummaryVariants = Array<GeneViewSummaryVariant>();
    for (let i = 0; i < length; i++) {
      testSummaryVariants[i] = new GeneViewSummaryVariant();
      testSummaryVariants[i].seenAsDenovo = correctOrder[i][0] as boolean;
      testSummaryVariants[i].effect = correctOrder[i][1] as string;
      testSummaryVariants[i].seenInAffected = correctOrder[i][2] as boolean;
      testSummaryVariants[i].seenInUnaffected = correctOrder[i][3] as boolean;
    }

    for (let i = 0; i < length - 1; i++) {
      expect(
        testSummaryVariants[i].comparisonValue < testSummaryVariants[i + 1].comparisonValue
      ).toBeTruthy();
    }
  });
});

describe('GeneViewSummaryVariantsArray', () => {
  const mockRow = {
    location: '1:999',
    position: 999,
    chrom: '1',
    variant: 'testVariant',
    effect: 'test effect',
    frequency: 2,
    family_variants_count: 1,
    is_denovo: true,
    seen_in_affected: true,
    seen_in_unaffected: false
  };

  it('should add summary row', () => {
    const summaryVariantsArray = new GeneViewSummaryVariantsArray();
    summaryVariantsArray.addSummaryRow(mockRow);

    const expectedSummaryVariant = GeneViewSummaryVariant.fromRow(mockRow);

    expect(summaryVariantsArray.summaryVariants[0]).toEqual(expectedSummaryVariant);
  });

  it('should push summary variant', () => {
    const expectedSummaryVariant = GeneViewSummaryVariant.fromRow(mockRow);
    const summaryVariantsArray = new GeneViewSummaryVariantsArray();
    summaryVariantsArray.push(expectedSummaryVariant);

    expect(summaryVariantsArray.summaryVariants[0]).toEqual(expectedSummaryVariant);
  });
});
