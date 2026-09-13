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
A user-controlled component that holds and strictly protects the user's private-key and public-key pair for accepting authentication challenges and responding to them. The private key is never exposed outside the wallet. The wallet is distinct from the user's identity, account, profile, and registry records.

_Avoid_: identity, account, profile, registry

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
A website, initially a self-hosted Apache/WordPress installation, that integrates the authentication component and offers site services to users.

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
An existing service and repository that performs exact-match lookup, publication, and retrieval of public-key bindings for human-readable identifiers by using `decent-registry` as its storage and resolution backend. It is a component that manages identity records, not the user's identity, wallet, private keys, account, or profile.

_Avoid_: identity, wallet, account service, registry
