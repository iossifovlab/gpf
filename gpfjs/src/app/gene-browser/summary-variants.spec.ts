import { CNV, CODING, LGDS, OTHER } from 'app/effect-types/effect-types';
import { SummaryAllele, SummaryAllelesArray, SummaryAllelesFilter } from './summary-variants';

describe('SummaryAllele', () => {
  let summaryAlleleMock: SummaryAllele;
  beforeEach(() => {
    summaryAlleleMock = new SummaryAllele('l1', 1, 20, 'chr', 'v1', 'CNV+', 1.00003, 2, true, false, true);
  });
  it('should compare alleles', () => {
    const a = new SummaryAllele('l1', 1, 20, 'chr', 'v1', 'CNV+', 1.00003, 2, true, false, true);
    const aComparisonValue = jest.spyOn(a, 'comparisonValue', 'get');
    const b = new SummaryAllele('l2', 2, 20, 'chr', 'v2', 'CNV-', 2.00023, 2, true, false, true);
    const bComparisonValue = jest.spyOn(b, 'comparisonValue', 'get');

    aComparisonValue.mockReturnValue(1);
    bComparisonValue.mockReturnValue(0);
    expect(SummaryAllele.comparator(a, b)).toBe(1);
    aComparisonValue.mockReturnValue(0);
    bComparisonValue.mockReturnValue(1);
    expect(SummaryAllele.comparator(a, b)).toBe(-1);
    aComparisonValue.mockReturnValue(1);
    bComparisonValue.mockReturnValue(1);
    expect(SummaryAllele.comparator(a, b)).toBe(0);
    aComparisonValue.mockReturnValue(0);
    bComparisonValue.mockReturnValue(0);
    expect(SummaryAllele.comparator(a, b)).toBe(0);
  });

  it('should create from row', () => {
    let summaryAllele: SummaryAllele;

    const row = {
      location: 'location1',
      position: 3,
      end_position: 7, // eslint-disable-line
      chrom: 'chrom1',
      variant: 'variant1',
      effect: 'effect1',
      frequency: 13,
      family_variants_count: 17, // eslint-disable-line
      is_denovo: true, // eslint-disable-line
      seen_in_affected: false, // eslint-disable-line
      seen_in_unaffected: true, // eslint-disable-line
    };
    summaryAllele = SummaryAllele.fromRow(row);

    expect(summaryAllele.location).toBe('location1');
    expect(summaryAllele.position).toBe(3);
    expect(summaryAllele.endPosition).toBe(7);
    expect(summaryAllele.chrom).toBe('chrom1');
    expect(summaryAllele.variant).toBe('variant1');
    expect(summaryAllele.effect).toBe('effect1');
    expect(summaryAllele.frequency).toBe(13);
    expect(summaryAllele.numberOfFamilyVariants).toBe(17);
    expect(summaryAllele.seenAsDenovo).toBe(true);
    expect(summaryAllele.seenInAffected).toBe(false);
    expect(summaryAllele.seenInUnaffected).toBe(true);
    expect(summaryAllele.sauid).toStrictEqual(row.location + ':' + row.variant);
    expect(summaryAllele.svuid).toStrictEqual(row.location + ':' + row.variant);

    row.is_denovo = false;
    row.seen_in_affected = true;
    row.seen_in_unaffected = false;
    summaryAllele = SummaryAllele.fromRow(row, 'svuid1');
    expect(summaryAllele.seenAsDenovo).toBe(false);
    expect(summaryAllele.seenInAffected).toBe(true);
    expect(summaryAllele.seenInUnaffected).toBe(false);
    expect(summaryAllele.sauid).toStrictEqual(row.location + ':' + row.variant);
    expect(summaryAllele.svuid).toBe('svuid1');
  });

  it('should get affected status', () => {
    summaryAlleleMock.seenInAffected = true;
    summaryAlleleMock.seenInUnaffected = true;
    expect(summaryAlleleMock.affectedStatus).toBe('Affected and unaffected');

    summaryAlleleMock.seenInAffected = true;
    summaryAlleleMock.seenInUnaffected = false;
    expect(summaryAlleleMock.affectedStatus).toBe('Affected only');

    summaryAlleleMock.seenInAffected = false;
    summaryAlleleMock.seenInUnaffected = true;
    expect(summaryAlleleMock.affectedStatus).toBe('Unaffected only');
  });

  it('should get variant type', () => {
    const summaryAllele = new SummaryAllele('l1', 1, 20, 'chr', 'v1', 'lgds', 1.00003, 2, true, false, true);

    summaryAllele.variant = 'comp(CTCTTGCACGTCCCATCACAGTAGCAAGGAGTACTCACTTGAGCTTGC->A)';
    expect(summaryAllele.variantType).toBe('comp');

    summaryAllele.variant = 'sub(A->C)';
    expect(summaryAllele.variantType).toBe('sub');

    summaryAllele.variant = 'del(3)';
    expect(summaryAllele.variantType).toBe('del');

    summaryAllele.variant = 'ins(T)';
    expect(summaryAllele.variantType).toBe('ins');

    summaryAllele.variant = 'CNV+(149511687-149515015)';
    summaryAllele.effect = 'CNV+';
    expect(summaryAllele.variantType).toBe('CNV+');

    summaryAllele.variant = 'CNV-(249511687-249515015)';
    summaryAllele.effect = 'CNV-';
    expect(summaryAllele.variantType).toBe('CNV-');
  });

  it('should check is lgds', () => {
    summaryAlleleMock.effect = 'lgds';
    expect(summaryAlleleMock.isLGDs()).toBeTruthy();
    summaryAlleleMock.effect = 'nonsense';
    expect(summaryAlleleMock.isLGDs()).toBeTruthy();
    summaryAlleleMock.effect = '';
    expect(summaryAlleleMock.isLGDs()).toBeFalsy();
  });

  it('should check is missense', () => {
    summaryAlleleMock.effect = 'missense';
    expect(summaryAlleleMock.isMissense()).toBeTruthy();
    summaryAlleleMock.effect = '';
    expect(summaryAlleleMock.isMissense()).toBeFalsy();
  });

  it('should check is synonymous', () => {
    summaryAlleleMock.effect = 'synonymous';
    expect(summaryAlleleMock.isSynonymous()).toBeTruthy();
    summaryAlleleMock.effect = '';
    expect(summaryAlleleMock.isSynonymous()).toBeFalsy();
  });

  it('should check is CNV+', () => {
    summaryAlleleMock.effect = 'CNV+';
    expect(summaryAlleleMock.isCNVPlus()).toBeTruthy();
    summaryAlleleMock.effect = '';
    expect(summaryAlleleMock.isCNVPlus()).toBeFalsy();
  });

  it('should check is CNV-', () => {
    summaryAlleleMock.effect = 'CNV-';
    expect(summaryAlleleMock.isCNVMinus()).toBeTruthy();
    summaryAlleleMock.effect = '';
    expect(summaryAlleleMock.isCNVMinus()).toBeFalsy();
  });

  it('should check is CNV', () => {
    summaryAlleleMock.effect = 'CNV+';
    expect(summaryAlleleMock.isCNV()).toBeTruthy();
    summaryAlleleMock.effect = 'CNV-';
    expect(summaryAlleleMock.isCNV()).toBeTruthy();
    summaryAlleleMock.effect = '';
    expect(summaryAlleleMock.isCNV()).toBeFalsy();
  });

  it('should get comparison value', () => {
    const summaryAllele1 = new SummaryAllele('l1', 1, 20, 'chr', 'v1', 'CNV+', 1.00003, 2, true, false, true);
    summaryAllele1.seenAsDenovo = false;
    summaryAllele1.effect = 'CNV+';
    summaryAllele1.seenInAffected = true;
    summaryAllele1.seenInUnaffected = true;

    const summaryAllele2 = new SummaryAllele('l1', 1, 20, 'chr', 'v1', 'CNV+', 1.00003, 2, true, false, true);
    summaryAllele2.seenAsDenovo = false;
    summaryAllele2.effect = 'CNV+';
    summaryAllele2.seenInAffected = false;
    summaryAllele2.seenInUnaffected = true;

    const summaryAllele3 = new SummaryAllele('l1', 1, 20, 'chr', 'v1', 'CNV+', 1.00003, 2, true, false, true);
    summaryAllele3.seenAsDenovo = false;
    summaryAllele3.effect = 'CNV+';
    summaryAllele3.seenInAffected = true;
    summaryAllele3.seenInUnaffected = false;

    const summaryAllele4 = new SummaryAllele('l1', 1, 20, 'chr', 'v1', 'CNV+', 1.00003, 2, true, false, true);
    summaryAllele4.seenAsDenovo = true;
    summaryAllele4.effect = 'CNV+';

    const summaryAllele5 = new SummaryAllele('l1', 1, 20, 'chr', 'v1', 'CNV+', 1.00003, 2, true, false, true);
    summaryAllele5.seenAsDenovo = false;
    summaryAllele5.effect = 'intron';

    const summaryAllele6 = new SummaryAllele('l1', 1, 20, 'chr', 'v1', 'CNV+', 1.00003, 2, true, false, true);
    summaryAllele6.seenAsDenovo = false;
    summaryAllele6.effect = 'synonymous';

    const summaryAllele7 = new SummaryAllele('l1', 1, 20, 'chr', 'v1', 'CNV+', 1.00003, 2, true, false, true);
    summaryAllele7.seenAsDenovo = false;
    summaryAllele7.effect = 'missense';

    const summaryAllele8 = new SummaryAllele('l1', 1, 20, 'chr', 'v1', 'CNV+', 1.00003, 2, true, false, true);
    summaryAllele8.seenAsDenovo = false;
    summaryAllele8.effect = 'lgds';

    const summaryAllele9 = new SummaryAllele('l1', 1, 20, 'chr', 'v1', 'CNV+', 1.00003, 2, true, false, true);
    summaryAllele9.seenAsDenovo = true;
    summaryAllele9.effect = 'lgds';

    expect(summaryAllele1.comparisonValue < summaryAllele2.comparisonValue).toBeTruthy();
    expect(summaryAllele2.comparisonValue < summaryAllele3.comparisonValue).toBeTruthy();
    expect(summaryAllele3.comparisonValue < summaryAllele4.comparisonValue).toBeTruthy();
    expect(summaryAllele4.comparisonValue < summaryAllele5.comparisonValue).toBeTruthy();
    expect(summaryAllele5.comparisonValue < summaryAllele6.comparisonValue).toBeTruthy();
    expect(summaryAllele6.comparisonValue < summaryAllele7.comparisonValue).toBeTruthy();
    expect(summaryAllele7.comparisonValue < summaryAllele8.comparisonValue).toBeTruthy();
    expect(summaryAllele8.comparisonValue < summaryAllele9.comparisonValue).toBeTruthy();
  });

  it('should check if intersects', () => {
    const summaryAllele1 = new SummaryAllele('l1', 1, 20, 'chr', 'v1', 'CNV+', 1.00003, 2, true, false, true);
    const summaryAllele2 = new SummaryAllele('l1', 1, 20, 'chr', 'v1', 'CNV+', 1.00003, 2, true, false, true);

    summaryAllele1.effect = 'lgds';
    summaryAllele1.position = 13;
    summaryAllele2.effect = 'lgds';
    summaryAllele2.position = 13;
    expect(summaryAllele1.intersects(summaryAllele2)).toBeTruthy();
    expect(summaryAllele2.intersects(summaryAllele1)).toBeTruthy();
    summaryAllele1.position = 13;
    summaryAllele2.position = 14;
    expect(summaryAllele1.intersects(summaryAllele2)).toBeFalsy();
    expect(summaryAllele2.intersects(summaryAllele1)).toBeFalsy();

    summaryAllele1.effect = 'CNV+';
    summaryAllele1.position = 13;
    summaryAllele1.endPosition = 17;
    summaryAllele2.effect = 'CNV-';
    summaryAllele2.position = 3;
    summaryAllele2.endPosition = 15;
    expect(summaryAllele1.intersects(summaryAllele2)).toBeTruthy();
    expect(summaryAllele2.intersects(summaryAllele1)).toBeTruthy();
    summaryAllele1.position = 13;
    summaryAllele1.endPosition = 17;
    summaryAllele2.position = 14;
    summaryAllele2.endPosition = 23;
    expect(summaryAllele1.intersects(summaryAllele2)).toBeTruthy();
    expect(summaryAllele2.intersects(summaryAllele1)).toBeTruthy();
    summaryAllele1.position = 13;
    summaryAllele1.endPosition = 17;
    summaryAllele2.position = 18;
    summaryAllele2.endPosition = 23;
    expect(summaryAllele1.intersects(summaryAllele2)).toBeFalsy();
    expect(summaryAllele2.intersects(summaryAllele1)).toBeFalsy();
    summaryAllele1.position = 13;
    summaryAllele1.endPosition = 17;
    summaryAllele2.position = 1;
    summaryAllele2.endPosition = 12;
    expect(summaryAllele1.intersects(summaryAllele2)).toBeFalsy();
    expect(summaryAllele2.intersects(summaryAllele1)).toBeFalsy();

    summaryAllele1.effect = 'lgds';
    summaryAllele1.position = 13;
    summaryAllele2.effect = 'CNV+';
    summaryAllele2.position = 3;
    summaryAllele2.endPosition = 15;
    expect(summaryAllele1.intersects(summaryAllele2)).toBeTruthy();
    expect(summaryAllele2.intersects(summaryAllele1)).toBeTruthy();
    summaryAllele1.position = 13;
    summaryAllele2.position = 14;
    summaryAllele2.endPosition = 15;
    expect(summaryAllele1.intersects(summaryAllele2)).toBeFalsy();
    expect(summaryAllele2.intersects(summaryAllele1)).toBeFalsy();
    summaryAllele1.position = 13;
    summaryAllele2.position = 3;
    summaryAllele2.endPosition = 12;
    expect(summaryAllele1.intersects(summaryAllele2)).toBeFalsy();
    expect(summaryAllele2.intersects(summaryAllele1)).toBeFalsy();
  });
});

describe('SummaryAllelesArray', () => {
  let summaryAlleleMock: SummaryAllele;
  beforeEach(() => {
    summaryAlleleMock = new SummaryAllele('l1', 1, 20, 'chr', 'v1', 'CNV+', 1.00003, 2, true, false, true);
  });
  it('should add summary row', () => {
    const row = {
      alleles: [
        {
          location: 'location1',
          position: 3,
          end_position: 7, //eslint-disable-line
          chrom: 'chrom1',
          variant: 'variant1',
          effect: 'effect1',
          frequency: 13,
          family_variants_count: 17, //eslint-disable-line
          is_denovo: true, //eslint-disable-line
          seen_in_affected: false, //eslint-disable-line
          seen_in_unaffected: true, //eslint-disable-line
        },
        {
          location: 'location2',
          position: 4,
          end_position: 9, //eslint-disable-line
          chrom: 'chrom2',
          variant: 'variant2',
          effect: 'effect2',
          frequency: 14,
          family_variants_count: 16, //eslint-disable-line
          is_denovo: false, //eslint-disable-line
          seen_in_affected: false, //eslint-disable-line
          seen_in_unaffected: false, //eslint-disable-line
        }
      ]
    };
    const summaryAlleleArray = new SummaryAllelesArray();
    summaryAlleleArray.addSummaryRow(row);
    expect(summaryAlleleArray.summaryAlleles).toStrictEqual([
      SummaryAllele.fromRow(row.alleles[0]),
      SummaryAllele.fromRow(row.alleles[1])
    ]);
  });

  it('should get total family variants count', () => {
    const summaryAlleleArray = new SummaryAllelesArray();
    const summaryAllele = summaryAlleleMock;

    summaryAllele.numberOfFamilyVariants = 3;
    summaryAllele.sauid = 'sauid1';
    summaryAlleleArray.addSummaryAllele(summaryAllele);
    summaryAllele.numberOfFamilyVariants = 7;
    summaryAllele.sauid = 'sauid2';
    summaryAlleleArray.addSummaryAllele(summaryAllele);
    summaryAllele.numberOfFamilyVariants = 13;
    summaryAllele.sauid = 'sauid3';
    summaryAlleleArray.addSummaryAllele(summaryAllele);
    summaryAllele.numberOfFamilyVariants = 19;
    summaryAllele.sauid = 'sauid4';
    summaryAlleleArray.addSummaryAllele(summaryAllele);

    expect(summaryAlleleArray.totalFamilyVariantsCount).toBe(76);
  });
});

describe('SummaryAllelesFilter', () => {
  it('should construct with default values', () => {
    const summaryAllelesFilter = new SummaryAllelesFilter();
    expect(summaryAllelesFilter.denovo).toBeTruthy();
    expect(summaryAllelesFilter.transmitted).toBeTruthy();
    expect(summaryAllelesFilter.codingOnly).toBeTruthy();
    expect(summaryAllelesFilter.selectedAffectedStatus).toStrictEqual(new Set());
    expect(summaryAllelesFilter.selectedEffectTypes).toStrictEqual(new Set());
    expect(summaryAllelesFilter.selectedVariantTypes).toStrictEqual(new Set());
  });

  it('should get min frequency', () => {
    const summaryAllelesFilter = new SummaryAllelesFilter();
    summaryAllelesFilter.selectedFrequencies = [-1, undefined];
    expect(summaryAllelesFilter.minFreq).toBeNull();
    summaryAllelesFilter.selectedFrequencies = [13, undefined];
    expect(summaryAllelesFilter.minFreq).toBe(13);
  });

  it('should get max frequency', () => {
    const summaryAllelesFilter = new SummaryAllelesFilter();
    summaryAllelesFilter.selectedFrequencies = [undefined, 17];
    expect(summaryAllelesFilter.maxFreq).toBe(17);
  });

  it('should filter summary variants array', () => {
    const summaryAllelesFilter = new SummaryAllelesFilter();
    const summaryAlleleArray = new SummaryAllelesArray();

    const row = {
      alleles: [
        // wanted allele
        {
          location: '1',
          is_denovo: false, //eslint-disable-line
          seen_in_affected: true, //eslint-disable-line
          seen_in_unaffected: false, //eslint-disable-line
          variant: 'sub(G->A)',
          effect: 'frame-shift',
          frequency: 10,
          position: 30,
          end_position: 30, //eslint-disable-line
          family_variants_count: 1, //eslint-disable-line
          chrom: '',
        },
        // wanted allele
        {
          location: '2',
          is_denovo: false, //eslint-disable-line
          seen_in_affected: true, //eslint-disable-line
          seen_in_unaffected: false, //eslint-disable-line
          variant: 'CNV+',
          effect: 'CNV+',
          frequency: 5,
          position: 25,
          end_position: 35, //eslint-disable-line
          family_variants_count: 1, //eslint-disable-line
          chrom: '',
        },
        // unwanted allele
        {
          location: '3',
          // filtered out because:
          is_denovo: true, //eslint-disable-line
          //
          seen_in_affected: true, //eslint-disable-line
          seen_in_unaffected: false, //eslint-disable-line
          variant: 'CNV+',
          effect: 'CNV+',
          frequency: 5,
          position: 25,
          end_position: 35, //eslint-disable-line
          family_variants_count: 1, //eslint-disable-line
          chrom: '',
        },
        // unwanted allele
        {
          location: '4',
          is_denovo: false, //eslint-disable-line
          // filtered out because:
          seen_in_affected: false, //eslint-disable-line
          seen_in_unaffected: true, //eslint-disable-line
          //
          variant: 'sub(G->T)',
          effect: 'CNV+',
          frequency: 5,
          position: 25,
          end_position: 35, //eslint-disable-line
          family_variants_count: 1, //eslint-disable-line
          chrom: '',
        },
        // unwanted allele
        {
          location: '5',
          is_denovo: false, //eslint-disable-line
          seen_in_affected: true, //eslint-disable-line
          seen_in_unaffected: false, //eslint-disable-line
          // filtered out because:
          variant: 'fake(A->T)',
          //
          effect: 'CNV+',
          frequency: 5,
          position: 25,
          end_position: 35, //eslint-disable-line
          family_variants_count: 1, //eslint-disable-line
          chrom: '',
        },
        // unwanted allele
        {
          location: '6',
          is_denovo: false, //eslint-disable-line
          seen_in_affected: true, //eslint-disable-line
          seen_in_unaffected: false, //eslint-disable-line
          variant: 'sub(G->T)',
          // filtered out because:
          effect: 'fake',
          //
          frequency: 5,
          position: 25,
          end_position: 35, //eslint-disable-line
          family_variants_count: 1, //eslint-disable-line
          chrom: '',
        },
        // unwanted allele
        {
          location: '7',
          is_denovo: false, //eslint-disable-line
          seen_in_affected: true, //eslint-disable-line
          seen_in_unaffected: false, //eslint-disable-line
          variant: 'sub(T->G)',
          effect: 'lgds',
          // filtered out because:
          frequency: 4,
          //
          position: 30,
          end_position: 30, //eslint-disable-line
          family_variants_count: 1, //eslint-disable-line
          chrom: '',
        },
        // unwanted allele
        {
          location: '8',
          is_denovo: false, //eslint-disable-line
          seen_in_affected: true, //eslint-disable-line
          seen_in_unaffected: false, //eslint-disable-line
          variant: 'sub(C->T)',
          effect: 'lgds',
          // filtered out because:
          frequency: 16,
          //
          position: 30,
          end_position: 30, //eslint-disable-line
          family_variants_count: 1, //eslint-disable-line
          chrom: '',
        },
        // unwanted allele
        {
          location: '9',
          is_denovo: false, //eslint-disable-line
          seen_in_affected: true, //eslint-disable-line
          seen_in_unaffected: false, //eslint-disable-line
          variant: 'CNV+',
          effect: 'CNV+',
          frequency: 5,
          // filtered out because:
          position: 20,
          end_position: 24, //eslint-disable-line
          //
          family_variants_count: 1, //eslint-disable-line
          chrom: '',
        },
        // unwanted allele
        {
          location: '10',
          is_denovo: false, //eslint-disable-line
          seen_in_affected: true, //eslint-disable-line
          seen_in_unaffected: false, //eslint-disable-line
          variant: 'CNV+',
          effect: 'CNV+',
          frequency: 5,
          // filtered out because:
          position: 36,
          end_position: 45, //eslint-disable-line
          //
          family_variants_count: 1, //eslint-disable-line
          chrom: '',
        },
        // unwanted allele
        {
          location: '11',
          is_denovo: false, //eslint-disable-line
          seen_in_affected: true, //eslint-disable-line
          seen_in_unaffected: false, //eslint-disable-line
          variant: 'sub(T->C)',
          effect: 'lgds',
          frequency: 10,
          // filtered out because:
          position: 24,
          end_position: 24, //eslint-disable-line
          //
          family_variants_count: 1, //eslint-disable-line
          chrom: '',
        },
      ]
    };
    summaryAlleleArray.addSummaryRow(row);

    summaryAllelesFilter.denovo = false;
    summaryAllelesFilter.selectedAffectedStatus = new Set(['Affected only']);
    summaryAllelesFilter.selectedEffectTypes = new Set([...LGDS, ...CODING, ...CNV]);
    summaryAllelesFilter.selectedVariantTypes = new Set(['sub', 'ins', 'del', 'CNV+', 'CNV-', 'comp']);
    summaryAllelesFilter.selectedFrequencies = [5, 15];
    summaryAllelesFilter.selectedRegion = [25, 35];

    const filteredSummaryAllelesArray = summaryAllelesFilter.filterSummaryVariantsArray(summaryAlleleArray);

    expect(filteredSummaryAllelesArray.summaryAlleles).toStrictEqual([
      summaryAlleleArray.summaryAlleles[0],
      summaryAlleleArray.summaryAlleles[1]
    ]);
  });

  it('should get query params', () => {
    const summaryAllelesFilter = new SummaryAllelesFilter();
    summaryAllelesFilter.codingOnly = false;
    summaryAllelesFilter.selectedAffectedStatus = new Set(['Affected only']);
    summaryAllelesFilter.selectedEffectTypes = new Set([...LGDS, ...CODING, ...CNV, ...OTHER]);
    summaryAllelesFilter.selectedVariantTypes = new Set(['sub', 'ins']);
    expect(summaryAllelesFilter.queryParams).toStrictEqual({
      effectTypes: [
        'frame-shift',
        'nonsense',
        'splice-site',
        'no-frame-shift-newStop',
        'missense',
        'no-frame-shift',
        'noStart',
        'noEnd',
        'synonymous',
        'CNV+',
        'CNV-',
        '3\'UTR',
        '3\'UTR-intron',
        '5\'UTR',
        '5\'UTR-intron',
        'intergenic',
        'intron',
        'non-coding',
        'non-coding-intron',
        'CDS',
      ],
      inheritanceTypeFilter: ['denovo', 'mendelian', 'omission', 'missing'],
      affectedStatus: ['Affected only'],
      variantTypes: ['sub', 'ins']
    });
  });
});
