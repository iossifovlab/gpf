import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ValidationError, validate } from 'class-validator';

export function toValidationObservable<T>(obj: T): Observable<T> {
  return Observable.fromPromise(validate(obj))
    .switchMap(errors => {
      if (errors.length === 0) {
        return Observable.of(obj);
      }
      return Observable.throw(errors);
    });
};


export function validationErrorsToStringArray(validationErrors: ValidationError[]): Array<string> {
  let errors: string[] = [];
  validationErrors.map((elem) => {
    for (let object in elem.constraints) {
      if (elem.constraints.hasOwnProperty(object)) {
        errors.push(elem.constraints[object]);
      }
    }
  });
  return errors;
}
