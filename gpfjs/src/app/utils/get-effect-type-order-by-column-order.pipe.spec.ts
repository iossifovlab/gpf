import { DeNovoData, EffectTypeRow, EffectTypeTable } from 'app/variant-reports/variant-reports';
import { GetEffectTypeOrderByColumOrderPipe } from './get-effect-type-order-by-column-order.pipe';

describe('ComparePipe', () => {
  it('should create an instance', () => {
    const pipe = new GetEffectTypeOrderByColumOrderPipe();
    expect(pipe).toBeTruthy();
  });

  it('should get regression ids', () => {
    const effectTypeTable1 = new EffectTypeTable(
      [
        new EffectTypeRow('\'3\'-UTR', [
          DeNovoData.fromJson({
            column: 'autism (2376)',
            number_of_observed_events: 2085,
            number_of_children_with_event: 1350,
            observed_rate_per_child: 0.8775252525252525,
            percent_of_children_with_events: 0.5681818181818182
          }),
          new DeNovoData('unaffected (1941)', 1126, 1756, 0.904688304997424, 0.5801133436373004)
        ])
      ], 'group1',
      [
        'autism (2376)', 'unaffected (1941)'
      ], ['LGDs', 'nonsynonymous', 'UTRs'], [
        'Nonsense',
        'Frame-shift',
        'Splice-site',
        'Missense',
        'No-frame-shift',
        'noStart',
        'noEnd',
        'Synonymous',
        'Non coding',
        'Intron',
        'Intergenic',
        '3\'-UTR',
        '5\'-UTR'
      ]);

    const pipe = new GetEffectTypeOrderByColumOrderPipe();
    expect(pipe.transform('\'3\'-UTR', effectTypeTable1, ['autism (2376)', 'unaffected (1941)'])).toStrictEqual([
      new DeNovoData('autism (2376)', 2085, 1350, 0.8775252525252525, 0.5681818181818182),
      DeNovoData.fromJson({
        column: 'unaffected (1941)',
        number_of_observed_events: 1126,
        number_of_children_with_event: 1756,
        observed_rate_per_child: 0.904688304997424,
        percent_of_children_with_events: 0.5801133436373004
      })]);

    expect(pipe.transform('\'3\'-UTR', effectTypeTable1, ['autism (2376)', 'unaffected (1941)'])).not.toStrictEqual([
      new DeNovoData('(2376)', 2085, 1350, 0.8775252525252525, 0.5681818181818182),
      DeNovoData.fromJson({
        column: 'unaffected (1512)',
        number_of_observed_events: 1126,
        number_of_children_with_event: 1756,
        observed_rate_per_child: 0.904688304997424,
        percent_of_children_with_events: 0.5801133436373004
      })]);
  });
});

