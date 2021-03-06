#!/usr/bin/env python

"""Unit tests for the CNVkit library, cnvlib."""
from __future__ import absolute_import, division, print_function

import unittest

import numpy as np
# from Bio._py3k import StringIO

import cnvlib
# Import all modules as a smoke test
from cnvlib import (access, antitarget, commands, core, coverage, diagram,
                    export, fix, importers, metrics, ngfrills, params, plots,
                    reference, reports, segmentation, smoothing,
                    gary, cnary, vary, rary)


class GaryTests(unittest.TestCase):

    def setUp(self):
        self.ex_cnr = cnvlib.read('formats/reference-tr.cnn')

    def test_empty(self):
        """Instantiate from an empty file."""
        garr = gary.GenomicArray.read("formats/empty")
        self.assertEqual(len(garr), 0)

    def test_iter(self):
        """Test iteration."""
        rows = iter(self.ex_cnr)
        firstrow = next(rows)
        self.assertEqual(tuple(firstrow), tuple(self.ex_cnr[0]))
        i = 0
        for i, _row in enumerate(rows):
            pass
        self.assertEqual(i + 2, len(self.ex_cnr))

    def test_copy(self):
        """Test creation of an independent copy of the object."""
        dupe = self.ex_cnr.copy()
        self.assertEqual(tuple(self.ex_cnr[3]), tuple(dupe[3]))
        self.ex_cnr[3, 'log2'] = -10.0
        self.assertNotEqual(tuple(self.ex_cnr[3]), tuple(dupe[3]))

    def test_autosomes(self):
        """Test selection of autosomes."""
        len_all = len(self.ex_cnr)
        len_x = (self.ex_cnr.chromosome == 'chrX').sum()
        len_y = (self.ex_cnr.chromosome == 'chrY').sum()
        auto = self.ex_cnr.autosomes()
        self.assertEqual(len(auto), len_all - len_x - len_y)
        autox = self.ex_cnr.autosomes(also='chrX')
        self.assertEqual(len(autox), len_all - len_y)
        autoy = self.ex_cnr.autosomes(also=['chrY'])
        self.assertEqual(len(autoy), len_all - len_x)
        autoxy = self.ex_cnr.autosomes(also=['chrX', 'chrY'])
        self.assertEqual(len(autoxy), len_all)

    def test_by_chromosome(self):
        for fname in ("formats/amplicon.cnr", "formats/cl_seq.cns"):
            cnarr = cnvlib.read(fname)
            row_count = 0
            for _chrom, rows in cnarr.by_chromosome():
                row_count += len(rows)
            self.assertEqual(row_count, len(cnarr))

    # def test_concat(self):

    def test_ranges(self):
        """Test range methods: by_ranges, in_range, in_ranges."""
        cnarr = cnvlib.read("formats/amplicon.cnr")
        segarr = cnvlib.read("formats/amplicon.cns")
        chrom_segarr = dict(segarr.by_chromosome())
        for chrom, subarr in cnarr.by_chromosome():
            count_segs = 0
            count_bins = 0
            subsegarr = chrom_segarr[chrom]
            for count_segs, (seg, bins) in enumerate(subarr.by_ranges(subsegarr)):
                count_bins += len(bins)
                self.assertEqual(seg.probes, len(bins))
                self.assertEqual(len(bins), len(
                    cnarr.in_range(seg.chromosome, seg.start, seg.end,
                                   mode='outer')))
                self.assertEqual(len(bins), len(
                    cnarr.in_range(seg.chromosome, seg.start, seg.end,
                                   mode='trim')))
            self.assertEqual(len(subsegarr), count_segs + 1)
            self.assertEqual(len(subarr), count_bins)
            self.assertEqual(len(subarr), len(
                cnarr.in_ranges(chrom, subsegarr['start'], subsegarr['end'],
                                mode="outer")))
            self.assertEqual(len(subarr), len(
                subarr.in_ranges(starts=subsegarr['start'],
                                 ends=subsegarr['end'], mode="outer")))
            self.assertEqual(len(subarr), len(
                cnarr.in_ranges(chrom, subsegarr['start'], subsegarr['end'],
                                mode="trim")))
            self.assertEqual(len(subarr), len(
                subarr.in_ranges(starts=subsegarr['start'],
                                 ends=subsegarr['end'], mode="trim")))

    def test_select(self):
        """Test sugary selection of a subset of the data array."""
        num_bg_rows = len(self.ex_cnr[self.ex_cnr['gene'] == 'Background'])
        self.assertEqual(len(self.ex_cnr.select(gene='Background')),
                         num_bg_rows)
        selector = lambda row: row['gene'] == 'Background'
        self.assertEqual(len(self.ex_cnr.select(selector)), num_bg_rows)

    def test_shuffle_sort(self):
        """Test shuffling and re-sorting the data array."""
        orig_cvg = tuple(self.ex_cnr['log2'][:10])
        self.assertEqual(tuple(self.ex_cnr['log2'][:10]), orig_cvg)
        self.ex_cnr.shuffle()
        self.assertNotEqual(tuple(self.ex_cnr['log2'][:10]), orig_cvg)
        self.ex_cnr.sort()
        self.assertEqual(tuple(self.ex_cnr['log2'][:10]), orig_cvg)



class CNATests(unittest.TestCase):
    """Tests for the CopyNumArray class."""

    def setUp(self):
        self.ex_cnr = cnvlib.read('formats/reference-tr.cnn')

    def test_empty(self):
        """Instantiate from an empty file."""
        cnarr = cnvlib.read("formats/empty")
        self.assertEqual(len(cnarr), 0)

    def test_basic(self):
        """Test basic container functionality and magic methods."""
        # Length
        self.assertEqual(len(self.ex_cnr), 27526)
        # Equality
        same = cnvlib.read('formats/reference-tr.cnn')
        self.assertEqual(self.ex_cnr, same)
        # Item access
        orig = self.ex_cnr[0]
        self.ex_cnr[0] = orig
        self.ex_cnr[3:4] = self.ex_cnr[3:4]
        self.ex_cnr[6:10] = self.ex_cnr[6:10]
        self.assertEqual(tuple(self.ex_cnr[0]), tuple(same[0]))
        self.assertEqual(self.ex_cnr[3:6], same[3:6])

    # def test_by_gene(self):

    def test_center_all(self):
        """Test recentering."""
        # Median-centering an already median-centered array -> no change
        chr1 = self.ex_cnr.in_range('chr1')
        self.assertAlmostEqual(0, np.median(chr1['log2']), places=1)
        chr1.center_all()
        orig_chr1_cvg = np.median(chr1['log2'])
        self.assertAlmostEqual(0, orig_chr1_cvg)
        # Median-centering resets a shift away from the median
        chr1plus2 = chr1.copy()
        chr1plus2['log2'] += 2.0
        chr1plus2.center_all()
        self.assertAlmostEqual(np.median(chr1plus2['log2']), orig_chr1_cvg)
        # Other methods for centering are similar for a CN-neutral chromosome
        for method in ("mean", "mode", "biweight"):
            cp = chr1.copy()
            cp.center_all(method)
            self.assertLess(abs(cp['log2'].median() - orig_chr1_cvg), 0.1)

    def test_drop_extra_columns(self):
        """Test removal of optional 'gc' column."""
        self.assertIn('gc', self.ex_cnr)
        cleaned = self.ex_cnr.drop_extra_columns()
        self.assertNotIn('gc', cleaned)
        self.assertTrue((cleaned['log2'] == self.ex_cnr['log2']).all())

    def test_gender(self):
        """Guess chromosomal gender from chrX log2 ratio value."""
        for (fname, sample_is_f, ref_is_m) in (
                ("formats/f-on-f.cns", True, False),
                ("formats/f-on-m.cns", True, True),
                ("formats/m-on-f.cns", False, False),
                ("formats/m-on-m.cns", False, True),
                ("formats/amplicon.cnr", False, True),
                ("formats/cl_seq.cns", True, True),
                ("formats/tr95t.cns", True, True),
                ("formats/reference-tr.cnn", False, False),
            ):
            cnarr = cnvlib.read(fname)
            if sample_is_f != cnarr.guess_xx(ref_is_m):
                print("Gender issue:", fname, sample_is_f, ref_is_m)
            self.assertEqual(sample_is_f, cnarr.guess_xx(ref_is_m))

    def test_residuals(self):
        cnarr = cnvlib.read("formats/amplicon.cnr")
        segments = cnvlib.read("formats/amplicon.cns")
        regions = rary.RegionArray(segments.data).drop_extra_columns()
        for arg in (None, segments, regions):
            resid = cnarr.residuals(arg)
            self.assertAlmostEqual(0, resid.mean(), delta=.3)
            self.assertAlmostEqual(1, np.percentile(resid, 80), delta=.2)
            self.assertAlmostEqual(2, resid.std(), delta=.5)

    # def test_squash_genes(self):



class RATests(unittest.TestCase):
    """Tests for RegionArray class."""

    def test_empty(self):
        """Instantiate from an empty file."""
        regions = rary.RegionArray.read("formats/empty")
        self.assertEqual(len(regions), 0)

    def test_read_bed(self):
        """Read the BED format."""
        regions = rary.RegionArray.read("formats/amplicon.bed")
        self.assertEqual(len(regions), 1433)

    def test_read_text(self):
        """Read the text region format."""
        regions = rary.RegionArray.read("formats/amplicon.text")
        self.assertEqual(len(regions), 1433)

    def test_read_ilist(self):
        """Read the interval list format."""
        regions = rary.RegionArray.read("formats/nv2_baits.interval_list")
        self.assertEqual(len(regions), 6809)



class ImporterTests(unittest.TestCase):
    """Tests for importers functionality."""

    def test_import_picard(self):
        """Test loading a Picard targetcoverage file."""
        fname = 'picard/p2-5_5.antitargetcoverage.csv'
        cna = importers.import_picard_pertargetcoverage(fname)
        self.assertGreater(len(cna), 1)

    def test_import_seg(self):
        """Test loading SEG format."""
        for fname, args in (
            # cnvkit.py import-seg cw-tr-log2.seg -p chr -c human -d tmp
            ('formats/cw-tr-log2.seg', ({'23': 'X', '24': 'Y', '25': 'M'}, "chr", False)),
            # cnvkit.py import-seg --from-log10 acgh-log10.seg -d tmp/
            ('formats/acgh-log10.seg', (None, None, True))):
            expect_lines = linecount(fname) - 1
            seen_lines = 0
            for cns in importers.import_seg(fname, *args):
                seen_lines += len(cns)
            self.assertEqual(seen_lines, expect_lines)



class CommandTests(unittest.TestCase):
    """Tests for top-level commands."""

    def test_antitarget(self):
        """The 'antitarget' command."""
        baits_fname = "formats/nv2_baits.interval_list"
        access_fname = "../data/access-5k-mappable.hg19.bed"
        self.assertLess(0, len(commands.do_antitarget(baits_fname)))
        self.assertLess(0, len(
            commands.do_antitarget(baits_fname, access_fname)))
        self.assertLess(0, len(
            commands.do_antitarget(baits_fname, access_fname, 200000)))
        self.assertLess(0, len(
            commands.do_antitarget(baits_fname, access_fname, 10000, 5000)))

    def test_breaks(self):
        """The 'breaks' command."""
        probes = cnvlib.read("formats/amplicon.cnr")
        segs = cnvlib.read("formats/amplicon.cns")
        rows = commands.do_breaks(probes, segs, 4)
        self.assertGreater(len(rows), 0)

    def test_call(self):
        """The 'call' command."""
        # Methods: clonal, threshold, none
        tr_cns = cnvlib.read("formats/tr95t.cns")
        tr_thresh = commands.do_call(tr_cns, None, "threshold",
                            is_reference_male=True, is_sample_female=True)
        self.assertEqual(len(tr_cns), len(tr_thresh))
        tr_clonal = commands.do_call(tr_cns, None, "clonal",
                            purity=.65,
                            is_reference_male=True, is_sample_female=True)
        self.assertEqual(len(tr_cns), len(tr_clonal))
        cl_cns = cnvlib.read("formats/cl_seq.cns")
        cl_thresh = commands.do_call(cl_cns, None, "threshold",
                            thresholds=np.log2((np.arange(12) + .5) / 6.),
                            is_reference_male=True, is_sample_female=True)
        self.assertEqual(len(cl_cns), len(cl_thresh))
        cl_clonal = commands.do_call(cl_cns, None, "clonal",
                            ploidy=6, purity=.99,
                            is_reference_male=True, is_sample_female=True)
        self.assertEqual(len(cl_cns), len(cl_clonal))
        cl_none = commands.do_call(cl_cns, None, "none",
                            ploidy=6, purity=.99,
                            is_reference_male=True, is_sample_female=True)
        self.assertEqual(len(cl_cns), len(cl_none))

    def test_call_gender(self):
        """Test each 'call' method on allosomes."""
        for (fname, sample_is_f, ref_is_m,
             chr1_expect, chrx_expect, chry_expect,
             chr1_cn, chrx_cn, chry_cn,
            ) in (
                ("formats/f-on-f.cns", True, False, 0, 0, None, 2, 2, None),
                ("formats/f-on-m.cns", True, True, 0.585, 1, None, 3, 2, None),
                ("formats/m-on-f.cns", False, False, 0, -1, 0, 2, 1, 1),
                ("formats/m-on-m.cns", False, True, 0, 0, 0, 2, 1, 1),
            ):
            cns = cnvlib.read(fname)
            chr1_idx = (cns.chromosome == 'chr1')
            chrx_idx = (cns.chromosome == 'chrX')
            chry_idx = (cns.chromosome == 'chrY')
            def test_chrom_means(segments):
                self.assertEqual(chr1_cn, segments['cn'][chr1_idx].mean())
                self.assertAlmostEqual(chr1_expect,
                                       segments['log2'][chr1_idx].mean(), 0)
                self.assertEqual(chrx_cn, segments['cn'][chrx_idx].mean())
                self.assertAlmostEqual(chrx_expect,
                                       segments['log2'][chrx_idx].mean(), 0)
                if not sample_is_f:
                    self.assertEqual(chry_cn, segments['cn'][chry_idx].mean())
                    self.assertAlmostEqual(chry_expect,
                                           segments['log2'][chry_idx].mean(), 0)

            # Call threshold
            cns_thresh = commands.do_call(cns, None, "threshold",
                                 is_reference_male=ref_is_m,
                                 is_sample_female=sample_is_f)
            test_chrom_means(cns_thresh)
            # Call clonal pure
            cns_clone = commands.do_call(cns, None, "clonal",
                                is_reference_male=ref_is_m,
                                is_sample_female=sample_is_f)
            test_chrom_means(cns_clone)
            # Call clonal barely-mixed
            cns_p99 = commands.do_call(cns, None, "clonal", purity=0.99,
                              is_reference_male=ref_is_m,
                              is_sample_female=sample_is_f)
            test_chrom_means(cns_p99)

    def test_export(self):
        """Run the 'export' command with each format."""
        # SEG
        seg_rows = export.export_seg(["formats/tr95t.cns"])
        self.assertGreater(len(seg_rows), 0)
        seg2_rows = export.export_seg(["formats/tr95t.cns",
                                       "formats/cl_seq.cns"])
        self.assertGreater(len(seg2_rows), len(seg_rows))
        # THetA2
        _header, theta_rows = export.export_theta("formats/tr95t.cns",
                                                  "formats/reference-tr.cnn")
        self.assertGreater(len(theta_rows), 0)
        for fname, ploidy, is_f in [("tr95t.cns", 2, True),
                                    ("cl_seq.cns", 6, True),
                                    ("amplicon.cns", 2, False)]:
            cns = cnvlib.read("formats/" + fname)
            # BED
            self.assertLess(len(export.export_bed(cns, ploidy, True, is_f,
                                                  cns.sample_id, "ploidy")),
                            len(cns))
            self.assertLess(len(export.export_bed(cns, ploidy, True, is_f,
                                                  cns.sample_id, "variant")),
                            len(cns))
            self.assertEqual(len(export.export_bed(cns, ploidy, True, is_f,
                                                   cns.sample_id, "all")),
                             len(cns))
            # VCF
            _vheader, vcf_body = export.export_vcf(cns, ploidy, True, is_f)
            self.assertTrue(0 < len(vcf_body.splitlines()) < len(cns))

    def test_fix(self):
        """The 'fix' command."""
        # Extract fake target/antitarget bins from a combined file
        ref = cnvlib.read('formats/reference-tr.cnn')
        is_bg = (ref["gene"] == "Background")
        tgt_bins = ref[~is_bg]
        tgt_bins.log2 += np.random.randn(len(tgt_bins)) / 5
        anti_bins = ref[is_bg]
        anti_bins.log2 += np.random.randn(len(anti_bins)) / 5
        blank_bins = cnary.CopyNumArray([])
        # Typical usage (hybrid capture)
        cnr = commands.do_fix(tgt_bins, anti_bins, ref)
        self.assertTrue(0 < len(cnr) <= len(ref))
        # Blank antitargets (WGS or amplicon)
        cnr = commands.do_fix(tgt_bins, blank_bins, ref[~is_bg])
        self.assertTrue(0 < len(cnr) <= len(tgt_bins))

    def test_gainloss(self):
        """The 'gainloss' command."""
        probes = cnvlib.read("formats/amplicon.cnr")
        rows = commands.do_gainloss(probes, male_reference=True)
        self.assertGreater(len(rows), 0)
        segs = cnvlib.read("formats/amplicon.cns")
        rows = commands.do_gainloss(probes, segs, True, 0.3, 4)
        self.assertGreater(len(rows), 0)

    def test_import_theta(self):
        """The 'import-theta' command."""
        cns = cnvlib.read("formats/nv3.cns")
        theta_fname = "formats/nv3.n2.results"
        for new_cns in commands.do_import_theta(cns, theta_fname):
            self.assertTrue(0 < len(new_cns) <= len(cns))

    def test_metrics(self):
        """The 'metrics' command."""
        cnarr = cnvlib.read("formats/amplicon.cnr")
        segments = cnvlib.read("formats/amplicon.cns")
        resids = cnarr.residuals(segments)
        self.assertLessEqual(len(resids), len(cnarr))
        values = metrics.ests_of_scale(resids)
        for val in values:
            self.assertGreater(val, 0)

    def test_reference(self):
        """The 'reference' command."""
        # Empty antitargets
        ref = commands.do_reference(["formats/amplicon.cnr"], ["formats/empty"])
        self.assertGreater(len(ref), 0)
        # Empty antitargets, flat reference
        ref = commands.do_reference_flat("formats/amplicon.bed",
                                         "formats/empty")
        self.assertGreater(len(ref), 0)

    def test_segment(self):
        """The 'segment' command."""
        cnarr = cnvlib.read("formats/amplicon.cnr")
        # R methods are in another script
        segments = segmentation.do_segmentation(cnarr, "haar")
        self.assertGreater(len(segments), 0)
        segments = segmentation.do_segmentation(cnarr, "haar", threshold=.001,
                                                skip_low=True)
        self.assertGreater(len(segments), 0)

    def test_segmetrics(self):
        """The 'segmetrics' command."""
        cnarr = cnvlib.read("formats/amplicon.cnr")
        segarr = cnvlib.read("formats/amplicon.cns")
        for func in (
            lambda x: metrics.confidence_interval_bootstrap(x, 0.05, 100),
            lambda x: metrics.prediction_interval(x, 0.05),
        ):
            lo, hi = commands._segmetric_interval(segarr, cnarr, func)
            self.assertEqual(len(lo), len(segarr))
            self.assertEqual(len(hi), len(segarr))
            sensible_segs_mask = (np.asarray(segarr['probes']) > 3)
            means = segarr[sensible_segs_mask, 'log2']
            los = lo[sensible_segs_mask]
            his = hi[sensible_segs_mask]
            self.assertTrue((los < means).all())
            self.assertTrue((means < his).all())

    def test_target(self):
        """The 'target' command."""
        # ENH: annotate w/ mini-refFlat
        r = commands.do_targets("formats/nv2_baits.interval_list")
        self.assertGreater(len(r), 0)
        r = commands.do_targets("formats/amplicon.bed", do_short_names=True,
                                do_split=True, avg_size=100)
        self.assertGreater(len(r), 0)



class OtherTests(unittest.TestCase):
    """Tests for other functionality."""

    def test_fix_edge(self):
        """Test the 'edge' bias correction calculations."""
        # With no gap, gain and loss should balance out
        # 1. Wide target, no secondary corrections triggered
        insert_size = 250
        gap_size = np.zeros(1)  # Adjacent
        target_size = np.asarray([600])
        loss = fix.edge_losses(target_size, insert_size)
        gain = fix.edge_gains(target_size, gap_size, insert_size)
        gain *= 2  # Same on the other side
        self.assertAlmostEqual(loss, gain)
        # 2. Trigger 'loss' correction (target_size < 2 * insert_size)
        target_size = np.asarray([450])
        self.assertAlmostEqual(fix.edge_losses(target_size, insert_size),
                        2 * fix.edge_gains(target_size, gap_size, insert_size))
        # 3. Trigger 'gain' correction (target_size + gap_size < insert_size)
        target_size = np.asarray([300])
        self.assertAlmostEqual(fix.edge_losses(target_size, insert_size),
                        2 * fix.edge_gains(target_size, gap_size, insert_size))

    # call
    # Test: convert_clonal(x, 1, 2) == convert_diploid(x)


# == helpers ==

def linecount(filename):
    i = 0
    with open(filename) as handle:
        for i, _line in enumerate(handle):
            pass
        return i + 1


if __name__ == '__main__':
    unittest.main(verbosity=2)
