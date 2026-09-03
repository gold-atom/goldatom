# Bitcoin raw-record geology: empirical analysis

This analysis covers canonical Bitcoin mainnet headers from genesis through fixed tip 965,246. The measured raw-record ledger contains 30 historical deposits/specimens; the difficulty-normalized comparison contains 8 records. These are historical facts, not GoldAtoms, founder inventory, ownership assignments, or retroactive issuance.

## Results and disconfirming evidence

The strongest adverse result is the degree of historical front-loading. Fourteen of 30 raw specimens (46.7%) occur before the first halving, 23 (76.7%) occur by height 368,527, and none occurs after height 756,951 on 2022-10-04. The current incomplete gap is 208,295 blocks, already almost twice the longest completed gap of 107,193 blocks. A sparse ledger exists, but its frequency is neither stationary nor well summarized by its historical median.

No non-genesis record occurred in the first 13 blocks of a difficulty period, no records were adjacent, and no historical retarget lowered the target below the entering frontier. Thus the feared “automatic record immediately after a difficulty jump” did not occur in this history. Difficulty growth still changes the conditional opportunity rate materially: 26 of 29 post-genesis specimens occurred at higher difficulty than the preceding specimen, two at the same difficulty, and one at lower difficulty. That association is not evidence that a retarget itself mechanically creates a specimen.

## Interpretation questions

1. **Does raw-record geology produce a sparse historical deposit sequence?** Yes. There are 30 raw specimens in 965,247 blocks. Completed intervals range from 1,028 to 107,193 blocks, with a median of 12,717 blocks. The current unfinished interval is 208,295 blocks.

2. **How strongly are deposits associated with Bitcoin difficulty growth?** Strongly in historical co-movement, but not exclusively: 26 of 29 post-genesis records have higher difficulty than the preceding record, two have equal difficulty, and one has lower difficulty. Four specimens (heights 334,261; 634,842; 742,035; and 756,951) occurred inside periods whose boundary reduced difficulty. Difficulty growth makes a fixed absolute frontier easier to beat relative to the valid-hash range; it does not determine which particular block wins.

3. **Do difficulty jumps produce effectively automatic records?** Not in the observed chain. Excluding genesis, zero raw records fall at retarget positions 0–12. At no retarget was the new target already below the entering frontier, the condition that would make the first valid block necessarily beat that frontier.

4. **Is difficulty sensitivity a bug or the intended consequence of absolute rarity?** It is mathematically inherent to measuring absolute hashes. Calling it intended does not establish that it is useful. If the desired law should be insensitive to Bitcoin's changing target, raw records fail that requirement; if absolute computational rarity is the desired quantity, removing the effect would change the statistic.

5. **How front-loaded is the history?** Materially. The halving-era counts are 14, 9, 4, 3, and 0 for eras 0 through 4 at the captured tip. Eighty percent of all specimens appear by height 458,091, before half of the observed block heights had elapsed. There have been no new specimens since 2022.

6. **What happens during stagnant or falling difficulty?** Records remain possible because valid hashes are sampled below the current target, but a fixed frontier becomes no easier to beat. The first three records occurred at difficulty 1. Four later records occurred during periods that began with a difficulty decrease. Long droughts are therefore possible and observed; falling difficulty does not erase or raise the frontier.

7. **At the current frontier and target, how rare is the next deposit?** The frontier is `0000000000000000000000005d6f06154c8685146aa7bc3dc9843876c9cefd0f`; the target is `000000000000000000023cc10000000000000000000000000000000000000000`. The gap is 18.615901 bits. Conditioned on a valid next block and the standard uniform-hash model, the probability is 0.00000248917536691, approximately 1 in 401,739 blocks.

8. **Does normalized-record geology appear practically exhausted?** The best normalized score is 0.000000620488975245, also set at height 756,951. Under an independent uniform conditional-score model, a new record has probability about 1 in 1,611,632 blocks. That is practically very slow at current scale, but “exhausted” is not literal: any future block can still set a record.

9. **What assumptions are needed to estimate future frequency?** At minimum: approximately uniform SHA-256 outputs conditional on target validity; a model for future Bitcoin targets and block cadence; independence sufficient for the chosen horizon; continued canonical-chain finality assumptions; and a model of miner publication/withholding behavior. Historical averages alone are inadequate because the target and fixed frontier interact.

10. **Can GoldAtom claimants influence whether a raw-record deposit exists?** A claimant acting only as a claimant cannot. The fact depends on the canonical Bitcoin header sequence, not on a claim or identity. A claimant who is also a Bitcoin miner has the same influence as any miner, described next; that influence comes from mining, not claiming.

11. **What influence does a Bitcoin miner have?** A miner searches many candidate headers as part of ordinary proof of work and can publish or withhold a valid block it finds. Withholding can suppress that candidate from canonical history, including a record candidate, at the cost and risk of losing the block reward. A miner cannot turn an above-frontier hash into a below-frontier one, and cannot remove another miner's established canonical record without a successful reorganization. Strategic behavior, reorg depth, timestamp/header-template freedom, and concentrated hash power remain part of the threat model and are not resolved by this experiment.

12. **What would falsify this candidate as useful?** Relevant falsifiers include an unacceptable dependence on target trajectory; economically plausible withholding or reorganization strategies that bias existence enough to matter; future difficulty changes causing bursts that violate the intended scarcity behavior; droughts too long for the intended system; ambiguity in canonical-chain/finality rules; or an inability to specify activation and later extraction without granting claimant influence. The observed front-loading and present drought are already disconfirming evidence against any claim of stable issuance cadence.

## Activation candidate, not executed

A future GoldAtom/1 profile could become active through a Bitcoin transaction containing a commitment equivalent to `GA1P || SHA256(frozen_profile)`. The canonical Bitcoin block containing that commitment would establish activation. Deposits at or below activation would remain permanently non-extractable historical specimens. Deposits above activation could become eligible only under a future extraction specification.

No activation height is selected here. No extraction, title process, ownership assignment, transaction, or GoldAtom minting is implemented or performed.
