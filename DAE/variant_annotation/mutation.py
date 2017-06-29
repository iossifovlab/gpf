class Mutation:
    def __init__(self, pos, ref, alt):
        self.start_position = pos
        self.end_ref_position = pos + len(ref) - 1
        self.end_alt_position = pos + len(alt) - 1
        self.length_diff = len(alt) - len(ref)
        self.ref = ref
        self.alt = alt

    def get_mutated_sequence(self, pos, pos_end):
        print("GET", pos, pos_end, self.start_position, self.end_alt_position)
        start_position = max(0, pos - self.start_position)
        end_position = pos_end - self.end_alt_position
        print("MUT", start_position, end_position)
        if end_position < 0:
            return self.alt[start_position:end_position]
        else:
            return self.alt[start_position:]


class MutatedGenomicSequence:
    def __init__(self, genome_seq, mutation):
        self.genome_seq = genome_seq
        self.mutation = mutation

    def clamp(self, val, min_val, max_val):
        return min(max_val, max(min_val, val))

    def get_sequence(self, chromosome, pos_start, pos_end):
        print("GETS", pos_start, pos_end)
        if pos_start > pos_end:
            return ""
        return self.genome_seq.getSequence(chromosome, pos_start,
                                           pos_end)

    def get_mutated_sequence(self, chromosome, pos, pos_end):
        mutation_start = self.clamp(self.mutation.start_position,
                                    pos, pos_end + 1)

        result = self.get_sequence(chromosome, pos, mutation_start - 1)
        result += self.mutation.get_mutated_sequence(pos, pos_end)

        mutation_end = self.clamp(self.mutation.end_alt_position + 1,
                                  pos, pos_end + 1)
        result += self.get_sequence(chromosome,
                                    mutation_end - self.mutation.length_diff,
                                    pos_end - self.mutation.length_diff)

        return result
