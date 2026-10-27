# Retention policy evidence

Date: 2026-10-25.
Status: Partial research. Deletion remains disabled.
Scope: Official PayPal Japan sources and their limits for PACT.
Terms follow the [shared glossary](../../GLOSSARY.md).

## Verified source statements

| Source and section | Verified statement | Effect on PACT |
| --- | --- | --- |
| [Buyer Protection](https://www.paypal.com/jp/legalhub/paypal/buyer-protection?locale.x=en_JP), Opening Disputes: Timeframes | Item Not Received disputes have a 180-day opening window after payment. | A one-day demonstration date does not cover this window. |
| Same source, Opening Disputes: Timeframes | Description disputes use the earlier of 30 days after fulfillment and 180 days after payment. | Claim type changes the applicable deadline. |
| Same source, Online dispute resolution process | An unresolved dispute requires escalation within 20 days after opening. | The opening deadline alone does not establish a final deletion date. |
| Same source, Dispute with PayPal or your card issuer | Card issuer rights can exceed PayPal Buyer Protection rights. | A universal 180-day deletion rule lacks sufficient support. |
| [Seller Protection](https://www.paypal.com/jp/legalhub/paypal/seller-protection?locale.x=en_JP), Intangible Goods and delivery proof | Digital delivery evidence can include recorded delivery dates and recipient access. | A stored output hash alone does not establish PayPal acceptance of delivery evidence. |
| Same source, What’s Eligible and Intangible Goods Additional Requirements | PayPal determines eligibility and applies additional requirements to intangible goods. | Successful Sandbox capture does not prove protection eligibility. |
| [Japan Privacy Statement](https://www.paypal.com/jp/legalhub/paypal/privacy-full?locale.x=ja_JP), Overview | The statement describes PayPal processing and distinguishes third-party processing. | PACT cannot adopt PayPal's retention duties as its own without an applicable basis. |

The protection pages state an update date of January 26, 2026.
The privacy page states an update date of September 28, 2026.
These statements establish source content, not legal applicability to every participant.
The seller country JP remains user-reported.
The buyer jurisdiction and PACT operator obligations remain unverified.

## Implementation decision

The current implementation retains evidence and disables deletion.
Existing signed retention dates remain demonstration conditions with an unverified policy basis.
This research does not change those signed agreements or enable automatic deletion.
Permanent retention is not an accepted final policy.

Before enabling deletion, the implementation needs the following evidence:

1. Identify the operator and participant jurisdictions that control the retention policy.
2. Verify applicable dispute, chargeback, and record retention obligations.
3. Record the policy basis and calculate the applicable retention date.
4. Preserve evidence while payment uncertainty, an objection, or a retention hold remains active.
5. Check every transaction reference before deleting a shared image.
6. Audit the deletion decision without exposing credentials or image contents.

The [evidence matrix](g3-g4-evidence-matrix-20261025.md) keeps G4 policy acceptance open.
No additional Sandbox payment or dashboard change is needed for this research.

## Language review

Language review covered source distinctions, conditions, dates, uncertainty, and implementation boundaries.
Exact source titles and URLs retain their required forms.
This review does not claim formal ASD-STE100 compliance.
