import { GenomicScore } from 'app/genomic-scores-block/genomic-scores-block';
import { BrowserQueryFilter, PersonSetCollection } from './genotype-browser';

describe('BrowserQueryFilter', () => {
  it('should create from json', () => {
    const browserQueryFilterMock = new BrowserQueryFilter(
      'name1', ['gene2', 'gene3'], ['effectType4', 'effectType5'],
      ['gender6', 'gender7'], new PersonSetCollection('id8', ['9', '10']),
      ['studyType11', 'studyType12'], ['variant13', 'variant14']
    );

    const browserQueryFilterMockFromJson = BrowserQueryFilter.fromJson(
      {
        datasetId: 'name1', geneSymbols: ['gene2', 'gene3'], effectTypes: ['effectType4', 'effectType5'],
        gender: ['gender6', 'gender7'], peopleGroup: { id: 'id8', checkedValues: ['9', '10'] },
        studyTypes: ['studyType11', 'studyType12'], variantTypes: ['variant13', 'variant14']
      }
    );

    expect(browserQueryFilterMock).toStrictEqual(browserQueryFilterMockFromJson);
  });
});

describe('PersonSetCollection', () => {
  it('should create from json', () => {
    expect(new PersonSetCollection('id1', ['check1', 'check2'])).toStrictEqual(PersonSetCollection.fromJson({
      id: 'id1',
      checkedValues: ['check1', 'check2']
    }));
  });
});
