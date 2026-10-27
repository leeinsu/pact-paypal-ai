# PayPal AI Hackathon 2026

Contest research checked: 2026-10-19 (KST).

- [PACT design](./PACT.md)
- [Project glossary](./GLOSSARY.md)
- [Source setup guide](./docs/feasibility/clean-start-20261025.md)
- [Submission description](./docs/feasibility/submission-description-draft-20261025.md)
- [Public source repository](https://github.com/leeinsu/pact-paypal-ai)

## Submission summary

PACT lets a buyer and a provider delegate a bounded digital task to separate Personal Agents.
Each Principal signs a Mandate that limits the agent, counterparty, amount, and expiry.
Gemini selects only permitted actions and complete candidates.
Local services validate the decisions, signatures, image conditions, and payment state.
PayPal Sandbox supplies consent, saved payment methods, authorization, capture, void, and readback.

The demonstrated transaction used one fixed-price image task and JPY 1.
The flow rejected an invalid source, accepted a replacement, generated the output, and captured payment after verification.
Both participants downloaded matching output and signed evidence.
The prototype does not support production payments.

The project uses Python, SQLite, OpenCV, NumPy, cryptography, browser WebCrypto, Gemini, and PayPal Sandbox.
The source is available under the [MIT License](./LICENSE).

## Verify the source

Use Linux with Python 3.13, `venv`, and network access for dependency installation.
Run these commands from the repository root:

```sh
python3 -m venv /tmp/pact-review-venv
/tmp/pact-review-venv/bin/python -m pip install \
  -r feasibility/requirements-opencv.txt -r pact/requirements.txt
export PATH="/tmp/pact-review-venv/bin:$PATH"
./verify.sh
```

The suite uses synthetic accounts and synthetic payment responses.
It makes no PayPal or Gemini requests.
The latest fresh-environment run passed 565 tests with zero failures and zero skips.
Follow the [source setup guide](./docs/feasibility/clean-start-20261025.md) to start an empty local HTTPS workspace.

## Current project

PACT connects bounded agents, one signed agreement, image checks, and PayPal Sandbox payment.
The adopted scope permits one buyer, one provider, one linked merchant, JPY, and one negotiated source image.
The [image amendment](docs/feasibility/negotiated-image-contract-20261024.md) replaces semantic background removal with an explicit raster operation.
Agents exchange submission conditions before agreement and request replacement images when preflight fails.
The [source exchange implementation](docs/feasibility/image-exchange-20261025.md) connects provider submissions, browser preflight, and signed agreement.
Request revisions and restarts share three source submissions per transaction.
Local, browser, and [live Gemini checks](docs/feasibility/evidence/image-exchange-gemini-20261025-attempt4.json) passed for this exchange.
The live check used synthetic PayPal responses and made no actual payment request.
A subsequent [combined Sandbox transaction](docs/feasibility/source-exchange-sandbox-20261025.md) passed with source rejection, replacement, real Gemini, and JPY 1 payment.
Both participants downloaded verified output, and repeated execution preserved one payment path.
One integer amount unit represents one yen.
The target flow uses atomic finalization and reservations, separate authorization and capture, payment readback, and immutable output delivery.
The [design](PACT.md), [glossary](GLOSSARY.md), and [GD adoption record](docs/feasibility/gd-reconciliation-20261024.md) define the implementation rules.

Local feasibility code and actual bounded Sandbox experiments exist.
The application implements the core transaction flow. Adopted demonstration acceptance remains incomplete.
Recorded experiments cover saved payment, unattended authorization, capture, void, repeat consent, and response-loss readback recovery.
G1 passed independent agent review within the [bounded Sandbox scope](docs/feasibility/g1-acceptance-20261024.md).
The reviewed evidence includes recorded initial consent for a distinct saved token and its unattended payment.
Production eligibility remains unverified.
G2 passed independent review within the [prepared photographic-panel scope](docs/feasibility/g2-acceptance-20261024.md).
G3 passed independent review within the [bounded transaction safety scope](docs/feasibility/g3-acceptance-20261025.md).
G4 passed independent review within the [bounded Sandbox delivery scope](docs/feasibility/g4-acceptance-20261025.md).
The latest suite passed 565 tests with zero failures and zero skips.
G3 now includes [authenticated image submission and signed agreement routes](docs/feasibility/g3-submission-20261024.md).
Participants can download [consistent evidence packages through HTTP](docs/feasibility/g3-http-records-20261024.md) for offline verification.
The [merchant linkage implementation](docs/feasibility/g3-merchant-linkage-20261024.md) adds session-bound PayPal consent and device-signed registration.
The [buyer linkage implementation](docs/feasibility/g3-buyer-linkage-20261024.md) adds fresh Vault consent and encrypted, device-signed buyer bindings.
The [local HTTPS runtime](docs/feasibility/g3-local-runtime-20261024.md) connects these API services to private persistent state.
The [browser workspace](docs/feasibility/g3-browser-workspace-20261024.md) adds device login, transaction downloads, activity, and emergency stop.
The [browser consent flow](docs/feasibility/g3-browser-consent-20261024.md) adds explicit account review and device-signed buyer or merchant registration.
The [worker command](docs/feasibility/g3-worker-runtime-20261024.md) executes one signed transaction through the same private persistent state.
The browser also registers and revokes device-signed Mandates with one counterparty, JPY limits, and an expiry.
The [local browser check](docs/feasibility/g3-http-browser-20261024.md) verifies device signing, protected cookies, CSRF, stop notices, and logout.
The [application transport check](docs/feasibility/g3-sandbox-readback-20261024.md) verifies existing Sandbox records without new payments.
User-signed Mandates, linked agent proposals, and both agreement signatures connect to the local transaction worker.
`pact.agents.negotiate` connects two Personal Agents through permitted candidates, three signed proposals, and acceptance or rejection.
Decision functions receive candidate data without signing keys. Existing services validate signatures, Mandates, and finalization.
The [Gemini connection](docs/feasibility/g3-gemini-negotiation-20261024.md) adds structured model decisions and a private runtime command.
The same runbook documents `pact.server trade`, which connects negotiation and payment execution through one bounded command.
The operator must prepare permitted candidates and valid Mandates before starting it.
Real Gemini comparison calls verified bounded agreement and rejection with `gemini-3.1-flash-lite`.
Local tests cover this connection through image generation, synthetic payment, and download.
Payment transport, encrypted images, persistent intake, and pre-capture closure also have local tests.
Saved payment tokens and authorization request bodies use encryption with an external key.
Actual seller ownership registration passed within the [revised verification scope](docs/feasibility/merchant-verification-scope-20261024.md).
Actual [buyer Vault consent and signed registration](docs/feasibility/buyer-vault-live-20261025.md) passed through the HTTPS application.
One [complete actual Sandbox transaction](docs/feasibility/integrated-sandbox-20261025.md) passed with real Gemini, signed Mandates, image checks, and JPY 6 payment.
Participant retention holds, signed audit exports, and actual restart downloads passed the [recovery checks](docs/feasibility/retention-recovery-20261025.md).
Participant support requests and restricted operator reviews passed the [support checks](docs/feasibility/support-recovery-20261025.md).
An actual [browser objection review](docs/feasibility/g4-objection-browser-20261025.md) matched existing PayPal records without changing financial tables.
An actual JPY 1 payment survived [worker interruption and query-only recovery](docs/feasibility/integrated-recovery-20261025.md).
The [G3 and G4 evidence matrix](docs/feasibility/g3-g4-evidence-matrix-20261025.md) separates verified behavior from remaining acceptance.
Query-only [objection evidence review](docs/feasibility/g4-objection-evidence-20261025.md) preserves objections and payment state.
Full adopted-product retention closure, physical deletion, shared-reference protection, and external objection outcome linkage remain incomplete.
These conditions must close before real trading. Deletion remains disabled.
The [retention source review](docs/feasibility/retention-policy-basis-20261025.md) explains why deletion remains disabled.
The [JP scope update](docs/feasibility/retention-jp-addendum-20261025.md) records the user-reported operator and participant jurisdictions.
The [G5 clarification](docs/feasibility/g5-delegated-commerce-20261025.md) measures delegated-commerce savings against human-operated transactions.
The [deterministic preflight](docs/feasibility/g5-comparator-preflight-20261025.md) separately limits claims about additional AI contribution.
The [closure plan](docs/feasibility/g1-closure-plan-20261024.md) records current evidence and unresolved conditions.
The [Korean checklist](docs/feasibility/user-checklist.ko.md) describes user tasks without exposing credentials.

Run the local checks from the repository root:

```sh
python3 -m venv /tmp/pact-opencv-venv
/tmp/pact-opencv-venv/bin/python -m pip install -r feasibility/requirements-opencv.txt -r pact/requirements.txt
export PATH="/tmp/pact-opencv-venv/bin:$PATH"
./verify.sh
```

This command runs local tests without PayPal payment requests or a server.
The [source setup guide](docs/feasibility/clean-start-20261025.md) also starts an empty HTTPS workspace with synthetic credentials.
A fresh dependency environment passed all 565 tests and the isolated HTTPS startup check.
Fresh-account commerce setup and public judge access remain unverified.
The [historical OpenCV experiment](docs/feasibility/g2-opencv-experiment-20261024.md) generates experimental cutouts without pretrained weights.
The current negotiated raster implementation uses OpenCV with an independent pixel checker.
The [local runbook](docs/feasibility/negotiated-image-runbook.md) covers request creation, preflight, output generation, and verification.
The standalone image command does not run agent negotiation, persistent intake, or payments.
The application connects those services through the source exchange and existing transaction worker.
The target interface uses one transaction detail view with expandable agreement, checker, and payment evidence.
A private [2:45 review draft](docs/feasibility/demo-recording-runbook-20261025.md) combines actual browser actions, recorded command execution, and labeled retained evidence.
The [actual Gemini command](docs/feasibility/evidence/single-command-live-gemini-20261025.json) used synthetic PayPal responses and made no additional payment.
The public source repository and MIT License are available for review.
The demonstration exports evidence without Disputes API submission.

The historical contest research below retains its 2026-10-19 reference date.
GD reconciliation does not revalidate contest eligibility, dates, prizes, or judging claims.

목표 부문은 `Best Use of Agentic Commerce`, `Best Use of PayPal + AI`, `Most Creative`이다.

- 공식 페이지: https://paypalaihackathon.devpost.com/
- 공식 규정: https://paypalaihackathon.devpost.com/rules
- 공식 자료: https://paypalaihackathon.devpost.com/resources
- PayPal 공식 안내: https://developer.paypal.com/community/blog/PayPal_AI_Hackathon/

## 한눈에 보기

PayPal과 AI를 모두 의미 있게 사용하는 온라인 해커톤이다. 지정 문제나 필수 트랙은 없다. 개인, 팀, 법인이 참가할 수 있다.

한국 거주자는 공식 제외 지역에 포함되지 않으므로, 거주지의 성년 연령 이상이고 이해 충돌 등 다른 제외 사유가 없다면 참가할 수 있다. 최종 자격 판단은 공식 규정을 기준으로 한다.

| 항목 | 내용 |
| --- | --- |
| 접수 기간 | 2026-10-01 09:15 PT ~ 2026-11-12 12:00 PST |
| 한국시간 마감 | **2026-11-13 05:00 KST** |
| 심사 기간 | 2026-12-01 ~ 2026-12-15 PT |
| 수상 발표 | 2026-12-21 예정 |
| 방식 | 온라인, 공개 |
| 핵심 요건 | PayPal 개발 플랫폼과 AI를 모두 의미 있게 사용 |
| 현금 상금 | 총 $67,500 |
| 기타 상금 | Render 크레딧 $2,250, 일부 구독 혜택 |

공식 페이지의 `$69,750` 표기는 현금 $67,500과 Render 크레딧 $2,250을 합한 금액으로 보인다. 규정의 개별 상금표를 우선 기준으로 삼는다.

## 참가 자격

- 거주지 기준 성년인 개인, 자격 있는 개인으로 구성된 팀, 또는 적법하게 설립된 법인이 참가할 수 있다.
- 팀 인원 제한은 없다. 팀은 제출 대표자 한 명을 지정해야 한다.
- 한 사람이 여러 팀에 참여하거나 개인 출품을 병행할 수 있다.
- 브라질, 퀘벡, 러시아, 크림반도, 쿠바, 이란, 북한과 미국의 포괄적 제재 지역 등은 제외된다.
- PayPal 또는 Devpost 등 대회 운영 관련자, 심사위원과 그 고용 조직, 이해 충돌이 있는 참가자는 제외될 수 있다.

출처: [Official Rules §3](https://paypalaihackathon.devpost.com/rules), [FAQ](https://paypalaihackathon.devpost.com/details/faqs)

## 만들어야 하는 것

새 앱을 만들거나 기존 앱을 의미 있게 개선해야 한다.

필수 조건:

- 무료 PayPal sandbox를 사용해 PayPal 기술, API, SDK, 제품 또는 개발 기능을 하나 이상 핵심 기능에 통합한다.
- AI 도구, 모델 또는 플랫폼을 사용자 경험이나 기능에 의미 있게 통합한다.
- 실제로 작동하는 프로토타입 또는 PoC를 제공한다.
- 심사위원이 이해하고 실행할 수 있도록 문서화한다.
- 기존 프로젝트라면 접수 기간 중의 중요한 개선 사항을 설명한다.

스폰서 도구는 선택 사항이다. AG Grid, APIMatic, Astropods, Bryntum, Channel3, Elastic, KERNEL, Postman, Render, Zapier를 사용할 수 있다.

## 제출 체크리스트

- [ ] Devpost에서 `Join Hackathon`으로 참가 등록
- [x] 기능과 사용 방법을 설명하는 영문 프로젝트 소개
- [x] 실행 가능한 데모
- [x] 호스팅 URL 또는 저장소의 완전한 설치·실행 절차
- [x] GitHub, GitLab 또는 Bitbucket의 공개 저장소
- [x] 저장소 최상단에서 확인 가능한 오픈소스 라이선스
- [x] 실행에 필요한 소스, 에셋, 설명 포함
- [x] 사용한 AI 모델·서비스와 사용 방식을 명시
- [x] 실제 작동 화면을 담은 **3분 미만** 영상
- [ ] 영상을 공개 YouTube 영상으로 업로드하고 제출 폼에 연결
- [x] 허가받지 않은 상표, 음악, 저작물을 영상에서 제외
- [ ] 심사 종료일까지 무료 테스트 접근 유지
- [ ] 비공개 데모라면 테스트 계정과 접근 절차 제공
- [ ] 실제 비밀 키는 공개 저장소에 넣지 않고, 심사용 sandbox 자격 증명을 안전한 방식으로 전달

출처: [Overview: What to Submit](https://paypalaihackathon.devpost.com/#requirements), [Official Rules §4](https://paypalaihackathon.devpost.com/rules)

## 심사 기준

1차 심사는 주제 적합성과 필수 API/SDK 사용을 통과/탈락으로 판단한다. 통과작은 아래 다섯 항목을 같은 비중으로 평가받는다.

1. 기술 구현: PayPal 개발 플랫폼과 AI를 깊이 있고 능숙하게 사용했는가?
2. 디자인: 단순 기술 데모가 아니라 완결된 제품 경험인가?
3. 잠재 영향: 실제 사용자의 구체적 문제를 신뢰할 수 있게 해결하는가?
4. 혁신성: 기존 개념과 구분되는 새 아이디어인가?
5. 발표: 영상이 전체 흐름을 명확히 보여 주고 문제, 대상, 가치를 설명하는가?

동점이면 위 순서대로 점수를 비교한다. 따라서 기술 구현이 첫 번째 동점 결정 요소다.

출처: [Official Rules §6](https://paypalaihackathon.devpost.com/rules)

## 상금

- 종합: 1위 $12,000, 2위 $8,000, 3위 $5,000
- 특별상 각 $5,000: Most Creative, Most Impactful, Best Demo Delivery, Best Use of PayPal + AI, Best Use of Agentic Commerce
- AG Grid: 1위 $5,000, 2위 $2,000, 공동 3위 3팀 각 $1,000
- APIMatic: 3팀 각 $1,000와 6개월 Business 구독
- Bryntum: 3팀 각 $1,000
- Channel3: 1팀 $1,500
- Render: $1,000 / $750 / $500 상당 크레딧

한 프로젝트는 종합상 또는 특별상 중 하나와 스폰서상 하나를 함께 받을 수 있다.

출처: [Official Rules §8](https://paypalaihackathon.devpost.com/rules)

## 공식 기술 자료

- [PayPal REST API 시작하기](https://developer.paypal.com/api/rest/): OAuth 2.0, sandbox 계정, Orders, Payments, Subscriptions, Invoicing, Disputes
- [PayPal AI Toolkit](https://github.com/paypal/AI-Toolkit): Codex 플러그인, PayPal 개발 모범 사례, sandbox MCP 서버
- [PayPal JavaScript SDK](https://developer.paypal.com/sdk/js/)
- [PayPal API Explorer](https://developer.paypal.com/api/rest/)
- [대회 자료 모음](https://paypalaihackathon.devpost.com/resources)
- [PayPal Discord](https://discord.gg/paypaldev)

PayPal AI Toolkit의 sandbox MCP는 주문·결제, 환불, 청구서, 구독, 분쟁, 카탈로그, 배송, 거래 보고 기능을 제공한다. Codex에서도 공식 플러그인을 사용할 수 있다. 액세스 토큰은 만료되므로 저장소에 고정하지 않는다.

## 1차 전략 가설

- 결제는 장식이 아니라 핵심 행동이어야 한다. AI가 추천만 하고 일반 Checkout으로 끝나는 구조는 `meaningfully use` 기준에서 약할 수 있다.
- 가장 작은 경쟁력 있는 범위는 한 사용자군, 한 문제, 한 PayPal 거래 흐름, 한 AI 판단 흐름이다.
- 영상만 보고도 평가할 수 있으므로 3분 안에 문제 → AI 판단 → PayPal sandbox 거래 → 결과를 한 번에 보여 주는 설계가 유리하다.
- 스폰서 도구는 제품에 꼭 필요할 때만 추가한다. 상금 트랙을 늘리기 위한 통합은 완성도와 설명 시간을 해칠 수 있다.
- 돈을 움직이는 AI라면 사전에 정한 금액 한도, 취소 가능한 위임, 자동 검사와 검증 가능한 거래 기록이 필요하다. PACT는 이 범위 안에서 거래별 사용자 확인 없이 실행한다.

## Next implementation conditions

1. Preserve the accepted G1 scope and its query-only recovery restrictions.
2. Preserve the accepted G2 implementation, evidence, and prepared photographic-panel scope.
3. Use the GD adoption record and bounded G1 and G2 acceptances for transaction safety implementation.
4. Verify G3 concurrency, ownership, stop, expiry, replay, and restart conditions.
5. Verify output delivery recovery before preparing the complete demonstration.

## 확인이 더 필요한 사항

- 참가자 본인의 연령, 고용 관계, 이해 충돌에 따른 최종 자격
- 한국 계정에서 사용할 수 있는 PayPal sandbox 기능과 선택 API의 제한
- 아이디어 확정 후 필요한 스폰서 도구의 무료 크레딧과 세부 상금 요건
- 세금, 상금 수령 방식, 팀 내 배분 방식

