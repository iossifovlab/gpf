import { Injectable } from '@angular/core';
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { transformAndValidate } from "class-transformer-validator";
import { ValidationError } from "class-validator";

export const toObservableWithValidation = <T>(targetClass, observable: Observable<object>): Observable<[T, boolean, ValidationError[]]> => {
  return observable.switchMap(value => {
    return Observable.fromPromise(transformAndValidate(targetClass, value)).map(validationState => {
      return [value, true, []];
    })
    .catch(errors => {
      return Observable.of([value, false, errors]);
    });

  });
}


export const validationErrorsToStringArray = (validationErrors: ValidationError[]): Array<string> => {
  let errors: string[] = [];
  validationErrors.map((elem) => {
    for (let object in elem.constraints) {
      errors.push(elem.constraints[object]);
    }
  });
  return errors;
}
