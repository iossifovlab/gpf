import { GeneViewTranscriptSegment } from './gene-view';

describe('GeneViewTranscriptSegment', () => {
  it('should have working getters', () => {
    const geneViewTranscriptSegment = new GeneViewTranscriptSegment(
      '1', 1109286, 1109306, true, false, false, 'exon 1/16'
    );

    expect(geneViewTranscriptSegment.chrom).toBe('1');
    expect(geneViewTranscriptSegment.start).toBe(1109286);
    expect(geneViewTranscriptSegment.stop).toBe(1109306);
    expect(geneViewTranscriptSegment.isExon).toBe(true);
    expect(geneViewTranscriptSegment.isCDS).toBe(false);
    expect(geneViewTranscriptSegment.isSpacer).toBe(false);
    expect(geneViewTranscriptSegment.label).toBe('exon 1/16');
  });

  it('should calculate length for a spacer segment', () => {
    const geneViewTranscriptSegment = new GeneViewTranscriptSegment(
      '1', 10, 100, true, false, false, 'exon 1/16'
    );
    expect(geneViewTranscriptSegment.length).toBe(90);
  });

  it('should calculate length for a non spacer segment', () => {
    const geneViewTranscriptSegment = new GeneViewTranscriptSegment(
      '1', 10, 100, true, false, true, 'exon 1/16'
    );
    expect(geneViewTranscriptSegment.length).toBe(180);
  });

  it('should calculate isIntron when isCDS is false', () => {
    const geneViewTranscriptSegment = new GeneViewTranscriptSegment(
      '1', 1109286, 1109306, true, false, false, 'exon 1/16'
    );
    expect(geneViewTranscriptSegment.isIntron).toBe(true);
  });

  it('should calculate isIntron when isCDS is true', () => {
    const geneViewTranscriptSegment = new GeneViewTranscriptSegment(
      '1', 1109286, 1109306, true, true, false, 'exon 1/16'
    );
    expect(geneViewTranscriptSegment.isIntron).toBe(false);
  });

  it('should calculate intersectionLength', () => {
    const geneViewTranscriptSegment = new GeneViewTranscriptSegment(
      '1', 10, 100, true, false, false, 'exon 1/16'
    );
    expect(geneViewTranscriptSegment.intersectionLength(5, 105)).toBe(90);
    expect(geneViewTranscriptSegment.intersectionLength(100, 10)).toBe(0);
  });

  it('should calculate isSubSegment', () => {
    const geneViewTranscriptSegment = new GeneViewTranscriptSegment(
      '1', 10, 100, true, false, false, 'exon 1/16'
    );
    expect(geneViewTranscriptSegment.isSubSegment(5, 105)).toBe(true);
    expect(geneViewTranscriptSegment.isSubSegment(100, 10)).toBe(false);
  });
});
