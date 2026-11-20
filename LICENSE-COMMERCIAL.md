# shellguard Commercial License

Version 1.0. This license is granted to the customer named on a shellguard
license key ("Licensee") and supplements the MIT License that governs the
source. It exists so a company can embed shellguard in a proprietary or
distributed product without the MIT attribution and source-disclosure
obligations, and with a written support commitment from the issuer.

## 1. Grant

The issuer grants Licensee a perpetual, worldwide, non-exclusive,
non-transferable right to:

- use shellguard in one product or one internal system;
- redistribute shellguard inside that product without publishing its source;
- remove or retain the MIT attribution notice at Licensee's discretion;
- receive the packaged download and updates for the licensed version.

## 2. License key

A license key is an offline HMAC-SHA256 token in the form
`SG1-<payload>.<signature>`. It names the customer and the tier and carries
an issue and expiry timestamp. Verify it locally:

```python
from shellguard.license import verify, LicenseError

try:
    lic = verify(key, issuer_secret)
    print(lic.customer, lic.tier, lic.expires)
except LicenseError as exc:
    print("not licensed:", exc)
```

The key is issued by the issuer and is deterministic for a given customer,
tier and issue time: a reissued key for the same inputs is identical.

## 3. Restrictions

Licensee may not resell or sublicence shellguard as a standalone product,
may not publish the issuer secret, and may not issue keys. The key is tied to
the named customer; a key issued for one customer does not license another.

## 4. Support

One email support thread per month, answered within two business days, for
the licensed version. Include the license key in the subject.

## 5. Warranty and liability

shellguard is provided "as is", without warranty of any kind. The issuer is
not liable for damages arising from its use. The MIT License continues to
apply to the source to the extent this license is silent.

## 6. Term

Perpetual for the licensed version, subject to the expiry encoded in the key.
