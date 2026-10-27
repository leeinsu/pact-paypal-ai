# Browser route and callback origin check

Date: 2026-10-24.
Status: Browser route verified. PayPal login configuration remains unverified.
Terms follow the [glossary](../../GLOSSARY.md).

## Observations and address selection

The user selected the agent-controlled server browser for PayPal login.
The browser process and application commands share the server network namespace.
A temporary server returned the same random marker through localhost and the existing Tailscale HTTPS route.
The marker server was stopped before application startup.
No workstation port forwarding is necessary for this browser.
The investigation did not establish workstation browser access or VS Code forwarding configuration.

The confirmed service origin is `https://server-debian-dev.tailffdbc2.ts.net`.
The existing Tailscale configuration forwards HTTPS port 443 to `http://127.0.0.1:3000`.
This route permits tailnet access only.
The agent did not change Tailscale routing or enable public access.
An initial marker request timed out before the marker server supplied a response with Content-Length.
A subsequent marker request and application requests succeeded through the same route.

An independent Python TLS client verified the certificate chain and hostname without disabling certificate checks.
The negotiated protocol was TLSv1.3.
The certificate expires on 2026-12-16 at 16:48:10 UTC.

## Application alignment

The server now accepts an explicit `--service-origin` for `serve`, `work`, and `negotiate`.
Direct localhost TLS remains the default.
The explicit `--local-tls-proxy` mode requires a service origin and binds HTTP only to `127.0.0.1`.
This mode trusts the local TLS proxy as a deployment boundary.
It does not infer the origin or TLS state from forwarded headers.
Host checks, POST Origin checks, signed challenges, cookies, and callback generation retain the configured external origin.

| Purpose | Confirmed URL |
| --- | --- |
| Service | `https://server-debian-dev.tailffdbc2.ts.net` |
| Merchant callback | `https://server-debian-dev.tailffdbc2.ts.net/api/paypal/merchant/callback` |
| Buyer callback | `https://server-debian-dev.tailffdbc2.ts.net/api/paypal/buyer/callback` |
| Buyer cancellation | `https://server-debian-dev.tailffdbc2.ts.net/api/paypal/buyer/cancel` |

The application uses new private state at `/home/user/.local/state/pact-sandbox`.
Existing state, keys, transactions, and historical evidence remain separate.
The browser completed device login through HTTPS.
Its session cookie has Secure, HttpOnly, Path=/, and SameSite=Lax attributes.
The cookie is restricted to the confirmed service host.
The browser retained its session after reload and after visiting PayPal.
The browser also retained its session after the application server restarted with the same private state.
The signed record summary returned HTTP 200 and the confirmed service origin.
Callback requests without consent parameters returned HTTP 400 without submitting payment requests.

## PayPal policy and remaining configuration

The official login documentation requires configuration of Log in with PayPal and a matching Return URL.
It does not establish localhost acceptance or rejection.
The investigation could not verify localhost policy through an authenticated Developer Dashboard.
IPN localhost restrictions concern server notifications and do not establish login redirect policy.
The selected callback avoids localhost without claiming provider registration success.

Sources:

- [PayPal login configuration](https://developer.paypal.com/log-in/build/), Enable Log in with PayPal and Test.
- [PayPal authorization endpoint](https://developer.paypal.com/log-in/build-button/), Construct authorization endpoint.
- [PayPal redirect matching](https://www.paypal.com/au/cshelp/article/how-do-i-set-a-redirect-url-for-the-paypal-identity-api-ts1995).

The application generated a merchant login request with the confirmed callback.
PayPal returned `invalid client_id or redirect_uri` before account login.
The dashboard remains unchanged according to the user.
This combined error does not isolate client identity, login eligibility, or Return URL configuration.
The [Korean checklist](user-checklist.ko.md#실제-판매자-로그인-설정) supersedes the earlier localhost registration instruction.
The user must save the confirmed merchant Return URL in the matching Sandbox app.
Actual consent and the PayPal return remain pending that configuration.

## Scope and language review

No new payment, Vault token creation, order, authorization, capture, or void occurred.
This work consumed JPY 0 and did not reset or increase the cumulative JPY 2500 limit.
These checks do not close G3 or G4.
The full suite passed 512 tests with no failures or skipped tests.
The proxy listener test uses an ephemeral port to avoid the running application port.
The [evidence record](evidence/callback-origin-local-20261024.json) contains test results and artifact hashes.

Language review covered changed English prose, terms, sentence lengths, conditions, and uncertainty.
The Korean checklist follows the user's explicit language exception.
Commands, paths, URLs, flags, cookie attributes, and API errors retain their exact forms.
The language review assigns no design score and claims no formal ASD-STE100 compliance.
