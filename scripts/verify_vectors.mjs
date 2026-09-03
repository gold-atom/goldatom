#!/usr/bin/env node
/**
 * Independent GoldAtom/0 pure-protocol verifier.
 *
 * This intentionally does not import or execute the Python implementation.
 * It recomputes canonical GoldAtom claim, challenge, local-work, mint, AtomID,
 * and title-transfer commitments using only Node.js built-ins.
 *
 * Scope boundary: a proof bundle does not contain full decoded Bitcoin
 * transactions or an active-chain/UTXO view, so this program does not verify
 * transaction inclusion, marker counts, canonical chain membership, or the
 * terminal title's unspent state. Those checks remain the responsibility of
 * the Core-backed verifier.
 */

import fs from "node:fs";
import crypto from "node:crypto";
import process from "node:process";

const PROFILES = new Map([
  [
    "goldatom-sim-v0",
    {
      id: "goldatom-sim-v0",
      network: "simnet",
      challengeDelay: 3,
      mintWindow: 12,
      maximumTarget: (1n << 252n) - 1n,
    },
  ],
  [
    "goldatom-regtest-v0",
    {
      id: "goldatom-regtest-v0",
      network: "regtest",
      challengeDelay: 3,
      mintWindow: 12,
      maximumTarget: (1n << 252n) - 1n,
    },
  ],
]);

const SUPPORTED_ALGORITHM = "sha256d-80-v0";
const REQUIRED_TOP_LEVEL = new Set([
  "format",
  "version",
  "profile",
  "claim",
  "work",
  "mint",
  "transfers",
]);

class VerificationError extends Error {
  constructor(code, message) {
    super(`${code}: ${message}`);
    this.name = "VerificationError";
    this.code = code;
  }
}

function fail(code, message) {
  throw new VerificationError(code, message);
}

function assertObject(value, name) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    fail("BAD_FORMAT", `${name} must be a JSON object`);
  }
}

function requireExactKeys(object, expected, name) {
  assertObject(object, name);
  const actual = new Set(Object.keys(object));
  for (const key of expected) {
    if (!actual.has(key)) fail("BAD_FORMAT", `${name} is missing field ${key}`);
  }
  for (const key of actual) {
    if (!expected.has(key)) fail("BAD_FORMAT", `${name} has unknown field ${key}`);
  }
}

function requireUInt(value, name, max = 0xffffffff) {
  if (!Number.isSafeInteger(value) || value < 0 || value > max) {
    fail("BAD_INTEGER", `${name} must be an integer in [0, ${max}]`);
  }
  return value;
}

function requireHex(value, byteLength = null, name = "hex") {
  if (typeof value !== "string" || !/^(?:[0-9a-f]{2})*$/.test(value)) {
    fail("BAD_HEX", `${name} must be canonical lowercase even-length hexadecimal`);
  }
  const bytes = Buffer.from(value, "hex");
  if (byteLength !== null && bytes.length !== byteLength) {
    fail("BAD_LENGTH", `${name} must be exactly ${byteLength} bytes`);
  }
  return bytes;
}

function u32be(value) {
  const out = Buffer.alloc(4);
  out.writeUInt32BE(requireUInt(value, "u32"));
  return out;
}

function u32le(value) {
  const out = Buffer.alloc(4);
  out.writeUInt32LE(requireUInt(value, "u32"));
  return out;
}

function varbytes(value) {
  return Buffer.concat([u32be(value.length), value]);
}

function varstr(value) {
  if (typeof value !== "string") fail("BAD_STRING", "value must be a string");
  return varbytes(Buffer.from(value, "utf8"));
}

function sha256(value) {
  return crypto.createHash("sha256").update(value).digest();
}

function sha256d(value) {
  return sha256(sha256(value));
}

function taggedHash(tag, message) {
  const tagHash = sha256(Buffer.from(tag, "utf8"));
  return sha256(Buffer.concat([tagHash, tagHash, message]));
}

function encodeOutpoint(outpoint) {
  requireExactKeys(outpoint, new Set(["txid", "vout"]), "outpoint");
  return Buffer.concat([
    requireHex(outpoint.txid, 32, "outpoint txid"),
    u32be(requireUInt(outpoint.vout, "outpoint vout")),
  ]);
}

function claimCommitment(profile, claim) {
  if (claim.algorithm !== SUPPORTED_ALGORITHM) {
    fail("BAD_ALGORITHM", `unsupported algorithm ${String(claim.algorithm)}`);
  }
  const message = Buffer.concat([
    varstr(profile.id),
    varstr(profile.network),
    u32be(requireUInt(claim.outpoint.vout, "claim seal vout")),
    varbytes(requireHex(claim.seal_script_hex, null, "claim seal script")),
    varstr(claim.algorithm),
    requireHex(claim.target_hex, 32, "target"),
    u32be(profile.challengeDelay),
    u32be(profile.mintWindow),
  ]);
  return taggedHash("GoldAtom/claim/v0", message);
}

function challengeDigest(profile, claim, claimDigest, work) {
  const message = Buffer.concat([
    varstr(profile.id),
    encodeOutpoint(claim.outpoint),
    requireHex(claim.block_hash, 32, "claim block hash"),
    claimDigest,
    requireHex(work.challenge_block_hash, 32, "challenge block hash"),
  ]);
  return taggedHash("GoldAtom/challenge/v0", message);
}

function workHeader(challenge, claimDigest, extraNonce, nonce) {
  const header = Buffer.concat([
    Buffer.from("GAW0", "ascii"),
    challenge,
    claimDigest,
    u32le(extraNonce),
    Buffer.alloc(4),
    u32le(nonce),
  ]);
  if (header.length !== 80) fail("INTERNAL", "work header is not 80 bytes");
  return header;
}

function mintCommitment(profile, claim, challenge, workHash, work, mint) {
  const message = Buffer.concat([
    varstr(profile.id),
    encodeOutpoint(claim.outpoint),
    challenge,
    u32be(requireUInt(work.extra_nonce, "extra_nonce")),
    u32be(requireUInt(work.nonce, "nonce")),
    workHash,
    u32be(requireUInt(mint.title_vout, "title_vout")),
    varbytes(requireHex(mint.title_script_hex, null, "title script")),
  ]);
  return taggedHash("GoldAtom/mint/v0", message);
}

function atomId(mint, mintDigest) {
  const message = Buffer.concat([
    requireHex(mint.txid, 32, "mint txid"),
    u32be(requireUInt(mint.title_vout, "title_vout")),
    mintDigest,
  ]);
  return taggedHash("GoldAtom/id/v0", message);
}

function transferCommitment(profile, atomDigest, transition, previousOutpoint) {
  const message = Buffer.concat([
    varstr(profile.id),
    atomDigest,
    u32be(requireUInt(transition.index, "transfer index")),
    encodeOutpoint(previousOutpoint),
    u32be(requireUInt(transition.successor_vout, "successor_vout")),
    varbytes(requireHex(transition.successor_script_hex, null, "successor script")),
  ]);
  return taggedHash("GoldAtom/transfer/v0", message);
}

function equalHex(actual, expectedHex, code, label) {
  const expected = requireHex(expectedHex, 32, label);
  if (!crypto.timingSafeEqual(actual, expected)) {
    fail(code, `${label} does not recompute`);
  }
}

function bufferToBigInt(buffer) {
  return BigInt(`0x${buffer.toString("hex")}`);
}

function expectedHashes(target) {
  const denominator = target + 1n;
  return ((1n << 256n) + denominator - 1n) / denominator;
}

function validateShape(bundle) {
  requireExactKeys(bundle, REQUIRED_TOP_LEVEL, "bundle");
  if (bundle.format !== "goldatom-proof") fail("BAD_FORMAT", "unsupported format");
  if (bundle.version !== 0) fail("BAD_VERSION", "unsupported version");
  requireExactKeys(
    bundle.claim,
    new Set([
      "outpoint",
      "block_hash",
      "height",
      "seal_script_hex",
      "algorithm",
      "target_hex",
      "commitment_hex",
      "txout_proof",
    ]),
    "claim",
  );
  requireExactKeys(
    bundle.work,
    new Set([
      "challenge_height",
      "challenge_block_hash",
      "challenge_digest_hex",
      "extra_nonce",
      "nonce",
      "work_hash_hex",
    ]),
    "work",
  );
  requireExactKeys(
    bundle.mint,
    new Set([
      "txid",
      "block_hash",
      "height",
      "txout_proof",
      "title_vout",
      "title_script_hex",
      "commitment_hex",
    ]),
    "mint",
  );
  if (!Array.isArray(bundle.transfers)) fail("BAD_FORMAT", "transfers must be an array");
  for (const [index, transition] of bundle.transfers.entries()) {
    requireExactKeys(
      transition,
      new Set([
        "index",
        "previous_outpoint",
        "txid",
        "block_hash",
        "height",
        "txout_proof",
        "successor_vout",
        "successor_script_hex",
        "commitment_hex",
      ]),
      `transfer ${index}`,
    );
  }
}

function verifyBundle(bundle, source = "<memory>") {
  validateShape(bundle);
  const profile = PROFILES.get(bundle.profile);
  if (!profile) fail("BAD_PROFILE", `unknown profile ${String(bundle.profile)}`);

  const claim = bundle.claim;
  const work = bundle.work;
  const mint = bundle.mint;
  requireUInt(claim.height, "claim height");
  requireUInt(work.challenge_height, "challenge height");
  requireUInt(mint.height, "mint height");
  requireHex(claim.block_hash, 32, "claim block hash");
  requireHex(work.challenge_block_hash, 32, "challenge block hash");
  requireHex(mint.block_hash, 32, "mint block hash");
  requireHex(claim.txout_proof, null, "claim txout proof");
  requireHex(mint.txout_proof, null, "mint txout proof");

  const targetBytes = requireHex(claim.target_hex, 32, "target");
  const target = bufferToBigInt(targetBytes);
  if (target > profile.maximumTarget) {
    fail("TARGET_TOO_EASY", "target exceeds profile maximum");
  }

  const claimDigest = claimCommitment(profile, claim);
  equalHex(claimDigest, claim.commitment_hex, "BAD_CLAIM_COMMITMENT", "claim commitment");

  const expectedChallengeHeight = claim.height + profile.challengeDelay;
  if (work.challenge_height !== expectedChallengeHeight) {
    fail("BAD_CHALLENGE_HEIGHT", "challenge height is not claim height plus delay");
  }
  const challenge = challengeDigest(profile, claim, claimDigest, work);
  equalHex(challenge, work.challenge_digest_hex, "BAD_CHALLENGE", "challenge digest");

  const header = workHeader(
    challenge,
    claimDigest,
    requireUInt(work.extra_nonce, "extra_nonce"),
    requireUInt(work.nonce, "nonce"),
  );
  const workHash = sha256d(header);
  equalHex(workHash, work.work_hash_hex, "BAD_WORK_HASH", "work hash");
  if (bufferToBigInt(workHash) > target) {
    fail("INSUFFICIENT_WORK", "work hash is above target");
  }

  if (
    mint.height < work.challenge_height + 1 ||
    mint.height > work.challenge_height + profile.mintWindow
  ) {
    fail("MINT_OUTSIDE_WINDOW", "mint height is outside the profile window");
  }
  const mintDigest = mintCommitment(profile, claim, challenge, workHash, work, mint);
  equalHex(mintDigest, mint.commitment_hex, "BAD_MINT_COMMITMENT", "mint commitment");
  const atomDigest = atomId(mint, mintDigest);

  let previousOutpoint = { txid: mint.txid, vout: mint.title_vout };
  for (const [index, transition] of bundle.transfers.entries()) {
    if (transition.index !== index) {
      fail("TRANSFER_INDEX", "title transfer indices must be contiguous from zero");
    }
    if (
      transition.previous_outpoint.txid !== previousOutpoint.txid ||
      transition.previous_outpoint.vout !== previousOutpoint.vout
    ) {
      fail("BROKEN_TITLE_CHAIN", "transfer does not name the preceding title outpoint");
    }
    const digest = transferCommitment(profile, atomDigest, transition, previousOutpoint);
    equalHex(digest, transition.commitment_hex, "BAD_TRANSFER_COMMITMENT", "transfer commitment");
    previousOutpoint = {
      txid: transition.txid,
      vout: transition.successor_vout,
    };
  }

  return {
    valid: true,
    scope: "pure-protocol commitments only; Bitcoin consensus state not checked",
    source,
    profile: profile.id,
    atom_id: atomDigest.toString("hex"),
    claim_commitment: claimDigest.toString("hex"),
    challenge_digest: challenge.toString("hex"),
    work_header_hex: header.toString("hex"),
    work_hash: workHash.toString("hex"),
    expected_local_hashes: expectedHashes(target).toString(),
    mint_commitment: mintDigest.toString("hex"),
    title_transfers: bundle.transfers.length,
    terminal_title_outpoint: previousOutpoint,
  };
}

function usage() {
  console.error("usage: node scripts/verify_vectors.mjs <bundle.json> [bundle.json ...]");
}

const paths = process.argv.slice(2);
if (paths.length === 0) {
  usage();
  process.exit(64);
}

try {
  const reports = paths.map((path) => {
    const text = fs.readFileSync(path, "utf8");
    const bundle = JSON.parse(text);
    return verifyBundle(bundle, path);
  });
  process.stdout.write(`${JSON.stringify(paths.length === 1 ? reports[0] : reports, null, 2)}\n`);
} catch (error) {
  if (error instanceof VerificationError) {
    console.error(`INVALID: ${error.message}`);
    process.exit(2);
  }
  console.error(`ERROR: ${error?.stack ?? String(error)}`);
  process.exit(1);
}
