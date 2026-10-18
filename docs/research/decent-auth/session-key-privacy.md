# Privacy-preserving transaction session keys

**Research date:** 2026-10-18
**Research issue:** [#48](https://github.com/jetpen/decent-ecosystem/issues/48)
**Parent map:** [#29](https://github.com/jetpen/decent-ecosystem/issues/29)

## Executive findings

**Assessment — best fit to investigate next:** use a fresh, random Ed25519 session key for each site-authenticated transaction session, and have the wallet privately authorize that key by signing a domain-separated binding that names the session key, exact site, fresh session identifier, expiry, and narrowly defined purpose. Deliver that binding to the participating site over its authenticated private channel, not with public transactions. The site validates the owner signature against the current Registry-resolved Identity key and retains the owner-to-session-key mapping. If the target transaction format permits an independent session key, transactions can then carry the session public key and signature, allowing public verification under that key without publishing the owner identifier, Identity public key, or owner-signed binding. No ledger was specified, so this transaction-format assumption is unresolved.

This is an *option for a follow-up protocol decision*, not an adopted design or implementation. It meets the site-correlation goal only if public transaction verification is allowed to trust the session key without a public owner-to-session delegation proof. If a public ledger/validator must independently prove that the session key was authorized by the owner, publishing a directly verifiable delegation would expose a link; a zero-knowledge/anonymous-credential or equivalent proof profile would then be required. The repository's current Identity boundary treats exact-key lookup as an input to authentication, not authorization, and the wallet-login contract explicitly separates authentication from consent and operation authority. See the current [wallet](../../components/decent-wallet.md) and [Identity](../../components/decent-identity.md) boundaries and [wallet-login v1](../../protocol/wallet-login/v1/README.md).

Do not equate “derived” with “privately authorized.” A deterministic child key derived from root material and an independently generated ephemeral key signed by the Identity key have different recovery, compatibility, and key-compromise properties. The current ecosystem documents an Ed25519 Identity key but does not specify an HD master seed/chain code or a child-derivation profile. [RFC 8032](https://www.rfc-editor.org/rfc/rfc8032.html) defines EdDSA private key material as an input bit string; [SLIP-0010](https://github.com/satoshilabs/slips/blob/master/slip-0010.md) defines an Ed25519 HD derivation scheme with hardened private derivation, but is not derivation from an arbitrary already-existing public key or a standard public child-key scheme. [1][2]

**Recommendation for the next design ticket:** make the independently generated, per-session key privately authorized by the Identity key the baseline to evaluate. It fits existing Ed25519 verification and avoids inventing child-key derivation from a key type whose wallet root/chain-code semantics are unspecified. Keep derivation as an alternative only if the wallet's actual root secret and migration/recovery model can be established. This recommendation does not settle whether transactions are per-site, per-login, or per-device, nor whether the public system must verify owner delegation.

## Current ecosystem facts and boundaries

- The ecosystem's wallet boundary assigns private-key custody and signing to `decent-wallet`; Identity resolves public-key bindings but does not authenticate challenges, establish sessions, or issue consent/authorization. The wallet component handoff marks recovery, rotation, portability, and migration as unresolved. See [`decent-wallet.md`](../../components/decent-wallet.md) and [`decent-identity.md`](../../components/decent-identity.md).
- Approved `decent-wallet-login-v1` is a fresh, single-use login proof. It is not a reusable transaction key or transaction authorization. Its proof carries the exact raw `identity_id` to the authenticating Provider, and the current contract keeps the Identity ID out of the displayed challenge/QR. Do not change that profile as part of this research. See [#46](https://github.com/jetpen/decent-ecosystem/issues/46) and the [vector README](../../protocol/wallet-login/v1/README.md).
- A successful login must not silently grant operation authority. A session-key binding, even if signed by the owner's Identity key, needs an explicit wallet decision that states its purpose and scope; transaction-specific approval and site policy remain separate. This is an ecosystem boundary, not a new protocol claim.

## Threat model and candidate flow

### Parties and visibility

| Party | Sees during private setup | Sees on public transaction | Desired capability / risk |
|---|---|---|---|
| Owner wallet | Identity secret, session secret, site context, transaction details | Its own public transaction | Must keep both secrets local and show a distinct approval for session setup and any required transaction consent. |
| Participating site | Exact owner Identity ID/key (from login/Registry), session public key, private binding, and any transactions it observes | Public transaction fields | Stores the mapping from Identity to session key/transaction. A site compromise or collusion exposes it. |
| Public observer/ledger | Session public key, transaction payload/signature, timing and network/publication metadata | Same | Can verify the session signature and correlate transactions that reuse the same session key; should not receive the owner's stable identifier/key or private binding. |
| Other sites | Only what their own authentication/transactions reveal | Public transactions | Must not receive a common long-lived session key or shared mapping. Colluding sites can still compare their private records and public metadata. |

Privacy Pass documentation similarly treats IP address, event time, Origin name, and deployment collusion assumptions as part of the privacy context; cryptography over transaction fields cannot by itself hide those signals. Its stated Origin-client unlinkability depends on matching redemption contexts and deployment assumptions. [5]

### Candidate private-binding flow

```text
Owner wallet                 Participating site               Public ledger
     |                               |                               |
     |-- fresh login proof (v1) ---->|  private exact Identity ID   |
     |                               |  resolve current owner key   |
     |-- session public key,         |                               |
     |   owner-signed binding ------>|  verify with current key;     |
     |                               |  store ID -> session key      |
     |                               |                               |
     |-- transaction + session sig -------------------------------->|  verify under
     |                               |                               |  session key
     |                               |<------ observe/index tx ------|
     |                               |  correlate via private map    |
```

The signed binding should use a new, versioned domain separate from wallet-login v1 and include at least: profile/version; exact session public key; exact participating-site origin or configured site identifier; fresh unpredictable session identifier; expiry; and an explicit key-use/purpose field. Any transaction scope, maximum count/value, or resource/action restriction must be explicit if required by the application; it must not be inferred from login. These are requirements for a follow-up profile, not a proposed wire format.

The public transaction must omit the Identity ID, Identity public key, owner-signed binding, stable OIDC `sub`, and any stable site/account identifier. Reusing one session public key intentionally makes transactions linkable *to each other within that session*. Rotate the key for each new session and use a site-specific context to avoid cryptographic cross-session/cross-site linkage. Public transaction content, funding/account addresses, timing, IP/network path, relaying/publishing behavior, and rare activity patterns can still correlate records; no key scheme alone provides anonymity.

If the participating site does not observe transactions and the transaction format exposes no session public key or other session identifier, it cannot correlate an observed transaction to its private mapping. Conversely, if the site publishes the owner-signed binding or an encrypted correlation handle that other parties can resolve, it has changed the trust model and must separately justify the privacy of that field.

## Approaches

### 1. Derive an Ed25519 child key from Identity key material

**What it means.** The wallet deterministically computes a child signing key using a defined KDF/HD derivation and a unique session context. It still needs to show the site that the child belongs to the authenticated owner. A private owner signature over the child public key and context can provide that proof; the signature must not be included with public transactions.

**Standards evidence and compatibility.** HKDF is a general extract-and-expand KDF, with context supplied through its `info` input; RFC 5869 does not define an Ed25519 child-key format or the desired transaction-session profile. [3] SLIP-0010 defines Ed25519 derivation from an HD seed/extended private node and supports hardened private-to-private child derivation; it explicitly does not support public-key derivation for Ed25519. This is a plausible existing construction only if the wallet starts from compatible root seed/chain-code material and implements the exact SLIP-0010 profile. [2] BIP-0032's public-child derivation model is curve/scalar-specific and its extended private/public keys carry additional chain-code state; it must not be assumed to operate on the ecosystem's raw Ed25519 key. [4]

**Fit to this wallet.** The ecosystem documentation names an Ed25519 Identity key but does not say that the Identity key is an HD child, that its originating seed/chain code is retained, or that a compatible path is supported. See [wallet](../../components/decent-wallet.md), [Identity](../../components/decent-identity.md), and [login v1](../../protocol/wallet-login/v1/README.md). Therefore, deriving a child directly from the existing Registry public key is not provided by the cited Ed25519 HD profile, and deriving from an unspecified 32-byte signing seed would be a new cryptographic profile, not an established wallet capability. HKDF can be a primitive in a carefully specified design; using `HKDF(identity_seed, site, session) -> 32 bytes -> Ed25519 seed` is not by itself a reviewed or interoperable standard profile. [1][2][3]

**Trade-offs.** Deterministic derivation can make a lost session key reproducible if the wallet preserves the exact root material and all derivation context. That also makes compromise of the root compromise every derived session key; compromise of a child key should not reveal the root only if the selected derivation scheme's security properties hold. The site still needs the private owner-to-child binding for correlation and verification. Reusing the same derivation context recreates the same public key and linkability; use of a random session identifier prevents accidental reuse but means the wallet must persist that identifier to recover the same key. SLIP-0010's hardened mode avoids publishing a public derivation path but means a site cannot derive or validate the child public key from only the parent's public key and a path. [2][4]

**Assessment.** Do not adopt this as the MVP baseline until the wallet confirms its actual root-key representation, derivation compatibility, migration/recovery, and cross-language implementation support. Do not apply HKDF directly to an Ed25519 encoded public key or treat the RFC 8032 seed as a general-purpose scalar without a reviewed construction. [1][2][3]

### 2. Generate an independent ephemeral key and privately authorize it with Identity key

**What it means.** The wallet generates a fresh Ed25519 keypair for the session. After login, it signs a context-bound statement binding that public key to the site/session and intended use. It sends the statement and signature only to the site over the authenticated private channel. The site verifies with the current Identity key, stores the mapping, and returns/records any needed session metadata. Public transactions use only the session key.

**Compatibility.** This uses ordinary Ed25519 key generation and verification already present in the ecosystem's login proof profile; it requires no Ed25519 child-key derivation. [1] The private binding is a new protocol object and must define canonical encoding, domain separation, site/session binding, expiry, replay handling, and wallet consent before implementation. See the [wallet-login v1 profile](../../protocol/wallet-login/v1/README.md) for the adjacent but separate login contract.

**Trade-offs.** A random key avoids deterministic cross-session linkage and limits the effect of a session-key leak to that session; it cannot be recovered after loss unless the wallet retains a backup or the owner creates a new session. The Identity key can revoke future sessions by refusing to authorize them, but cannot retroactively revoke already-published transactions or invalidate signatures accepted by a ledger unless a separate revocation/policy mechanism exists. The site mapping remains sensitive site-held state. If the same session key signs multiple transactions, observers can link those transactions to that pseudonymous session, but not cryptographically to the owner's Identity without the private mapping or outside information.

**Assessment.** This is the most compatible and smallest design to take to the next decision gate. It is not a mathematical child key derived from the Identity secret; it is an independently generated key *authorized by* the Identity key. The protocol owner must confirm whether that distinction satisfies the product requirement.

### 3. Unlinkable credential/token alternatives

Privacy Pass offers a different primitive: a Client obtains cryptographic tokens through an issuance flow and redeems tokens for authorization without the Origin learning a unique client identifier through the token itself. The standardized HTTP scheme is `PrivateToken`, not ordinary session-key transaction signatures; token reuse can link transactions, so clients often present a token once. [5][6] RFC 9578 defines OPRF-based private verification and blind-RSA public verification issuance variants. The issuance/redemption separation and its privacy depend on deployment roles, metadata, anonymity sets, and whether Issuer/Origin/Attester parties collude. [5][7][8][9]

The current BBS signature scheme draft supports zero-knowledge proofs of signed messages, selective disclosure, and unlinkable presentations; the active IRTF draft is work in progress (draft-13 at research time), not a published RFC. [10] A separate Blind BBS Signatures draft describes hidden-message signing, but is also work in progress. [11] These approaches may help if future requirements need public verifiers to validate narrowly scoped owner credentials without seeing identifiers. They are substantially more complex, do not directly give an ordinary Ed25519 public transaction signature, and do not automatically let the participating site correlate a redemption with an owner. BBS unlinkability applies to the proof value, not arbitrary other values a Prover discloses. [10] Issuer/trust, status/revocation, wallet-library, and transaction integration remain separate design work.

**Assessment.** Keep Privacy Pass/BBS as a future research branch if the public ledger must validate owner-authorized rights while preserving unlinkability from the issuer/owner identity. They are not a drop-in answer for “site can correlate this public session key to its authenticated owner.”

## Comparison summary

| Approach | Public verifier | Site correlation | Linkability | Existing Ed25519 fit | Main unresolved risk |
|---|---|---|---|---|---|
| SLIP-0010 derived child | Verifies transaction under child key; public owner delegation still needs a proof | Site keeps private owner-to-child mapping/binding | Same child key links transactions in one session; unique hardened child per session avoids direct equality across sessions | Only if wallet has compatible HD root/chain code; no public derivation for Ed25519 | Current wallet's actual key origin, root material, recovery, and implementation are unspecified. |
| HKDF-derived Ed25519 seed | Verifies transaction under child key; no public owner link without an added public proof | Same private mapping/binding requirement | Per-session context can make child keys distinct; context reuse repeats key | Technically plausible as a new profile, but not an existing Ed25519 derivation standard | Must specify construction, key separation, exact IKM semantics, vectors, and review. |
| Random ephemeral Ed25519 + private owner signature | Verifies transaction under session key only | Site validates private owner signature and stores mapping | Transactions link within session; fresh key per session/site avoids direct cryptographic link across sessions/sites | Highest fit: normal Ed25519 keys/signatures | Public validators cannot know owner authorized it unless an additional privacy-preserving proof is added. |
| Privacy Pass / BBS credentials | Token/BBS proof verifier checks issuer signature/proof, not an Ed25519 transaction key by itself | Oblivious issuance/privacy may prevent issuer-site correlation unless site separately keeps a mapping | Designed to reduce issuance/redemption or proof linkability; metadata and reuse still matter | New cryptographic suites/libraries and protocol integration | More infrastructure; current scheme/drafts are not transaction signing/session-key profiles. |

## What “only the site can correlate” can and cannot mean

A cryptographic design can keep the stable owner ID, Identity public key, and owner-signed session binding out of public transaction artifacts while allowing the site—who received the private binding—to map a session public key to the authenticated owner. This is pseudonymity relative to public observers, not anonymity against the participating site.

That claim requires all of the following assumptions: the binding is sent only to the intended site; the session key is not reused outside its intended scope; the site does not publish/share its mapping; transactions expose no other stable owner identifier; and observers cannot identify the owner through timing, network, funding, transaction content, or external records. A site database compromise or collusion reveals the mapping. Privacy Pass's own threat model treats event time, IP address, Origin name, deployment, and collusion as part of the privacy analysis. [5]

Transactions using one session public key are intentionally publicly linkable to that key. If the requirement instead demands that even the public ledger cannot link same-session transactions, use one-time transaction keys or a privacy-preserving proof/credential design; the ledger then needs another way to validate each transaction and the site needs another private correlation handle. RFC 9577 warns that a reused `PrivateToken` can enable transaction linkage and describes the common one-token-per-challenge model. [6]

## Open decisions for the follow-up

1. Does “derived from the owner's identity key” strictly require deterministic child-key derivation, or is independent per-session key generation plus a private owner-key signature sufficient?
2. Does the public transaction verifier need proof that the owner authorized the session key, or is verification under the session key sufficient while the site alone retains the attribution mapping?
3. Is within-session public linkability an intended feature? What is the exact rotation boundary: each login, site, device, or transaction?
4. What is the minimum transaction consent and scope shown in the wallet, and does the session key authorize one transaction, a bounded transaction class, or only identify a login/session?
5. What is the wallet's actual Ed25519 private-key representation and generation path? Does it retain an HD seed/chain code, or only a raw Ed25519 signing seed? What recovery/rotation guarantees are intended?
6. Must site correlation survive site database loss, or is the site mapping deliberately the only correlation authority? What metadata-retention/access-control policy applies?
7. Which ledger/transaction format, public-key/signature fields, and transaction-indexing path are targeted? No ledger or transaction format was specified by #48, so ledger-specific claims remain open.

## Conclusion and next step

Research favors a fresh per-session Ed25519 key privately authorized by the owner's Identity key over inventing a child-key derivation from the present Identity key. This supports site-only attribution as an off-chain mapping while keeping owner identity material out of public transactions, but it does not enable a public verifier to establish owner delegation unless the design adds an anonymous credential or proof. Keep this as a recommendation, not a protocol decision.

A separate design decision ticket is needed to settle the derivation meaning, public-verification requirement, intended within-session linkability, session lifetime/scope, wallet consent, and private mapping contract. Do not amend the approved wallet-login v1 or claim a transaction-authentication flow exists.

## Sources

[1] https://www.rfc-editor.org/rfc/rfc8032.html — RFC 8032: Edwards-Curve Digital Signature Algorithm (EdDSA)
[2] https://github.com/satoshilabs/slips/blob/master/slip-0010.md — SLIP-0010: Universal private key derivation from master private key
[3] https://www.rfc-editor.org/rfc/rfc5869.html — RFC 5869: HMAC-based Extract-and-Expand Key Derivation Function (HKDF)
[4] https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki — BIP-0032: Hierarchical Deterministic Wallets
[5] https://www.rfc-editor.org/rfc/rfc9576.html — RFC 9576: The Privacy Pass Architecture
[6] https://www.rfc-editor.org/rfc/rfc9577.html — RFC 9577: The Privacy Pass HTTP Authentication Scheme
[7] https://www.rfc-editor.org/rfc/rfc9578.html — RFC 9578: Privacy Pass Issuance Protocols
[8] https://www.rfc-editor.org/rfc/rfc9474.html — RFC 9474: RSA Blind Signatures
[9] https://www.rfc-editor.org/rfc/rfc9497.html — RFC 9497: Oblivious Pseudorandom Functions Using Prime-Order Groups
[10] https://datatracker.ietf.org/doc/draft-irtf-cfrg-bbs-signatures/13 — The BBS Signature Scheme, Internet-Draft 13
[11] https://datatracker.ietf.org/doc/draft-irtf-cfrg-bbs-blind-signatures/03 — Blind BBS Signatures, Internet-Draft 03
