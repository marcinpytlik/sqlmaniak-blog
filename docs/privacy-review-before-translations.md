# Privacy notice: legal and operational review before EN/DE publication

Scope: SQLManiak blog at https://sqlmaniak.blog. This is a technical/content review checklist, **not legal advice or a completed GDPR assessment**.

## Existing Polish source
- `content/polityka-prywatnosci.md` contains an explicit pending-review note in section 1: the controller status must be verified legally and organizationally, particularly for GA4 and service providers.
- It distinguishes possible responsibility of Marcin Pytlik and Pracownia IT Joanny i Marcina Pytlik Sp. z o.o. for different purposes. The legal roles are **not yet established conclusively** by the source document.
- It describes GitHub Pages, Formspree, Google Analytics 4, possible transfers outside the EEA, consent stored in the browser, and contact-message retention.
- It currently states GA4 retention as two months and a 30-day mail-inbox process. Verify these claims against actual settings, service contracts and workflows.
- The English and German footers and contact forms explicitly link to the Polish notice and indicate its language; they do not suggest a reviewed EN/DE legal notice exists.

## Required confirmation before publishing translated policies
1. Verify controller(s), company names, contact address, and roles for contact forms, analytics and contracts.
2. Review actual Formspree account configuration and agreements, message handling, retention and international transfers.
3. Verify GA4 consent implementation, events, retention, Google agreements, and actual storage/processing settings.
4. Confirm hosting, cookie/local storage disclosures, transfers, retention and the rights-exercise procedure.
5. Obtain legal/organizational approval for the corrected Polish notice.
6. Only then create faithful reviewed English and German translations, preserving links and accurate terminology.
7. Add real translated pages, legal-review date, reciprocal `hreflang` and localized footer links.
8. Test the three notices and contact forms in CI, and independently test the live contact form with the owner's authorization.

## Current delivery
The EN/DE About, Contact and Services pages can be tested and reviewed without claiming a finalized translated privacy notice. Contact submissions still use the existing Formspree endpoint. No new external processor is introduced in this change.
