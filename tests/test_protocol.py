from __future__ import annotations

import unittest
from dataclasses import replace

from goldatom.demo import build_simulated_fixture
from goldatom.encoding import EncodingError, marker_script, require_hex
from goldatom.models import GoldAtomBundle, Outpoint
from goldatom.profiles import get_profile
from goldatom.protocol import build_work_header, calculate_work_hash
from goldatom.verify import VerificationError, verify_bundle
from goldatom.view import BitcoinTransaction, TxOutput, UTXO


class GoldAtomProtocolTests(unittest.TestCase):
    def assert_verification_code(self, expected_code: str, bundle, view) -> None:
        with self.assertRaises(VerificationError) as caught:
            verify_bundle(bundle, view)
        self.assertEqual(expected_code, caught.exception.code)

    def test_genesis_vector_is_valid(self) -> None:
        fixture = build_simulated_fixture()
        report = verify_bundle(fixture.bundle, fixture.view)
        self.assertEqual(
            "164b8c2fd964c6a5deed2f16264bedfe2e20ee777c677c250d3f0673a5957417",
            report.atom_id,
        )
        self.assertEqual(16, report.expected_local_hashes)
        self.assertEqual(1, report.burial_blocks)

    def test_eighty_byte_work_header_and_vector(self) -> None:
        fixture = build_simulated_fixture()
        bundle = fixture.bundle
        header = build_work_header(
            challenge_digest=bytes.fromhex(bundle.work.challenge_digest_hex),
            claim_commitment_digest=bytes.fromhex(bundle.claim.commitment_hex),
            extra_nonce=bundle.work.extra_nonce,
            nonce=bundle.work.nonce,
        )
        self.assertEqual(80, len(header))
        self.assertEqual(
            bundle.work.work_hash_hex,
            calculate_work_hash(
                challenge_digest=bytes.fromhex(bundle.work.challenge_digest_hex),
                claim_commitment_digest=bytes.fromhex(bundle.claim.commitment_hex),
                extra_nonce=bundle.work.extra_nonce,
                nonce=bundle.work.nonce,
            ).hex(),
        )

    def test_valid_title_transfer(self) -> None:
        fixture = build_simulated_fixture(with_transfer=True)
        report = verify_bundle(fixture.bundle, fixture.view)
        self.assertEqual(1, report.title_transfers)
        self.assertEqual(fixture.bundle.transfers[0].txid, report.current_title_outpoint.txid)

    def test_tampered_work_hash_is_rejected(self) -> None:
        fixture = build_simulated_fixture()
        bad_work = replace(fixture.bundle.work, work_hash_hex="00" * 32)
        bad_bundle = replace(fixture.bundle, work=bad_work)
        self.assert_verification_code("BAD_WORK_HASH", bad_bundle, fixture.view)

    def test_tampered_nonce_is_rejected(self) -> None:
        fixture = build_simulated_fixture()
        bad_work = replace(fixture.bundle.work, nonce=fixture.bundle.work.nonce + 1)
        bad_bundle = replace(fixture.bundle, work=bad_work)
        self.assert_verification_code("BAD_WORK_HASH", bad_bundle, fixture.view)

    def test_challenge_reorg_is_rejected(self) -> None:
        fixture = build_simulated_fixture()
        fixture.view.replace_header(fixture.bundle.work.challenge_height, "ab" * 32)
        self.assert_verification_code("HEADER_LOOKUP", fixture.bundle, fixture.view)

    def test_target_above_profile_maximum_is_rejected_first(self) -> None:
        fixture = build_simulated_fixture()
        profile = get_profile(fixture.bundle.profile)
        easier_target = f"{profile.maximum_target + 1:064x}"
        bad_claim = replace(fixture.bundle.claim, target_hex=easier_target)
        bad_bundle = replace(fixture.bundle, claim=bad_claim)
        self.assert_verification_code("TARGET_TOO_EASY", bad_bundle, fixture.view)

    def test_mint_outside_window_is_rejected(self) -> None:
        fixture = build_simulated_fixture()
        profile = get_profile(fixture.bundle.profile)
        bad_height = fixture.bundle.work.challenge_height + profile.mint_window + 1
        bad_mint = replace(fixture.bundle.mint, height=bad_height)
        bad_bundle = replace(fixture.bundle, mint=bad_mint)
        self.assert_verification_code("MINT_OUTSIDE_WINDOW", bad_bundle, fixture.view)

    def test_second_mint_marker_is_rejected(self) -> None:
        fixture = build_simulated_fixture()
        mint = fixture.bundle.mint
        key = (mint.txid, mint.block_hash)
        original = fixture.view.transactions[key]
        duplicate_marker = marker_script("mint", bytes.fromhex(mint.commitment_hex)).hex()
        fixture.view.transactions[key] = BitcoinTransaction(
            txid=original.txid,
            block_hash=original.block_hash,
            height=original.height,
            inputs=original.inputs,
            outputs=original.outputs + (TxOutput(0, duplicate_marker),),
        )
        self.assert_verification_code("MINT_MARKER_COUNT", fixture.bundle, fixture.view)

    def test_missing_current_title_is_rejected(self) -> None:
        fixture = build_simulated_fixture()
        title = Outpoint(fixture.bundle.mint.txid, fixture.bundle.mint.title_vout)
        fixture.view.spend_utxo(title)
        self.assert_verification_code("TITLE_SPENT_OR_MISSING", fixture.bundle, fixture.view)

    def test_broken_transfer_ancestry_is_rejected(self) -> None:
        fixture = build_simulated_fixture(with_transfer=True)
        transition = fixture.bundle.transfers[0]
        bad_transition = replace(
            transition,
            previous_outpoint=Outpoint("12" * 32, transition.previous_outpoint.vout),
        )
        bad_bundle = replace(fixture.bundle, transfers=(bad_transition,))
        self.assert_verification_code("BROKEN_TITLE_CHAIN", bad_bundle, fixture.view)

    def test_claim_proof_cannot_be_relabelled(self) -> None:
        fixture = build_simulated_fixture()
        bad_claim = replace(fixture.bundle.claim, txout_proof="34" * 32)
        bad_bundle = replace(fixture.bundle, claim=bad_claim)
        self.assert_verification_code("BAD_INCLUSION_PROOF", bad_bundle, fixture.view)

    def test_duplicate_json_key_is_rejected(self) -> None:
        fixture = build_simulated_fixture()
        text = fixture.bundle.to_json()
        text = text.replace(
            '"profile": "goldatom-sim-v0",',
            '"profile": "goldatom-sim-v0", "profile": "goldatom-sim-v0",',
            1,
        )
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            GoldAtomBundle.from_json(text)

    def test_noncanonical_hex_whitespace_is_rejected(self) -> None:
        with self.assertRaises(EncodingError):
            require_hex("aa bb", name="test")

    def test_unsupported_title_script_is_rejected(self) -> None:
        fixture = build_simulated_fixture()
        mint = fixture.bundle.mint
        key = (mint.txid, mint.block_hash)
        original = fixture.view.transactions[key]
        bad_script = "51"
        outputs = list(original.outputs)
        outputs[mint.title_vout] = TxOutput(outputs[mint.title_vout].value_sats, bad_script)
        fixture.view.transactions[key] = BitcoinTransaction(
            txid=original.txid,
            block_hash=original.block_hash,
            height=original.height,
            inputs=original.inputs,
            outputs=tuple(outputs),
        )
        bad_bundle = replace(
            fixture.bundle,
            mint=replace(fixture.bundle.mint, title_script_hex=bad_script),
        )
        self.assert_verification_code("UNSUPPORTED_TITLE_SCRIPT", bad_bundle, fixture.view)

    def test_current_title_value_mismatch_is_rejected(self) -> None:
        fixture = build_simulated_fixture()
        title = Outpoint(fixture.bundle.mint.txid, fixture.bundle.mint.title_vout)
        original = fixture.view.utxos[title]
        fixture.view.utxos[title] = UTXO(
            outpoint=title,
            value_sats=original.value_sats + 1,
            script_pubkey_hex=original.script_pubkey_hex,
            confirmations=original.confirmations,
        )
        self.assert_verification_code("CURRENT_TITLE_VALUE", fixture.bundle, fixture.view)

    def test_unconfirmed_current_title_is_rejected(self) -> None:
        fixture = build_simulated_fixture()
        title = Outpoint(fixture.bundle.mint.txid, fixture.bundle.mint.title_vout)
        original = fixture.view.utxos[title]
        fixture.view.utxos[title] = UTXO(
            outpoint=title,
            value_sats=original.value_sats,
            script_pubkey_hex=original.script_pubkey_hex,
            confirmations=0,
        )
        self.assert_verification_code("CURRENT_TITLE_UNCONFIRMED", fixture.bundle, fixture.view)

    def test_nested_record_must_be_json_object(self) -> None:
        fixture = build_simulated_fixture()
        data = fixture.bundle.to_dict()
        data["claim"] = []
        with self.assertRaisesRegex(ValueError, "claim must be a JSON object"):
            GoldAtomBundle.from_dict(data)


if __name__ == "__main__":
    unittest.main()
