
export class IdDescription {

  constructor(
    readonly id: string,
    readonly description: string
  ) { }
}

export class Phenotype extends IdDescription {
  constructor(
    readonly id: string,
    readonly description: string,
    readonly color: string
  ) {
    super(id, description);
  }
}

export class Dataset extends IdDescription {
  constructor(
    readonly id: string,
    readonly description: string,
    readonly hasDenovo: boolean,
    readonly hasTransmitted: boolean,
    readonly hasCnv: boolean
  ) {
    super(id, description);
  }


}
