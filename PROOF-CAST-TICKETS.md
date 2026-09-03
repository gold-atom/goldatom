# GoldAtom/1 Research Note: Proof-Cast Tickets

**Status:** non-normative design branch  
**Date:** 2026-09-02  
**Purpose:** convert freely multiplied identities into costly, pre-draw extraction chances without allowing additional work to manufacture additional ore.

## 1. The problem

A claimant-dependent rarity gate is not scarce when a claimant can cheaply vary keys, salts, transaction identifiers, or other inputs. If one trial succeeds with probability `p`, then `n` cheap variants succeed with probability:

```text
1 - (1 - p)^n
```

At a nominal probability of `1/4096`, 10,000 cheap variants produce at least one success about 91.3% of the time. The apparent rarity disappears.

A Proof-Cast Ticket replaces each cheap variant with an independently valid proof of work. Ten thousand chances then require ten thousand valid work proofs.

## 2. The governing separation

```text
History controls supply.
Work controls allocation.
Bitcoin controls chronology and title.
```

PoW tickets may increase a prospector's chance of receiving an already-open vein. They may never increase the number of veins or the number of atoms issued by one vein.

## 3. Required invariants

1. Claimant-controlled bytes do not influence whether a vein opens.
2. Each ticket carries a publicly verifiable expected production cost.
3. Each ticket is fixed and publicly available before the draw is knowable.
4. Every valid ticket receives one equal draw at the declared ticket difficulty.
5. One open vein settles to at most one GoldAtom title.
6. Additional hashpower changes ownership probability, not maximum issuance.
7. Every winner and fallback winner is deterministically derivable by an independent verifier.

## 4. Epoch outline

```text
PRECLAIM
  claim UTXO and owner/title key become canonical

CAST
  prospectors manufacture PoW tickets bound to the epoch and claim

CLOSE
  the complete ticket set fossilizes before future draw history exists

DRAW
  future Bitcoin blocks derive a claimant-independent randomness value

VEIN
  the same future history decides whether this epoch contains ore

RANK
  every prior ticket is ranked against the future draw

SETTLE
  the highest-ranked eligible ticket spends its claim into one title UTXO

BURY
  later Bitcoin chainwork deepens the atom's historical assay
```

## 5. Ticket work

A candidate ticket header may commit to:

```text
protocol domain
profile identifier
epoch identifier
cast-start Bitcoin block
claim outpoint
owner/title public key
ticket target
counter
nonce
```

One illustrative digest is:

```text
ticket_id = SHA256d(
  "GoldAtom/ticket/v1" ||
  profile || epoch || cast_start_block ||
  claim_outpoint || owner_key || ticket_target ||
  counter || nonce
)
```

The ticket is valid when its numeric digest is at or below `ticket_target`.

The verifier does not claim to know the literal electricity consumed. It verifies a statistically rare result with a declared expected work value.

## 6. Publication and data availability

Tickets must be committed before the draw window. A commitment root is insufficient unless the complete leaf set is also publicly available and fixed before the draw; otherwise a participant can selectively reveal only favorable tickets.

The first prototype should prefer explicit, easy-to-audit ticket publication over premature compression. Later versions may batch tickets using a commitment structure paired with a defined data-availability rule.

## 7. Vein gate

The epoch randomness and vein predicate must exclude every claimant-controlled input:

```text
R_e = Extract(future canonical Bitcoin block interval)
V_e = SHA256d("GoldAtom/vein/v1" || profile || epoch || R_e)
open = uint256(V_e) <= vein_target
```

The exact extractor remains an open research choice. A multi-block construction raises the cost of block withholding but does not eliminate source-miner influence.

## 8. Winner selection

For each valid pre-draw ticket `t_i`:

```text
score_i = SHA256d("GoldAtom/draw/v1" || R_e || ticket_id_i)
```

Sort by:

```text
score ascending,
ticket_id ascending,
claim commitment ascending,
publication transaction id ascending
```

The first eligible ticket is the provisional winner. If it does not settle during its fixed slot, eligibility passes to the next ranked ticket.

With `m` tickets held by one prospector and `N` valid tickets total:

```text
Pr(win | vein opens) = m / N
```

## 9. Supply law

Let the claimant-independent vein gate open with probability `p_v`, and let `N_e` be the number of valid tickets in epoch `e`:

```text
atoms_e = open_e * 1[N_e > 0]
E[atoms_e] = p_v * Pr(N_e > 0) <= p_v
```

Ten tickets and ten billion tickets can alter competition, but an epoch still creates at most one atom.

This is the essential distinction from a design in which every winning ticket independently mints an atom. In that weaker design, expected issuance grows with ticket count and collapses back into ordinary PoW issuance.

## 10. Principal attacks still open

- **Hashpower concentration:** PoW prices chances; it does not create egalitarian distribution.
- **Existing ASIC advantage:** SHA-256d gives incumbent Bitcoin hardware a large advantage.
- **Hidden optimization:** a new work function risks undisclosed hardware or algorithmic asymmetries.
- **Ticket censorship:** Bitcoin miners can exclude ticket transactions during the cast window.
- **Beacon manipulation:** a source miner may withhold a block when GoldAtom value exceeds the sacrificed Bitcoin reward and fees.
- **Data floods:** ticket volume may overwhelm indexers or make complete-set reconstruction expensive.
- **Fee shocks:** high Bitcoin fees may price out small ticket publishers or alter the effective competition set.
- **Settlement griefing:** winners can refuse to settle, requiring fixed fallback slots and bond rules.
- **Reorganizations:** cast, draw, and settlement finality must be chainwork-based and explicitly reversible.
- **Empty open veins:** an open vein with no valid tickets needs a deterministic status: unclaimed, expired, or carried forward.

## 11. First prototype boundary

The next executable prototype should use regtest and deliberately tiny targets. It should prove only that independent implementations derive the same:

1. valid pre-draw ticket set;
2. draw randomness;
3. vein state;
4. ranked winner list;
5. one-vein/one-title settlement;
6. fallback after winner timeout;
7. invalidation and restoration across a reorganization.

It should not introduce a ticker, sale, mainnet profile, or claim of solved monetary scarcity.

## 12. One-sentence formulation

> You cannot hash more gold into existence. You can only hash yourself more chances of discovering the gold that history has already decided exists.


