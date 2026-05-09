interface PartitionBucket {
  count: number;
  percent: number;
}

export interface PartitionsJson {
  left: PartitionBucket;
  mid: PartitionBucket;
  right: PartitionBucket;
}

export class Partitions {
  public static fromJson(json: PartitionsJson): Partitions {
    return new Partitions(
      Number(json.left.count),
      Number(json.left.percent),
      Number(json.mid.count),
      Number(json.mid.percent),
      Number(json.right.count),
      Number(json.right.percent),
    );
  }

  public constructor(
    public readonly leftCount: number,
    private readonly leftPercent: number,
    public readonly midCount: number,
    private readonly midPercent: number,
    public readonly rightCount: number,
    private readonly rightPercent: number,
  ) { }
}
