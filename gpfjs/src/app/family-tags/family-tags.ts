import { IsEmpty } from 'class-validator';

export class FamilyTags {
  // @IsEmpty({message: 'Please select at least one family tag.'})
  public selectedTags: string[] = [];
  public deselectedTags: string[] = [];
  public tagIntersection = true; // mode "And"
}
