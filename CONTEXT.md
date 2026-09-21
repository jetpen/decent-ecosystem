# Decentralized Ecosystem

This context defines the canonical domain language for the decentralized ecosystem vision. It describes conceptual ownership and boundaries; it is not an implementation specification.

## Identity and Account

**Identity**:
The user's private key paired with its public key and associated information that identifies the person, including their name and aliases such as email address or telephone number. The private key is controlled and retained by the user's wallet and is never transmitted as registry content.

_Avoid_: account, profile, `decent-identity` service

**Account**:
User-owned information associated with a particular website and selectively disclosed by the user. A website may maintain its own proprietary representation of that user's account; that site-owned representation is opaque to this ecosystem and is distinct from the user-owned account information.

_Avoid_: identity, global account, website's proprietary account record

**Profile**:
Additional user-owned data beyond the properties of the user's identity and account that a website may associate with the user, such as preferences, time zone, or language. The user controls whether profile data is disclosed to a particular website.

_Avoid_: identity properties, account properties, website-owned profile

**Wallet**:
A user-controlled component that generates, holds, and strictly protects the user's private-key and public-key pair; accepts authentication challenges; responds to them; signs user-authorized Registry updates; participates in threshold approval through independent multisignature signing; and acts as the user's consent agent for disclosure and selected threshold-approved operations. Signer wallets retain their own secrets, and only finalized threshold-approved material is submitted to the Registry. Its authoritative retained data is limited to key material and local signing, approval, and authorization state; account/profile entities remain external user-owned data. Wallet initialization includes an owner setup step that establishes a password-derived symmetric encryption key for securely storing wallet contents. The password and derived key remain local to wallet protection and are never displayed, logged, transmitted, or otherwise disclosed; the private key is never exposed outside the wallet. The wallet is distinct from the user's identity, account, profile, and registry records.

_Avoid_: identity, account, profile, registry, consent authority for site policy

**Authentication**:
The wallet's response to a website challenge that demonstrates control of the identity's private key. Authentication establishes control of an identity for a particular interaction; it does not by itself grant access to account information or site resources.

_Avoid_: authorization, identity resolution, login session

**Authorization**:
The user's permission for a website or another component to access or act on user-owned account/profile information or a site resource after authentication. Authorization is distinct from identity resolution and authentication.

_Avoid_: authentication, identity, implicit access

**Threshold Approval**:
Authorization of an operation by at least a configured number of distinct authorized signers from a defined signer set. The ecosystem MVP requires threshold approval for selected sensitive account operations; whether login also requires it is delegated to the component-repository specifications.

_Avoid_: single-key approval, password-only approval, recovery policy

## Participants and Components

**User**:
The person who controls the identity and wallet, owns the user-owned account information and profiles, and decides disclosure and authorization.

_Avoid_: account, operator, site administrator

**Participating Site**:
A website, initially a self-hosted Apache/WordPress installation, that integrates a site-specific authentication implementation and offers site services to users. `decent-wordpress-auth` is the first such implementation, not a universal authentication authority.

_Avoid_: component, registry, operator

**Operator**:
The person or organization that administers a participating site, controls its configuration and proprietary site-owned account representation, but does not control the user's wallet, identity, private keys, user-owned account information, or profiles.

_Avoid_: user, site-owned account information, identity owner

**Component**:
An independently implemented system or repository with a distinct capability boundary, data responsibility, trust boundary, and lifecycle. The existing components are `decent-identity` and `decent-registry`; the provisional components are `decent-wallet` and `decent-wordpress-auth`.

_Avoid_: feature, shared database, repository-free service

## Registry Components

**Registry Record**:
An authorized, signed statement that `decent-registry` stores and resolves without owning the user, account, or profile described by it. The current Registry defines Identity Records for owner-name/public-key bindings and Provider Records for provider locations; the consuming component gives each record its application meaning.

_Avoid_: database row, identity, account, profile

**decent-identity**:
An existing, capability-neutral service and repository that performs exact-match lookup, publication, and retrieval of user-authorized public-key bindings for human-readable identifiers. Identifiers use their raw UTF-8 form without normalization or alias expansion. It is an identity-specific adapter over a `decent-registry` deployment; the Registry owns the record network, validation, replication, and durable storage. The wallet-authorized signed record is the source of publication authority; `decent-identity` does not mint or alter it. `decent-registry` is the authoritative storage and resolution substrate for these records; `decent-identity` owns no authoritative identity data and resolves no binding when the Registry cannot validate or resolve one. Public-key resolution does not itself authenticate users. `decent-identity` may relay verified authorization metadata attached to a Registry Record, but does not interpret threshold approval or decide whether it authorizes a site action. It does not verify login challenges, establish sessions, grant authorization, interpret consent, approve site actions, or own the user's identity, wallet, private keys, account, profile, or application data.

_Avoid_: identity, wallet, account service, authorization authority, registry

## Authority and Trust

**User-sovereign capability model**:
The user controls disclosure and authorization for identity, account, and profile information. The wallet is the sole private-key custodian and the user's consent agent. Components receive only purpose-bound capabilities, and the participating site controls only its opaque site-owned account representation.

_Avoid_: service-mediated ownership, authentication-implies-consent, ecosystem-wide authorization

**Purpose-bound consent**:
A user's explicit wallet-mediated grant that is limited to a requesting site or component, a stated purpose, requested data or capability, and an appropriate interaction or session scope. Authentication alone does not imply consent.

_Avoid_: implicit consent, unrestricted disclosure, standing access by default

**Capability-neutral infrastructure**:
The conceptual role of `decent-identity` and `decent-registry`: identity-binding lookup/publication and authorized registry-record storage/resolution without ownership of account/profile data, interpretation of user consent, site authorization, or approval of site actions.

_Avoid_: policy authority, account owner, consent authority

**Site relationship**:
The relationship between a user's user-owned account information and a particular participating site, including the site's opaque account representation and associated sessions. Deactivation ends or refuses this relationship without deleting the user's identity, wallet, or unrelated site relationships.

_Avoid_: global identity deactivation, identity deletion, ecosystem-wide account

**Account Entity**:
A user-owned, site-specific entity containing account/profile information, settings, preferences, or selective disclosures. An account entity is stored by an external storage provider and is distinct from its public Provider Record, the user's identity, and the participating site's opaque proprietary account representation. Its schema may vary by site, but it is not arbitrary application data.

_Avoid_: registry record, public profile, arbitrary application content, site-owned account

**External Storage Provider**:
A separate component that accepts, retains, retrieves, and updates user-owned account entities as a delegated custodian. It enforces presented capabilities but does not own the entities, issue or broaden consent, interpret site policy, or become the authority for user disclosure. `decent-simple-storage` is the provisional MVP component for this role.

_Avoid_: registry backend, identity authority, data owner, consent authority
