import { ArrayNotEmpty } from 'class-validator';

export const ALL_STATES = new Set([
  'affected only',
  'unaffected only',
  'affected and unaffected',
  'neither'
]);

export class PresentInChild {
  @ArrayNotEmpty({
    message: 'select at least one'
  })
  selected: Set<string> = new Set([
    'affected only',
    'affected and unaffected'
  ]);
}
