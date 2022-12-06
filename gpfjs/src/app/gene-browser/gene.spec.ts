import { IS_RFC_3339 } from 'class-validator';
import { Transcript, Gene, TranscriptSegment } from './gene';

describe('TranscriptSegment', () => {
  it('should check is intron', () => {
    let transcriptSegment: TranscriptSegment = new TranscriptSegment('chrom', 1, 10, true, true, true, 'label');
    expect(transcriptSegment.isIntron).toBeFalsy();
    transcriptSegment = new TranscriptSegment('chrom', 1, 10, true, false, true, 'label');
    expect(transcriptSegment.isIntron).toBeTruthy();
  });

  it('should get intersection length', () => {
    const transcriptSegment = new TranscriptSegment('chrom', 10, 20, true, true, true, 'label');

    expect(transcriptSegment.intersectionLength(5, 10)).toBe(0);
    expect(transcriptSegment.intersectionLength(20, 25)).toBe(0);
    expect(transcriptSegment.intersectionLength(5, 15)).toBe(5);
    expect(transcriptSegment.intersectionLength(10, 15)).toBe(5);
    expect(transcriptSegment.intersectionLength(10, 20)).toBe(10);
    expect(transcriptSegment.intersectionLength(5, 25)).toBe(10);
    expect(transcriptSegment.intersectionLength(18, 25)).toBe(2);
    expect(transcriptSegment.intersectionLength(5, 13)).toBe(3);
  });

  it('should check is sub segment', () => {
    const transcriptSegment = new TranscriptSegment('chrom', 10, 20, true, true, true, 'label');

    expect(transcriptSegment.isSubSegment(5, 10)).toBeFalsy();
    expect(transcriptSegment.isSubSegment(5, 15)).toBeFalsy();
    expect(transcriptSegment.isSubSegment(20, 25)).toBeFalsy();
    expect(transcriptSegment.isSubSegment(15, 25)).toBeFalsy();
    expect(transcriptSegment.isSubSegment(12, 18)).toBeFalsy();

    expect(transcriptSegment.isSubSegment(5, 20)).toBeTruthy();
    expect(transcriptSegment.isSubSegment(10, 25)).toBeTruthy();
    expect(transcriptSegment.isSubSegment(10, 20)).toBeTruthy();
  });
});

describe('Transcript', () => {
  it('should construct', () => {
    const transcript = new Transcript(
      'id',
      'chrom',
      'strand',
      [{ chromosome: 'coding1', start: 1, stop: 5 }],
      [{ chromosome: 'exon1', start: 1, stop: 5 },
        { chromosome: 'exon2', start: 7, stop: 12 },
        { chromosome: 'exon3', start: 15, stop: 16 },
        { chromosome: 'exon4', start: 18, stop: 20 }]
    );
    expect(transcript.start).toEqual(1);
    expect(transcript.stop).toEqual(20);
    expect(transcript.length).toEqual(19);
    expect(transcript.medianExonLength).toEqual(1);
    expect(transcript.transcriptId).toEqual('id');
    expect(transcript.chromosome).toEqual('chrom');
    expect(transcript.strand).toEqual('strand');
    expect(transcript.codingSequences).toEqual([{ chromosome: 'coding1', start: 1, stop: 5 }]);
    expect(transcript.exons).toEqual([
      { chromosome: 'exon1', start: 1, stop: 5 },
      { chromosome: 'exon2', start: 7, stop: 12 },
      { chromosome: 'exon3', start: 15, stop: 16 },
      { chromosome: 'exon4', start: 18, stop: 20 },
    ]);

    const expectedSegments = [
      {
        chromosome: 'exon1',
        start: 1,
        stop: 1,
        isExon: true,
        isCDS: true,
        isSpacer: false,
        label: 'exon 1/4',
        length: 0
      } as TranscriptSegment,
      {
        chromosome: 'exon1',
        start: 1,
        stop: 5,
        isExon: true,
        isCDS: true,
        isSpacer: false,
        label: 'exon 1/4',
        length: 4
      } as TranscriptSegment,
      {
        chromosome: 'exon1',
        start: 5,
        stop: 5,
        isExon: true,
        isCDS: true,
        isSpacer: false,
        label: 'exon 1/4',
        length: 0
      } as TranscriptSegment,
      {
        chromosome: 'exon1',
        start: 5,
        stop: 7,
        isExon: false,
        isCDS: false,
        isSpacer: true,
        label: 'intron 1/3',
        length: 4
      } as TranscriptSegment,
      {
        chromosome: 'exon2',
        start: 7,
        stop: 12,
        isExon: true,
        isCDS: false,
        isSpacer: false,
        label: 'exon 2/4',
        length: 5
      } as TranscriptSegment,
      {
        chromosome: 'exon2',
        start: 12,
        stop: 15,
        isExon: false,
        isCDS: false,
        isSpacer: true,
        label: 'intron 2/3',
        length: 6
      } as TranscriptSegment,
      {
        chromosome: 'exon3',
        start: 15,
        stop: 16,
        isExon: true,
        isCDS: false,
        isSpacer: false,
        label: 'exon 3/4',
        length: 1
      } as TranscriptSegment,
      {
        chromosome: 'exon3',
        start: 16,
        stop: 18,
        isExon: false,
        isCDS: false,
        isSpacer: true,
        label: 'intron 3/3',
        length: 4
      } as TranscriptSegment,
      {
        chromosome: 'exon4',
        start: 18,
        stop: 20,
        isExon: true,
        isCDS: false,
        isSpacer: false,
        label: 'exon 4/4',
        length: 2
      } as TranscriptSegment,
    ];

    for (let i = 0; i < transcript.segments.length; i++) {
      expect(transcript.segments[i].chromosome).toStrictEqual(expectedSegments[i].chromosome);
      expect(transcript.segments[i].start).toStrictEqual(expectedSegments[i].start);
      expect(transcript.segments[i].stop).toStrictEqual(expectedSegments[i].stop);
      expect(transcript.segments[i].isExon).toStrictEqual(expectedSegments[i].isExon);
      expect(transcript.segments[i].isCDS).toStrictEqual(expectedSegments[i].isCDS);
      expect(transcript.segments[i].isSpacer).toStrictEqual(expectedSegments[i].isSpacer);
      expect(transcript.segments[i].label).toStrictEqual(expectedSegments[i].label);
      expect(transcript.segments[i]).toHaveLength(expectedSegments[i].length);
    }
  });

  it('should create from json', () => {
    const transcript = Transcript.fromJson({
      transcript_id: 'testTranscriptId',
      chrom: 'testChrom',
      strand: 'testStrand',
      cds: [{ chromosome: 'chr1', start: 1, stop: 10 }, { chromosome: 'chr2', start: 11, stop: 20 }],
      exons: [{ chromosome: 'chr3', start: 21, stop: 31}, { chromosome: 'chr4', start: 32, stop: 43 }]
    });
    expect(transcript.transcriptId).toBe('testTranscriptId');
    expect(transcript.chromosome).toBe('testChrom');
    expect(transcript.strand).toBe('testStrand');
    expect(transcript.codingSequences).toStrictEqual([
      { chromosome: 'chr1', start: 1, stop: 10 },
      { chromosome: 'chr2', start: 11, stop: 20 }
    ]);
    expect(transcript.exons).toStrictEqual([
      { chromosome: 'chr3', start: 21, stop: 31 },
      { chromosome: 'chr4', start: 32, stop: 43 }
    ]);
  });

  it('should check if area is in CDS', () => {
    const transcript = new Transcript(
      'id',
      'chrom',
      'strand',
      [{ chromosome: 'coding1', start: 1, stop: 5 },
        { chromosome: 'coding1', start: 7, stop: 12 },
        { chromosome: 'coding1', start: 15, stop: 16 }],
      [{ chromosome: 'exon1', start: 1, stop: 5 }]
    );

    expect(transcript.isAreaInCDS(0, 1)).toBeFalsy();
    expect(transcript.isAreaInCDS(5, 7)).toBeFalsy();
    expect(transcript.isAreaInCDS(8, 14)).toBeFalsy();
    expect(transcript.isAreaInCDS(20, 21)).toBeFalsy();
    expect(transcript.isAreaInCDS(2, 5)).toBeTruthy();
    expect(transcript.isAreaInCDS(7, 11)).toBeTruthy();
    expect(transcript.isAreaInCDS(8, 11)).toBeTruthy();
    expect(transcript.isAreaInCDS(15, 16)).toBeTruthy();
  });
});

describe('Gene', () => {
  it('should set collapsed transcript during construction', () => {
    const transcripts = [
      new Transcript(
        'id1',
        'chrom1',
        'strand1',
        [{ chromosome: 'coding1', start: 1, stop: 10 },
          { chromosome: 'coding2', start: 12, stop: 15 }],
        [{ chromosome: 'exon1', start: 7, stop: 11 },
          { chromosome: 'exon2', start: 20, stop: 25 }]
      ),
      new Transcript(
        'id2',
        'chrom2',
        'strand2',
        [{ chromosome: 'coding3', start: 3, stop: 10 },
          { chromosome: 'coding4', start: 18, stop: 20 }],
        [{ chromosome: 'exon3', start: 13, stop: 16 },
          { chromosome: 'exon4', start: 18, stop: 25 }]
      )
    ];

    const expectedTranscripts = [
      new Transcript(
        'collapsed',
        'chrom1',
        'strand1',
        [{ chromosome: 'coding1', start: 1, stop: 10 },
          { chromosome: 'coding2', start: 12, stop: 15 }],
        [{ chromosome: 'exon1', start: 7, stop: 11 }, { chromosome: 'exon2', start: 20, stop: 25 }]
      ),
      new Transcript(
        'collapsed',
        'chrom2',
        'strand1',
        [{chromosome: 'coding3', start: 3, stop: 10}, { chromosome: 'coding4', start: 18, stop: 20 }],
        [{ chromosome: 'exon3', start: 13, stop: 16 },
          { chromosome: 'exon4', start: 18, stop: 25 }]
      )
    ];

    const gene = new Gene('gene1', transcripts);
    expect(gene.collapsedTranscripts).toStrictEqual(expectedTranscripts);
  });

  it('should set chromosomes during construction', () => {
    const transcripts = [
      new Transcript(
        'id1',
        'chrom1',
        'strand1',
        [{ chromosome: '', start: 0, stop: 0 }],
        [{ chromosome: 'exon1', start: 7, stop: 11 },
          { chromosome: 'exon2', start: 20, stop: 25 }]
      ),
      new Transcript(
        'id2',
        'chrom2',
        'strand2',
        [{ chromosome: '', start: 0, stop: 0 }],
        [{ chromosome: 'exon3', start: 13, stop: 16 },
          { chromosome: 'exon4', start: 18, stop: 22 }]
      ),
      new Transcript(
        'id1',
        'chrom1',
        'strand1',
        [{ chromosome: '', start: 0, stop: 0 }],
        [{ chromosome: 'exon1', start: 3, stop: 16 },
          { chromosome: 'exon2', start: 18, stop: 35 }]
      )
    ];

    const gene = new Gene('gene1', transcripts);
    expect(gene.chromosomes.get('chrom1')).toStrictEqual([3, 35]);
    expect(gene.chromosomes.get('chrom2')).toStrictEqual([13, 22]);
  });

  it('should create from json', () => {
    const geneFromJson = Gene.fromJson({
      gene: 'gene1',
      transcripts: [
        { transcript_id: 'testTranscriptId1',
          chrom: 'testChrom1',
          strand: 'testStrand1',
          cds: [{ chromosome: 'chr1', start: 1, stop: 10 }, { chromosome: 'chr2', start: 11, stop: 20 }],
          exons: [{ chromosome: 'chr3', start: 21, stop: 31}, { chromosome: 'chr4', start: 32, stop: 43 }]
        },
        { transcript_id: 'testTranscriptId2',
          chrom: 'testChrom2',
          strand: 'testStrand2',
          cds: [{ chromosome: 'chr5', start: 4, stop: 7 }, { chromosome: 'chr6', start: 9, stop: 15 }],
          exons: [{ chromosome: 'chr7', start: 18, stop: 23}, { chromosome: 'chr8', start: 27, stop: 31 }]
        }
      ]
    });

    const transcripts = [
      new Transcript(
        'testTranscriptId1',
        'testChrom1',
        'testStrand1',
        [{ chromosome: 'chr1', start: 1, stop: 10 }, { chromosome: 'chr2', start: 11, stop: 20 }],
        [{ chromosome: 'chr3', start: 21, stop: 31}, { chromosome: 'chr4', start: 32, stop: 43 }]
      ),
      new Transcript(
        'testTranscriptId2',
        'testChrom2',
        'testStrand2',
        [{ chromosome: 'chr5', start: 4, stop: 7 }, { chromosome: 'chr6', start: 9, stop: 15 }],
        [{ chromosome: 'chr7', start: 18, stop: 23}, { chromosome: 'chr8', start: 27, stop: 31 }]
      )
    ];
    const gene = new Gene('gene1', transcripts);

    expect(geneFromJson).toStrictEqual(gene);
  });

  it('should get region string', () => {
    const transcripts = [
      new Transcript(
        'id1',
        'chrom1',
        'strand1',
        [{ chromosome: '', start: 0, stop: 0 }],
        [{ chromosome: 'exon1', start: 7, stop: 11 },
          { chromosome: 'exon2', start: 20, stop: 25 }]
      ),
      new Transcript(
        'id2',
        'chrom2',
        'strand2',
        [{ chromosome: '', start: 0, stop: 0 }],
        [{ chromosome: 'exon3', start: 13, stop: 16 },
          { chromosome: 'exon4', start: 18, stop: 22 }]
      ),
      new Transcript(
        'id3',
        'chrom3',
        'strand3',
        [{ chromosome: '', start: 0, stop: 0 }],
        [{ chromosome: 'exon5', start: 3, stop: 16 },
          { chromosome: 'exon6', start: 18, stop: 35 }]
      )
    ];

    const gene = new Gene('gene1', transcripts);
    expect(gene.getRegionString(0, 100)).toEqual(['chrom1:7-25', 'chrom2:13-22', 'chrom3:3-35']);
    expect(gene.getRegionString(7, 10)).toEqual(['chrom1:7-10', 'chrom3:7-10']);
    expect(gene.getRegionString(0, 6)).toEqual(['chrom3:3-6']);
    expect(gene.getRegionString(27, 100)).toEqual(['chrom3:27-35']);
  });

  it('should check gene on multiple chromosomes', () => {
    const transcripts = [
      new Transcript(
        'id1',
        'chrom1',
        'strand1',
        [{ chromosome: '', start: 0, stop: 0 }],
        [{ chromosome: 'exon1', start: 7, stop: 11 },
          { chromosome: 'exon2', start: 20, stop: 25 }]
      ),
      new Transcript(
        'id2',
        'chrom2',
        'strand2',
        [{ chromosome: '', start: 0, stop: 0 }],
        [{ chromosome: 'exon3', start: 13, stop: 16 },
          { chromosome: 'exon4', start: 18, stop: 22 }]
      ),
      new Transcript(
        'id3',
        'chrom3',
        'strand3',
        [{ chromosome: '', start: 0, stop: 0 }],
        [{ chromosome: 'exon5', start: 3, stop: 16 },
          { chromosome: 'exon6', start: 18, stop: 35 }]
      )
    ];

    const gene = new Gene('gene1', transcripts);
    expect(gene.collapsedTranscripts).toHaveLength(transcripts.length);
    expect(gene.collapsedTranscripts[0]).toStrictEqual(new Transcript(
      'collapsed',
      'chrom1',
      'strand1',
      [{ chromosome: '', start: 0, stop: 0 }],
      [{ chromosome: 'exon1', start: 7, stop: 11 },
        { chromosome: 'exon2', start: 20, stop: 25 }]
    ));
    expect(gene.collapsedTranscripts[1]).toStrictEqual(new Transcript(
      'collapsed',
      'chrom2',
      'strand1',
      [{ chromosome: '', start: 0, stop: 0 }],
      [{ chromosome: 'exon3', start: 13, stop: 16 },
        { chromosome: 'exon4', start: 18, stop: 22 }]
    ));
    expect(gene.collapsedTranscripts[2]).toStrictEqual(new Transcript(
      'collapsed',
      'chrom3',
      'strand1',
      [{ chromosome: '', start: 0, stop: 0 }],
      [{ chromosome: 'exon5', start: 3, stop: 16 },
        { chromosome: 'exon6', start: 18, stop: 35 }]
    ));
  });
});
