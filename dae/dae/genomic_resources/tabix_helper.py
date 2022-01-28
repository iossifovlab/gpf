import struct
import gzip
import logging

logger = logging.getLogger(__name__)


class TabixHelper:

    TABIX_MAGIC = b'TBI\x01'
    TABIX_BLOCK_BYTES_MASK = 0x0000000000000FFFF
    FEXTRA = 4

    GZIP_MAGIC          = b"\x1F\x8B"

    # samtools format specs:
    # https://samtools.github.io/hts-specs/SAMv1.pdf
    # https://github.com/xbrianh/bgzip/blob/master/bgzip/__init__.py
    BGZIP_EOF = bytes.fromhex(
        "1f8b08040000000000ff0600424302001b0003000000000000000000")

    def __init__(self, filename, index_filename):
        self.filename = filename
        self.index_filename = index_filename
        self.bgzfile = None
        self.bgz_block = None
        self.index = None
    
    def open(self):
        assert self.index is None
        assert self.bgzfile is None

        self.index = gzip.open(self.index_filename, "rb")
        self.bgzfile = open(self.filename, "rb")
        self._load_bgzheader()

    def close(self):
        assert self.index is not None
        self.index.close()
        self.index = None

    def read_values(self, fmt):
        size = struct.calcsize(fmt)
        packet = self.index.read(size)

        res = struct.unpack(fmt, packet)
        return res

    def _load_bgzheader(self):
        magic = self.bgzfile.read(2)
        if magic != b"\037\213":
            raise IOError(f"not a bgzip file: {self.filename}")
        
        method, flag, last_mtime = struct.unpack(
            "<BBIxx", self.bgzfile.read(8))
        logger.debug(f"method: {method:0x}")
        logger.debug(f"flag: {flag:0x}")
        logger.debug(f"last_mtime: {last_mtime}")

        if not flag & self.FEXTRA:
            raise IOError(f"not a bgzip file: {self.filename}")
        
        # Read & discard the extra field, if present
        extra_len, = struct.unpack("<H", self.bgzfile.read(2))
        extra_data = self.bgzfile.read(extra_len)
        logger.debug(f"extra length {extra_len}")
        logger.debug(f"extra data   {extra_data}")

        if b"BC" not in extra_data:
            raise IOError(b"not a bgzip file: {self.filename}")

        bci            = extra_data.index(b'BC')
        subfield_len_d = extra_data[bci + 2:bci + 2 + 2]
        subfield_len,  = struct.unpack("<H", subfield_len_d)
        logger.debug(f"subfield len {subfield_len} ({subfield_len_d})")
        
        block_len_d    = extra_data[bci + 2 + 2:bci + 2 + 2 + subfield_len]
        block_len,     = struct.unpack("<H", block_len_d)
        logger.debug(f"block len    {block_len + 1:12,d}")

        self.bgz_block = block_len + 1

        self.bgzfile.seek(0)

    def _load_block(self, pos):
        self.bgzfile.seek(pos)
        blockdata = self.bgzfile.read(self.bgz_block)
        block = gzip.decompress(blockdata)
        blocktext = block.decode()

        return blocktext

    def load_index(self):

        (magic, ) = self.read_values("<4s")
        if magic != self.TABIX_MAGIC:
            logger.error(
                f"wrong tabix index magic {magic} in {self.index_filename}")
            raise ValueError("wrong tabix index magic")
        self.data = {}

        self._load_header()
        self._load_names()
        self._load_bins()
    
    def _load_bins(self):
        sequencies = []
        for seq_index in range(self.data["n_ref"]):
            seq_data = {}
            seq_data["seq_index"] = seq_index
            seq_data["name"] = self.data["names"][seq_index]

            (n_bins, ) = self.read_values("<i")
            logger.debug(f"seq '{seq_data['name']}' (index {seq_index})")
            logger.debug(f"n_bins={n_bins}")

            seq_data["n_bins"] = n_bins
            seq_data["bins"] = []

            bins_data = []
            for bin_index in range(n_bins):
                (bin, ) = self.read_values("<I")
                (n_chunk, ) = self.read_values("<i")

                logger.debug(
                    f"bin_index   {bin_index}/{n_bins}")
                logger.debug(
                    f"bin     Distinct bin number  uint32_t {bin:15,d}")
                logger.debug(
                    f"n_chunk # chunks             int32_t  {n_chunk:15,d}")
                
                chunks_data = self._load_chunks(n_chunk)
        
                bins_data.append({
                    "bin_index": bin_index,
                    "bin": bin,
                    "n_chunk": n_chunk,
                    "chunks_data": chunks_data,
                })
            seq_data["bins"] = bins_data
            (n_intv,)  = self.read_values('<i')
            logger.debug(
                f"n_intv   # 16kb intervals (for the linear index) int32_t "
                f"{n_intv:15,d}")

            seq_data["n_intv"] = n_intv
            ioffs_data = []
            for intv_index in range(n_intv):
                (ioff, ) = self.read_values("<Q")
                ioffs_data.append({
                    "intv_index": intv_index,
                    "ioff": ioff
                })
                logger.debug(
                    f"interval {intv_index}/{n_intv}: ioff={ioff:0x}"
                )
            seq_data["ioffs"] = ioffs_data

        sequencies.append(seq_data)
        return sequencies

    def _load_chunks(self, n_chunk):
        chunks_data = []
        for cnk_index in range(n_chunk):
            (cnk_beg, cnk_end,) = self.read_values("<QQ")
            logger.debug(f"cnk_index = {cnk_index}")
            logger.debug(f"cnk_beg   = {cnk_beg:16x}")
            logger.debug(f"cnk_end   = {cnk_end:16x}")

            cnk_real_begin = cnk_beg >> 16
            cnk_real_end = cnk_end >> 16

            cnk_data = {
                "cnk_index": cnk_index,
                "cnk_beg": cnk_beg,
                "cnk_real_beg": cnk_beg >> 16,
                "cnk_bytes_beg": cnk_beg & self.TABIX_BLOCK_BYTES_MASK,
                "cnk_end": cnk_end,
                "cnk_real_end": cnk_end >> 16,
                "cnk_bytes_end": cnk_end & self.TABIX_BLOCK_BYTES_MASK,
            }
            logger.debug(f"chunk data: {cnk_data}")
            chunks_data.append(cnk_data)

            block = self._load_block(0)
            logger.debug(f"block: {block}")

        return chunks_data


    def _load_names(self):
        l_nm = self.data["l_nm"]
        names = self.index.read(l_nm)
        result = [n.decode("utf8") for n in names.split(b"\x00") if n]
        logger.debug(f"sequence names loaded: {result}")

        self.data["names"] = result

    def _load_header(self):        
        (
            n_ref,    # # sequences                              int32_t
            f_format, # Format (0: generic; 1: SAM; 2: VCF)      int32_t
            col_seq,  # Column for the sequence name             int32_t
            col_beg,  # Column for the start of a region         int32_t
            col_end,  # Column for the end of a region           int32_t
            meta,     # Leading character for comment lines      int32_t
            skip,     # # lines to skip at the beginning         int32_t
            l_nm      # Length of concatenated sequence names    int32_t
        ) = self.read_values('<8i')

        logger.debug(
            f"n_ref    # sequences                           int32_t "
            f"{n_ref:15,d}")
        logger.debug(
            f"format   Format (0: generic; 1: SAM; 2: VCF)   int32_t "
            f"{f_format:15,d}")
        logger.debug(
            f"col_seq  Column for the sequence name          int32_t "
            f"{col_seq:15,d}")
        logger.debug(
            f"col_beg  Column for the start of a region      int32_t "
            f"{col_beg:15,d}")
        logger.debug(
            f"col_end  Column for the end of a region        int32_t "
            f"{col_end:15,d}")
        logger.debug(
            f"meta     Leading character for comment lines   int32_t "
            f"{meta:15,d}")
        logger.debug(
            f"skip     # lines to skip at the beginning      int32_t "
            f"{skip:15,d}")
        logger.debug(
            f"l_nm     Length of concatenated sequence names int32_t "
            f"{l_nm:15,d}")

        self.data["n_ref"] = n_ref
        self.data["format"] = f_format
        self.data["col_seq"] = col_seq
        self.data["col_beg"] = col_beg
        self.data["col_end"] = col_end
        self.data["meta"] = chr(meta)
        self.data["skip"] = skip
        self.data["l_nm"] = l_nm
