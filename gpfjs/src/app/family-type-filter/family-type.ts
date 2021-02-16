import { ArrayNotEmpty } from 'class-validator';

export class FamilyTypes {
  @ArrayNotEmpty()
  familyTypes: string[] = new Array();
}
