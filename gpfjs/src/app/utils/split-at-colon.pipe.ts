import { Pipe, PipeTransform } from '@angular/core';


@Pipe({
  name: "splitAtColon"
})
export class SplitAtColonPipe implements PipeTransform {
  transform(val:string, beforeOrAfter: string):string {
    let result = val.split(":")
    if (beforeOrAfter === "before") {
      return result[0];
    }
    else if (beforeOrAfter === "after") {
      return result[1];
    }
    return ""
  }
}
