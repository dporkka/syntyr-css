"""The CSS contract's raw hashes are reproducible even when zlib is not."""
from copy import deepcopy
import unittest

from scripts import build


class CSSContractPortabilityTests(unittest.TestCase):
    def test_gzip_measurements_are_informational_across_zlib_versions(self):
        expected = build.css_contract()
        from_other_zlib = deepcopy(expected)
        for preset in from_other_zlib["presets"].values():
            preset["gzip_bytes"] = max(1, preset["gzip_bytes"] - 25)
        self.assertTrue(build.css_contract_matches(expected, from_other_zlib))

    def test_source_checksum_and_raw_size_remain_exact(self):
        expected = build.css_contract()
        corrupt = deepcopy(expected)
        corrupt["presets"]["minimal"]["sha256"] = "0" * 64
        self.assertFalse(build.css_contract_matches(expected, corrupt))
        corrupt = deepcopy(expected)
        corrupt["presets"]["cinematic"]["raw_bytes"] += 1
        self.assertFalse(build.css_contract_matches(expected, corrupt))

    def test_missing_or_implausible_gzip_measurement_is_rejected(self):
        expected = build.css_contract()
        invalid = deepcopy(expected)
        del invalid["presets"]["saas"]["gzip_bytes"]
        self.assertFalse(build.css_contract_matches(expected, invalid))
        invalid = deepcopy(expected)
        invalid["presets"]["saas"]["gzip_bytes"] = invalid["presets"]["saas"]["raw_bytes"] + 1
        self.assertFalse(build.css_contract_matches(expected, invalid))
