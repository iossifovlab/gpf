import { IsNotEmpty } from 'class-validator';

export class FamilyIds {
  @IsNotEmpty({message: 'Please insert at least one family id.'})
  public familyIds = '';
}
