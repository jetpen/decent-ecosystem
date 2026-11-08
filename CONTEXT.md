# Decentralized Ecosystem

This context defines the canonical domain language for the decentralized ecosystem vision. It describes conceptual ownership and boundaries; it is not an implementation specification.

## Identity and Account

**Identity**:
The user's private key paired with its public key and associated information that identifies the person, including their name and aliases such as email address or telephone number. The private key is controlled and retained by the user's wallet and is never transmitted as registry content.

_Avoid_: account, profile, `decent-identity` service

**Identity Owner Key (Owner Key)**:
The user's wallet-controlled asymmetric key pair used to prove control of an Identity and sign owner-authorized statements. Its public key is bound to the exact Identity identifier by the current validated Registry Record; its private key remains in the Wallet. In the wallet-login and wallet-account-disclosure v1 profiles, this is an Ed25519 key pair. An Owner-Key signature proves control of that key, not independent verification of the user's account/profile claims. This key is distinct from wallet-container encryption keys, RP signing keys, and Keycloak signing keys.

_Avoid_: wallet encryption key, RP signing key, Keycloak signing key, third-party attestation

**Account**:
User-owned information associated with a particular website and selectively disclosed by the user. A website may maintain its own proprietary representation of that user's account; that site-owned representation is opaque to this ecosystem and is distinct from the user-owned account information.

_Avoid_: identity, global account, website's proprietary account record

**Profile**:
Additional user-owned data beyond the properties of the user's identity and account that a website may associate with the user, such as preferences, time zone, or language. The user controls whether profile data is disclosed to a particular website.

_Avoid_: identity properties, account properties, website-owned profile

**Wallet**:
A user-controlled component that generates, holds, and strictly protects the user's private-key and public-key pair; accepts authentication challenges; responds to them; signs user-authorized Registry updates; participates in threshold approval through independent multisignature signing; and acts as the user's consent agent for disclosure and selected threshold-approved operations. Signer wallets retain their own secrets, and only finalized threshold-approved material is submitted to the Registry. Its authoritative retained data includes key material, local signing, approval, authorization state, and the wallet-local Master Account Entity. Site-specific Account Entities may be delegated to an External Storage Provider only through separate explicit user authorization; the Master Account Entity remains local. Wallet initialization includes an owner setup step that establishes a password-derived symmetric encryption key for securely storing wallet contents. The password and derived key remain local to wallet protection and are never displayed, logged, transmitted, or otherwise disclosed; the private key is never exposed outside the wallet. The wallet is distinct from the user's identity, account, profile, and registry records.

_Avoid_: identity, account, profile, registry, consent authority for site policy

**Authentication**:
The wallet's response to a website challenge that demonstrates control of the identity's private key. Authentication establishes control of an identity for a particular interaction; the participating application establishes its own login session only after successful verification. Authentication does not by itself grant access to account information or site resources.

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
The person or organization that administers a participating site, controls its configuration and any proprietary site-owned account representation it maintains, but does not control the user's wallet, identity, private keys, user-owned account information, or profiles.

_Avoid_: user, site-owned account information, identity owner

**Storage Provider Operator**:
The person or organization that administers a `decent-simple-storage` service instance and its infrastructure. The Storage Provider Operator may approve owner onboarding, assign or change a bounded storage quota, and enforce provider-wide operational policy, but does not own user Storage Objects, issue or broaden data consent, interpret site policy, or become the authority for user disclosure.

_Avoid_: data owner, wallet authority, consent authority, site operator

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

**decent-wordpress-auth**:
The first site-specific authentication implementation for a participating Apache/WordPress site. It coordinates wallet authentication and purpose-bound disclosure requests, verifies the designated wallet proof, establishes a site-local session, and uses a user-owned site-specific Account Entity as the conceptual registration record through user-mediated authorization. A separate opaque site-owned account registration is not required by the ecosystem MVP. It does not issue or broaden wallet capabilities, own the user's identity, wallet keys, account/profile data, consent, Registry records, or ecosystem-wide authorization.

_Avoid_: universal authenticator, identity authority, wallet, account owner, consent authority

**decent-simple-storage**:
A provisional external storage-provider component that onboards owners, accepts, retains, retrieves, and updates user-owned storage objects as a delegated custodian. Its primary ecosystem use is schema-open JSON account entities containing account/profile information, site-specific settings and preferences, and selective disclosures. It also provides generically useful storage for owner-authorized arbitrary binary or textual content whose content type is permitted by a provider allowlist and whose owner has been approved for an assigned capacity limit; the provider enforces that quota before accepting storage growth. It enforces presented capabilities but does not own stored objects, issue or broaden consent, interpret site policy, or become the authority for user disclosure. Each uploaded Storage Object is content-addressed by its SHA-256 content digest and has corresponding public Provider Record discovery metadata in `decent-registry`; Registry is not the object store and does not contain the object content.

_Avoid_: data owner, consent authority, registry backend, identity authority, unallowlisted content, unlimited owner storage

**Storage Object**:
A user-owned item that may be created, uploaded, retrieved, downloaded, updated, replaced, or deleted through `decent-simple-storage` under applicable capabilities and provider limits. Each uploaded Storage Object is identified for discovery by the SHA-256 digest of its content. An Account Entity is the ecosystem's primary JSON Storage Object with site-specific account/profile meaning; other Storage Objects may contain owner-authorized allowlisted content without becoming Registry Records, identity data, or site-owned account representations.

_Avoid_: Registry Record, identity, site-owned account, unrestricted content

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
The relationship between a user's user-owned account information and a particular participating site, including the site's opaque account representation and associated sessions. Each site MUST declare its signup policy as open or closed. Open signup permits creation of a new Keycloak principal and site account from a wallet-local Identity only when the exact Identity is not already present in Keycloak. Closed signup also creates an account from a previously absent Identity, but the site MUST withhold access until a site administrator approves that account. When an enabled exact Keycloak principal already exists but the site has no local account for it, the user may use the distinct `signup_recovery` action with fresh wallet proof to create that site account without creating another Keycloak principal; disabled principals remain blocked. The site's open/closed policy still determines whether administrator approval is required before access. Deactivation ends or refuses this relationship without deleting the user's identity, wallet, or unrelated site relationships.

_Avoid_: global identity deactivation, identity deletion, ecosystem-wide account

**Account Entity**:
A user-owned, site-specific entity containing account/profile information, settings, preferences, or selective disclosures. An account entity is stored by an external storage provider and is distinct from its public Provider Record, the user's identity, and the participating site's opaque proprietary account representation. Its schema may vary by site, but it is not arbitrary application data.

_Avoid_: registry record, public profile, arbitrary application content, site-owned account

**Master Account Entity**:
A user-owned, cross-site JSON entity held only in the authenticated encrypted wallet-container. It contains reusable account/profile information, preferences, and selectively disclosable data. It is not uploaded, replicated, or stored by an External Storage Provider because that provider does not ensure the privacy required for this sensitive cross-site entity. A participating site may receive selected fields only through an explicit wallet-approved disclosure. The Master Account Entity remains distinct from each site's opaque account representation and from site-specific Account Entities; edits do not automatically propagate to site-specific accounts.

_Avoid_: global public profile, site-owned account, Registry Record, external-storage object, unrestricted disclosure

**External Storage Provider**:
A separate component that accepts, retains, retrieves, and updates site-specific user-owned Account Entities as a delegated custodian. It enforces presented capabilities but does not own the entities, issue or broaden consent, interpret site policy, or become the authority for user disclosure. It MUST NOT store the wallet-local Master Account Entity. `decent-simple-storage` is the provisional MVP component for site-specific Account Entities.

_Avoid_: registry backend, identity authority, data owner, consent authority
