import { IsNotEmpty } from 'class-validator';

export class FamilyIds {

  @IsNotEmpty()
  familyIds = '';
};
