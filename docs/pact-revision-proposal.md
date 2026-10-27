# PACT 설계 수정안

Status: **Adopted design baseline through GD on 2026-10-24**.
Original proposal date: 2026-10-20.
The user requested GD execution after reviewing the reconciliation preparation.
The [adoption record](feasibility/gd-reconciliation-20261024.md) identifies reconciled documents and ADR dispositions.
Adoption does not establish G1, G2, or implementation success.

The user adopted the [negotiated image amendment](feasibility/negotiated-image-contract-20261024.md) on 2026-10-24.
That amendment supersedes semantic background removal and section 7 under the explicit raster contract.
입력: [최초 적대적 평가 21/50](reviews/pact-initial-review.md). R1~R13은 그 평가의 고정 ID다. 이번 보완은 [설계 완성도 재평가](reviews/pact-design-completeness-review.md)의 D1~D5를 반영한다.
The original proposal recorded all implementation and experiment gates as unexecuted.
The current gate table in section 10 replaces that historical status.
Document adoption does not increase a design score or prove a feature works.

Currency decision: The user adopted JPY instead of USD for this design.
One integer amount unit represents one yen.
The sandbox preparation amount remains JPY 5000 without conversion or multiplication by 100.
The currency decision alone did not authorize external execution or complete GD.
The adoption record now documents the broader reconciliation.

## 1. 좁힌 주장과 범위

**제안:** 두 사용자가 한 번 정한 제한 안에서 에이전트가 같은 조건에 합의한다. 짧은 이미지 작업의 완료 조건을 검사한 뒤 PayPal sandbox 지급을 실행한다. 사용자에게 결과 파일과 연결된 증거를 제공한다.

- The scope permits one buyer, one provider, one previously linked PayPal merchant account, JPY, and one image.
- 양측 위임, 동일 합의, 자동 검사, 최초 동의 이후 무인 승인·지급, 증거 연결을 유지한다.
- 서버 하나와 SQLite의 단일 쓰기 트랜잭션으로 상태·한도·기록 순서를 관리한다. 지급 작업자도 하나다.
- 서명 검증은 양측에서 할 수 있다. PayPal 상태 조회와 결제 계정 연결에는 PACT 서버를 신뢰한다.
- 장터, 다중 판매자 온보딩, 범용 작업 규칙, 새 결제망, 자동 분쟁 제출은 이번 구현에 넣지 않는다.
- 사용자별 서명 열쇠와 에이전트 열쇠를 분리한다. 복구 열쇠 기능은 기존 ADR대로 남기되 핵심 시연 경로에 넣지 않는다.

**확인된 사실:** 기존 문서는 무인 결제 방식과 검사 정확성을 미확인으로 적고 있다. 공식 PayPal 문서는 저장 결제수단과 멱등성을 설명한다. 이는 선택한 계정의 사용 권한이나 API 조합의 성공을 입증하지 않는다. [저장 결제수단](https://developer.paypal.com/platforms/checkout/save-payment-methods/), [멱등성](https://developer.paypal.com/api/rest/reference/idempotency/)

## 2. 고객과 가치 가설 — R8

The [2026-10-25 clarification](feasibility/g5-delegated-commerce-20261025.md) defines human intervention across delegated commerce rather than objections.

**미검증 가설:** 동일한 외부 작업 제공자에게 상품 사진을 반복 의뢰하는 소규모 판매자는 건별 가격·조건 확인과 불량 결과의 지급 확인을 줄일 필요가 있다. 독립된 제공자에게 일을 맡기는 경우를 대상으로 한다.

비교 대상은 같은 모델의 직접 호출, 사람의 검사 후 지급, 고정 규칙에 따른 자동 지급이다. PACT도 같은 모델·입력·제공자·가격 범위를 사용한다. 제공자가 필요 없는 직접 호출이 더 낫다면 그 결과를 보고한다. 자동 지급 비교군은 §9에서 정한다.

대상 사용자 3명에게 최근 의뢰 과정과 실패 사례를 확인한다. 각 사용자가 최근 연속 20건의 실제 의뢰 입력을 제공하면 총 60건을 조사한다. 보기 좋은 단색 사진만 고르거나 실패 표본을 빼지 않는다. 자료 제공 동의를 받고 사용자별 선정 기간과 누락 이유를 기록한다. 자료가 부족하면 결과를 미확정으로 남긴다.
검사기와 지원 범위를 G2에서 고정한 뒤 이 60건에 적용한다. 평가 담당자는 검사기 판정과 별도로 지원 조건 충족 여부를 판정한다. 전체 의뢰 중 지원 가능하고 입력 검사를 통과한 비율을 적용률로 기록한다. G2의 제한된 품질 평가와 G5의 고객 적용률은 서로 대신할 수 없다.
지원되는 입력 중 시간순 첫 10건을 각 흐름으로 처리한다. 사람의 개입 횟수·시간, 전체 소요 시간, 제공자 요금·모델·검사·결제 비용, 정상 결과 거부 수, 불량 결과 지급 수를 기록한다. 공통 비용도 포함한다. 초기 설정 시간과 건별 시간은 따로 보고한다.

아래 수치는 **실험 전에 정할 초기 판단 기준이며 실증값이 아니다.** 변경 시 변경 이유와 날짜를 기록하고 새 표본으로 평가한다.

| 판단 대상 | 최초 기각 기준 | 수치를 선택한 이유 |
| --- | --- | --- |
| 고객 문제 | 3명 중 2명 이상이 최근 반복 확인 부담과 구체적 실패 사례를 제시하지 못함 | 소수 조사에서 문제의 반복 여부부터 확인 |
| 적용률 | 60건 중 지원 가능하고 입력 검사를 통과한 건이 60% 미만 | 대부분의 실제 의뢰를 다루지 못하면 좁힌 작업 가설을 재검토 |
| 사람의 시간 | 사람 검사·지급 흐름 대비 건별 개입 시간의 중앙값을 50% 이상 줄이지 못함 | 초기 설정을 요구할 만큼 큰 절약을 목표로 설정 |
| 시간·비용 | 같은 비교군보다 전체 시간 중앙값이 20% 초과 증가하거나 건별 비용 중앙값이 10% 초과 증가 | 개입 감소를 위해 감수할 초기 증가 한도 |
| 설정 부담 | 구매자와 제공자의 합산 설정 시간이 30분 초과이거나 100건 내에 회수되지 않음 | 짧은 작업의 반복 사용에 맞춘 초기 한도 |

설정 회수 건수는 추가 설정 시간을 건별 평균 개입 절약 시간으로 나눈 값이다. 절약 시간이 0 이하이면 회수 불가다. 기존 결제 설정 시간 등 모든 흐름에 공통인 부담과 PACT 추가 부담을 분리해 공개한다.
후속 정상 거래의 추가 승인 0회와 불량 지급 0회는 안전 목표다. 이 목표만으로 고객 가치를 인정하지 않는다. 기각 기준 하나라도 해당하면 현재 고객·작업 가설을 재검토한다. 표본이 작은 조사 결과를 시장 전체의 수요나 절약률로 일반화하지 않는다.

Source preparation and resubmission costs count toward the customer comparison under the negotiated image amendment.
Measure both parties' preparation time, rejected submissions, and additional image requests.
Do not select only sources already compatible with the raster rule.
Report whether reduced transaction checks compensate for the provider's preparation burden.

## 3. 선행 게이트 G1: 실제 무인 결제 — R1

화면 전체를 만들기 전에 구매자 sandbox 계정과 단일 판매자 sandbox 앱으로 아래 실험만 수행한다.

1. 사용자가 최초 저장·후속 결제 동의 절차를 완료한다. 선택한 제품명, API 문서 URL, 앱 기능·권한, 판매자 식별값을 기록한다.
2. 동의 결과로 받은 토큰 유형·저장 범위·구매자 연결을 기록한다. 비밀 토큰 값은 공개 증거에 넣지 않는다.
3. 새 브라우저 승인 없이 해당 토큰으로 후속 주문을 만들고 승인한 뒤 별도로 결제를 실행한다.
4. 사용한 요청의 경로·필드·멱등성 지원 여부·보관 기간, 응답 상태, 주문·승인·결제 ID를 비밀 제거 후 보관한다.
5. 선택한 API에서 각 단계 조회와 승인 취소가 가능한지 확인한다. 후속 조회의 금액·통화·수취인이 합의와 일치하는지 확인한다.

정확한 API와 필드는 이 실험에서 공식 문서와 실제 계정 응답으로 확정한다. 저장 토큰만 있으면 임의 판매자에게 지급할 수 있다고 가정하지 않는다.
**통과:** 최초 동의 녹화와 후속 추가 클릭 0회인 승인·결제·조회 기록을 연결할 수 있다.
**실패:** 핵심 무인 거래는 미구현으로 표시하고 통합을 중단한다. 거래별 Checkout 승인이나 모의 결제를 성공한 무인 결제로 대체하지 않는다. 다른 결제 방식으로 전환하려면 별도 설계 결정이 필요하다.

## 4. 서명·계정·파일 결속 — R4

최종 합의의 정확한 바이트열을 두 에이전트가 서명한다. 고정 필드와 정해진 직렬화 형식을 사용한다. 검증자는 재구성한 바이트열과 서명을 확인한다.
Amounts are integers in JPY yen.
The validator checks strings, ranges, times, and file sizes at input boundaries.
The validator treats structured AI output as untrusted input.

| 객체 | 서명 또는 확인값으로 묶을 내용 |
| --- | --- |
| 양측 위임 | User and agent public keys, permitted roles, counterparties, tasks, JPY transaction and period limits, duration, expiry, and revocation identifier |
| 최종 합의 | 거래 ID, 양측 위임 해시, 역할, 금액·통화, 지급 계정 연결 ID·판, 판매자 ID, 입력 파일 해시, 규칙서 해시·판, 기한, 재작업·중단·인도 조건, 보관 종료일 |
| 결과·검사 | 합의 해시, 제출 순번, 입력·출력 해시, 검사기 판·규칙서 해시, 항목별 수치·결과, 검사 시각 |
| 지급 작업 | 거래·합의 해시, 잠긴 검사 결과·출력 해시, 서버의 계정 연결 ID, 실제 요청 금액·통화·수취인, 단계별 요청 ID |
| 결제 영수증 | 앞선 결속과 주문·승인·결제 ID, 서버 조회 시각·상태, PACT 서버 서명 |

계정 연결은 최초 동의 세션의 로그인 사용자와 서버가 얻은 저장 토큰·구매자 식별값을 묶은 불변 판의 내부 기록이다. 판매자 등록도 제공자 Principal과 고정 판매자 ID를 묶는다. 에이전트가 토큰이나 판매자 ID를 임의 지정하지 못한다.
확정과 지급 제출 직전에 `구매자 Principal = 계정 연결 소유자`, `제공자 Principal = 등록 판매자 소유자`를 검사한다. 양측 에이전트 서명 열쇠가 해당 Principal의 위임에 속하는지, 합의가 참조한 계정 연결 판과 실제 요청의 토큰·판매자 설정이 같은지도 대조한다. 불일치하면 외부 호출 전에 거부한다.
PayPal 응답에서 확인 가능한 지급자·수취인·금액·통화를 대조한다. 토큰만 제공되어 구매자 식별값을 직접 대조할 수 없다면 G1에 그 한계와 동의 세션에 의존하는 연결을 기록한다.
같은 거래 ID의 다른 합의 해시를 거부한다. 합의 해시와 PayPal 주문 ID도 각각 중복 등록하지 않는다. 결제 전후 출력 파일은 해시를 이름으로 한 변경 불가 파일로 보관하며 최신 URL 내용으로 바꾸지 않는다.

**앱 인증과 객체 권한:** Principal은 [용어집](../GLOSSARY.md)의 위임 주체다. 앱 세션은 그 Principal의 요청임을 확인하는 로그인 상태이며 거래 위임을 대신하지 않는다.
최소 로그인 절차는 다음과 같다.

1. 서버는 로그인 시작 브라우저에 묶인 요청을 발급한다. 요청에는 서비스 주소, 목적, 일회용 난수와 5분 만료 시각을 넣는다.
2. 사용자는 기기에서 사용자 서명 열쇠로 요청에 서명한다.
3. 서버는 서명·주소·목적·만료·난수의 미사용 여부와 시작 브라우저 연결을 확인한다. 성공하면 난수를 소비한다.
4. 최초 등록에서는 검증된 공개 열쇠에 새 내부 Principal ID를 연결한다. 기존 로그인에서는 등록된 연결을 조회한다. 요청자가 보낸 Principal ID를 신뢰하지 않는다.

사용자 비밀 열쇠는 기기 밖으로 내보내지 않는다. 서버는 브라우저가 로그인 상태를 제시하는 세션 쿠키를 발급한다. HTTPS의 HttpOnly·Secure·SameSite 속성을 적용한다. 상태 변경 요청에는 세션에 묶인 위조 요청 방지값도 확인한다. 로그아웃·세션 만료 시 권한을 폐기한다. 로그인 상실을 이유로 운영자가 Principal 연결을 임의 변경하지 않는다.
계정 등록·변경은 현재 세션과 해당 동작·대상을 묶은 새 사용자 서명을 요구한다. 서버는 로그인과 같은 방식으로 일회용 난수·5분 만료·시작 브라우저를 확인한다. PayPal 동의 시작·복귀는 같은 세션의 일회용 상태값으로 연결한다. 서버가 얻은 계정 정보만 저장한다. 변경은 새 판을 만들며 기존 합의의 연결 판을 바꾸지 않는다. 이전 판을 사용할 수 없으면 기존 거래를 조회·보류하고 새 계정으로 대신 지급하지 않는다.

| 요청 | 허용 주체와 객체 범위 |
| --- | --- |
| 구매 결제수단 등록·변경 | 해당 구매자 Principal의 세션과 새 사용자 서명. 에이전트와 운영자는 대행 불가 |
| 판매자 등록·변경 | 해당 제공자 Principal의 세션과 새 사용자 서명. 판매자 계정 확인 절차는 G1에서 확정 |
| 입력·결과 파일 읽기 | 구매자는 자기 입력과 지급 확인된 결과. 제공자는 확정된 자기 거래의 작업 입력과 제출 결과. 비당사자는 거부 |
| 거래 기록·증거 내보내기 | 해당 거래의 양측 Principal. 결제 토큰·상대의 비공개 계정 자료는 제외 |
| 긴급 정지 | 당사자 세션이 자기 Principal 또는 자신이 참여한 거래에 요청. 자기 사용자 열쇠를 잃어도 유효 세션에서는 정지 가능. 상대의 다른 거래는 변경 불가 |
| 운영자 조회·확인 | 사전에 등록한 별도 운영자 계정. §6 지원 건의 결제 식별값·상태·감사 기록만 조회. 일반 파일 다운로드·계정 연결 변경·새 지급은 불가 |

운영 주체는 지원 담당자의 별도 공개 열쇠를 사전에 등록한다. 운영자도 같은 로그인 절차를 거치며 일반 사용자 등록으로 운영자 권한을 얻을 수 없다.
서버는 요청마다 세션의 Principal과 대상 객체의 소유자·거래 당사자·현재 상태를 대조한다. 객체 ID를 아는 것만으로 권한을 주지 않는다. 에이전트 요청도 서명과 위임 범위를 확인하며 사용자·운영자 권한으로 승격하지 않는다.
서버 파일 암호화 열쇠는 PACT 운영 주체가 서버의 별도 비밀 설정으로 보관한다. DB·파일 저장소·공개 저장소에 함께 기록하지 않는다. 사용자 서명 열쇠나 사용자 백업 열쇠와 다르다. 서버 프로세스는 파일 처리에 필요한 복호화 권한을 갖는다. 따라서 호스트 관리자에 대한 비밀성까지 보장하지 않는다. 일반 운영자 지원 화면에는 이 열쇠를 제공하지 않는다.

**신뢰 한계:** PayPal ID를 서명에 넣어도 PayPal이 그 합의를 확인했다는 뜻은 아니다. 서버 서명은 서버의 진술을 증명한다. 제3자가 독립 검증할 PayPal 서명 증명이나 지급자 계정 소유권의 암호학적 증명은 제공하지 않는다.
서명된 기록의 변조는 비교할 수 있지만 악성 PACT 서버의 허위 PayPal 조회 결과나 모든 당사자에게 일관된 거짓말까지 막는다고 주장하지 않는다.

## 5. 확정·한도·취소의 원자성 — R2·R5

양쪽 서명은 확정 요청의 전제다. **최종 확정 효력은 기록 서버의 확정 트랜잭션 커밋에서 발생한다.** 벽시계나 마지막 서명 시각으로 순서를 정하지 않는다.
같은 DB 트랜잭션에서 양쪽 서명·위임·만료·긴급 정지를 검사하고, 양쪽 기간 한도를 검사·예약하고, 거래와 순번을 기록한다. 모두 성공하거나 모두 취소한다.
서명은 됐으나 기록에 확정되지 않은 합의는 이행·결제를 시작하지 않는다. 서버 기록을 못 읽으면 확정하지 않는다.

- 위임 취소도 같은 DB 쓰기 순서에 넣는다. 취소가 먼저 커밋되면 확정 요청을 거부한다. 확정이 먼저면 위임 취소가 기존 거래를 지우지 않는다.
- 각 위임의 고정 기간별로 `소비액 + 예약액 + 신규 금액 ≤ 기간 한도`를 확인한다. 새 기간으로 넘어가도 기존 거래 예약을 옮기지 않는다.
- 확정 시 양측 한도를 예약한다. 지급 완료 확인 시 예약액을 소비액으로 한 번만 이동한다. 제공자 측 한도도 체결 금액의 총량 제한으로 해석한다.
- 지급 가능성이 없는 상태가 확정돼야 해제한다. 미승인 종료, 확인된 승인 취소·만료가 예다. 단순 로컬 기한 경과·통신 오류만으로 해제하지 않는다.
- 지급 상태가 불명이면 한도를 계속 예약한다. 후속 거래가 막힐 수 있음을 화면에 표시한다. 환불이 생겨도 이번 기간의 소비액을 자동 복원하지 않는다.

With a JPY 10 limit, concurrent JPY 6 agreements must finalize exactly one agreement.
If either Mandate check fails, neither reservation may remain.
공개 요약에는 순번·종류·확인값만 넣는다. 양측은 서명 영수증과 동일 증거 묶음을 각각 보관한다. 이는 단일 서버의 가용성·공모·기록 분기를 해결하는 합의망이 아니다.

## 6. 지급 상태·응답 유실·긴급 정지 — R3·R5·R6

정상 경로는 `협상 → 확정·예약 → 승인 → 작업 → 검사 통과 → 지급 제출 → 지급 확인 → 결과 접근 가능`이다.
별도 상태는 `검사 실패`, `중단 처리 중`, `지급 상태 확인 중`, `지급 실패`, `정지`, `결제 완료·전달 재시도`다.

결제 외부 호출 전에 단계별 고정 요청 ID와 불변 요청 내용을 DB에 저장한다. 주문 생성·승인·결제는 서로 다른 요청 ID를 쓴다.
재시작하면 미완료 작업을 읽고 알려진 외부 ID로 먼저 조회한다. G1에서 지원이 확인된 경우에만 같은 요청 ID·같은 내용으로 재시도한다. 새 주문·승인으로 우회하지 않는다.
응답 ID조차 못 받은 작업은 지원되는 멱등 재시도 또는 조회 방법으로만 복구한다. 보관 기간을 넘겼거나 중복 여부를 확인할 수 없으면 `지급 상태 확인 중`으로 멈춘다. 아래 운영 절차에서 지급 불가능을 확인하기 전 한도를 해제하지 않는다.
승인·결제가 `PENDING`이거나 결과가 불명이면 다음 단계로 가지 않는다. 결제 완료는 G1에서 정한 최종 성공 상태를 서버 조회로 확인한다. 자동 확인이 불가능하면 아래 수동 확인 절차만 예외로 허용한다.

**긴급 정지와 지급 제출의 경계:** 지급 작업자가 같은 DB 쓰기 트랜잭션에서 정지·기한·검사 결과·§4의 계정 소유와 위임 연결을 재확인하고 `지급 제출` 기록을 커밋한다. 이 커밋이 이번 구현의 지급 발송 확정점이다.
합의 기한은 지급 제출 커밋 전까지 효력이 있다. 커밋 시 서버 시각이 합의 기한 이상이면 지급 제출을 거부한다. 정지가 먼저 커밋되면 지급 제출과 발송을 금지한다. 지급 제출이 먼저면 이후의 합의 기한 경과나 정지는 이미 확정된 지급 의도를 취소하지 않는다. HTTP 발송 전 종료됐더라도 재시작 후 같은 작업·요청 ID로 발송·조회·지원되는 재시도를 수행해 결과를 확정한다. 새 작업이나 새 요청 ID를 만들지 않는다.
DB 커밋과 PayPal 수신을 하나의 원자적 동작으로 만들 수 없다. 멱등 보관 기간을 넘겼거나 결과를 확인할 수 없으면 앞서 정한 보류 규칙을 따른다.
화면은 후자의 경우 “정지 접수: 이미 확정된 지급 요청은 취소되지 않으며 처리를 계속합니다”와 현재 조회 상태를 표시한다. 그 밖의 새 지급 작업·새 증거 제출은 금지한다.
승인이 남았고 지급 제출이 커밋되지 않았으면 G1에서 확인한 승인 취소를 요청한다. 지급이 확인되면 이미 지급됐다고 알리고 자동 환불을 주장하지 않는다.

PayPal 결제 승인의 만료는 합의 기한과 별개다. 지급 제출 뒤 승인이 만료되어도 로컬 시각만으로 실패를 확정하지 않는다. 기존 지급의 성공·진행 여부를 조회한다. G1에서 정한 증거로 미지급과 기존 경로의 지급 불가능을 모두 확인하면 `지급 실패`로 바꾸고 예약을 해제한다. 새 승인을 만들지 않는다. 확인이 부족하면 `지급 상태 확인 중`을 유지한다.

상태 처리기는 지급 작업자 안에서 근거와 허용 전이를 검사해 DB 상태·예약액을 함께 바꾸는 부분이다. 별도 서비스가 아니다.

**장기 미확정 지급의 운영 절차:** PACT 운영 주체가 지정한 지원 담당자가 처리한다. 사용자 화면은 거래 번호, 예약액, 마지막 확인 시각, 미확정 이유와 `지원 요청`을 표시한다. 사용자는 앱에서 자기 거래에 문의를 등록하고 답변·이의 제기를 같은 기록에 남긴다. 결제 비밀값이나 서명 열쇠를 제출하지 않는다.
지급 작업자가 자동 복구 불가를 확인하면 즉시 지원 건을 연다. 담당자는 1영업일 이내에 접수 여부와 다음 확인 예정 시각을 기록하는 것을 초기 운영 목표로 삼는다. 이는 PayPal 처리 시간이나 해결 기한의 보장이 아니다. 상태가 같아도 사용자 화면에서 마지막 확인과 다음 확인 예정 시각을 볼 수 있게 한다.
허용 증거는 서버가 인증된 API로 조회한 거래 상태와, 담당자가 공식 판매자 계정 또는 PayPal 지원 경로에서 직접 확인한 기록이다. 후자는 계정·금액·통화·외부 ID 또는 요청 ID로 해당 지급에 연결돼야 한다. G1에서 수동 확인에 필요한 최종 상태와 증거 항목을 정하며, 모든 항목을 확인한 경우에만 종결을 허용한다. 사용자의 캡처 화면, 잔액 변화, 검색 결과 없음만으로 상태를 확정하지 않는다. G1에서 해당 API의 최종 상태와 확인 수단을 정하지 못하면 수동 종결도 허용하지 않는다.

| 확인 결과 | 담당자와 시스템의 허용 행동 |
| --- | --- |
| 해당 지급 완료 확인 | 담당자가 근거를 등록. 상태 처리기가 연결값을 검사한 뒤 예약을 소비액으로 한 번만 이동하고 결과 접근을 복구 |
| 미지급이며 기존 경로의 지급 불가능 확인 | 담당자가 두 조건의 근거를 등록. 상태 처리기가 검증한 뒤 지급 실패와 예약 해제를 함께 기록 |
| 확인 불가·충돌·연결값 부족 | 상태와 예약 유지. 새 지급·추정 성공·임의 해제 금지. 영구 미확정도 가능한 결과로 안내 |

상태 처리기는 거래 연결값·필수 증거 항목·현재 상태·허용 전이를 자동 대조한다. 공식 계정 화면이나 지원 답변의 진위·내용 해석은 담당자의 확인에 의존한다. 이 수동 확인은 PACT 운영 주체를 신뢰하는 절차이며 독립적인 PayPal 서명 증명이 아니다.
운영자는 근거 없는 상태 덮어쓰기나 잔액 수정을 할 수 없다. 상태 처리기는 등록된 증거와 허용 전이만 적용하며 지급을 새로 생성하지 않는다. 확인 불가 건에서 담당자가 문의에 답했더라도 거래는 종결하지 않는다.
감사 기록은 담당자, 확인 시각, 증거 출처·확인값, 변경 전후 상태·예약액, 판단 이유를 남긴다. 비밀을 제거한 판단 근거는 거래 당사자가 볼 수 있다. 이의 제기가 오면 같은 건에 추가 증거를 연결해 재검토한다. 근거가 충돌하면 추가 상태 변경을 멈추고 불명 사실을 표시한다. 미확정·이의 제기 중에는 관련 증거의 삭제를 정지한다.

## 7. Negotiated image submission and independent G2 evaluation — R9

The user adopted the [negotiated image contract](feasibility/negotiated-image-contract-20261024.md) on 2026-10-24.
The buyer agent sends dimensions, background RGB, and the complete fixed rule with its proposal.
The provider agent submits a compatible source image or proposes supported alternatives within both Mandates.
The server checks the exact source before final agreement, reservations, or payment authorization.
Unsupported or uncertain inputs require resubmission.
Three failed source submissions close the negotiation without payment.
The server persists submission counts across request revisions and restarts under the same negotiation identity.
The existing three-proposal limit remains unchanged.

The final agreement binds the request hash, source hash, rule identifier, rule hash, dimensions, and region counts.
Any request or source change requires new preflight before agreement.
The provider cannot substitute source bytes after finalization.
The existing authorization, output custody, checker, capture, and recovery requirements remain mandatory.

The service performs an explicit raster operation rather than semantic product recognition.
The rule removes perimeter-connected pixels within RGB distance 8 of the requested background color.
It preserves every other pixel, which must have distance at least 32 and form one connected region.
It rejects intermediate colors, enclosed background-colored regions, nonopaque input, and unsupported formats.
The output retains exact dimensions and all original RGB values.
Removed pixels have alpha 0, and preserved pixels have alpha 255.
The [rule artifact](../feasibility/image-rule.raster-v1.json) and amendment define all restrictions.
Dark regions can remain preserved even when a human calls them shadows.
The interface must disclose this limitation before delegation.

The generator uses OpenCV without pretrained models.
The checker independently traverses pixel regions and does not trust a provider mask or declaration.
Image acceptance does not certify product identity, authenticity, photographic quality, or customer usefulness.
AI negotiates supported image conditions, prices, and deadlines within delegated authority.
The fair negotiation comparison in section 9 remains required.

G2 requires a fresh freeze of the request schema, rule, checker, generator, dependencies, calibration hashes, and support scope.
Ten calibration originals remain separate from twenty independent evaluation originals.
The evaluator supplies independently authored raster reference regions and valid outputs after the freeze.
Reference regions cannot come from production checker or generator results.
The evaluator records source permissions, selection reasons, provenance, and every first-run result.
The evaluation distinguishes customer-relevant photographs from synthetic cases.
Synthetic tests alone cannot establish G2 success or customer applicability.

Each evaluation original receives seven attacks: full transparency, unchanged source, preserved-region deletion, residual background, replacement content, resizing, and boundary damage.
G2 must accept at least eighteen valid outputs and reject all 140 attacks and every declared unsupported case.
Unsupported categories cover format, dimensions, transparency, perimeter, intermediate colors, enclosed background regions, and disconnected preserved regions.
The report must disclose actual denominators, false acceptances, false rejections, and failure artifacts.
Changes to rules or scope require fresh evaluation data after another freeze.
The [active protocol](feasibility/g2-protocol.md) defines the evaluation boundary.
Legacy semantic experiments remain historical evidence and cannot establish success under the new contract.
Checker failure cannot be bypassed through per-transaction human approval.
G3 remains blocked until reviewed G2 success.

## 8. 끝까지 이어지는 사용자 흐름 — R6·R7

The buyer sets image submission conditions, limits, and budget.
The provider sets its minimum price and supported work.
The agents exchange source images under section 7 before final agreement.
The runtime command `pact.server trade` connects this exchange, negotiation, and the existing worker for one prepared transaction.
The operator prepares permitted candidates and valid Mandates before execution.
The command permits at most one signed rework and preserves existing payment limits and recovery restrictions.
The interface shows preflight failures, remaining submission attempts, and supported alternatives.
정상 거래에서는 현재 단계·가격·남은 한도·지급 상태를 먼저 보여 준다. 서명·해시는 펼쳐 보는 거래 기록에 둔다. 주요 사건 알림은 앱 화면에서 제공하며 이메일 통합은 만들지 않는다.
협상은 최대 제안 3회로 제한한다. 두 에이전트는 가격·기한을 위임 안에서 구조화해 제안한다. 일반 코드가 조건을 검증한다. 합의 실패는 지급 없이 종료한다.

| 사건 | 사용자가 보는 결과와 다음 행동 |
| --- | --- |
| 검사 실패 | 실패 항목과 재작업 여부 표시. 최초 합의에 허용된 경우에만 기한 안에 1회 재작업. 재실패는 중단 처리 |
| 검사 불능·지급 제출 전 기한 만료 | 지급 제출 금지. 승인 조회·취소 뒤 지급 불가능이 확인되면 예약 해제 |
| 지급 제출 후 합의 기한 만료 | 기존 지급 의도 유지. 같은 요청의 조회·지원되는 발송 또는 재시도 진행. 확인 전 예약 유지 |
| 지급 제출 후 외부 승인 만료 | 기존 지급 조회. 미지급과 지급 불가능 확인 시 실패·예약 해제. 불명이면 예약 유지·지원 요청 |
| 장기 지급 상태 불명 | 예약액·담당자·마지막 확인·다음 확인 예정 표시. 앱 지원 요청과 이의 제기 가능. 확인 불가 시 예약 지속 |
| 긴급 정지 | 새 지급 작업·증거 제출 중단. 이미 커밋된 지급은 계속 처리함을 표시하고 의무·예약액·조회 상태 안내 |
| 지급 실패 | 제공자에게 미지급과 작업 비용 손실 가능성 표시. 구매자에게 결과 사용권을 열지 않음 |
| 지급 확인 | 구매자에게 같은 출력 해시의 파일 접근권 부여. 제공자에게 지급 ID와 상태 표시 |
| 전달 실패 | `결제 완료·전달 재시도` 표시. 같은 파일 접근을 재시도하며 추가 지급 없음 |

결제 전에 출력 파일을 접근 제한 영속 경로에 기록하고 다시 읽어 해시를 확인한다. 임시 디렉터리·메모리만 사용하지 않으며 프로세스 재시작 뒤에도 같은 파일을 읽을 수 있어야 한다. 저장 실패는 지급을 막는다. 구매자는 결제 전 원본 결과를 내려받을 수 없다.
이 저장소는 파일 전달을 위한 신뢰된 중개점이며 자금 에스크로가 아니다. 제공자의 작업 비용이나 결제 후 다운로드 성공을 보장하지 않는다.
결제 성공 후 권한 갱신 전에 종료되면 재시작 시 지급 조회로 접근권과 같은 해시의 파일 다운로드를 복구한다. 다운로드 실패는 같은 파일로 재시도한다. 파일 소실·영구 장애면 성공으로 표시하지 않고 지원 요청과 증거 다운로드 경로를 제공한다.
호스트 전체 소실에 대비한 외부 백업은 이번 구현 범위 밖이다. 소실 표시와 수동 지원은 정상적인 결과 인도나 재시작 복구의 통과 증거를 대신하지 않는다.
자동 환불·분쟁 판정은 범위 밖이다. 실제 결제 후 인도 불능을 자동으로 해결한다고 주장하지 않는다. 사용자는 공개된 수동 지원 절차로 사안을 전달한다.
원본·결과는 접근 제어와 암호화 저장을 적용한다. 공개 기록에는 개인·결제 비밀값과 파일 원문을 넣지 않는다. 보관 종료일까지 유지하고 분쟁 보관 정지가 있으면 삭제하지 않는다.

## 9. 차별점과 발표 — R10·R11·R12·R13

AP2에도 위임·서명·판매자 역할·영수증이 있다. “기존 프로토콜은 구매자만 다룬다”는 문구를 쓰지 않는다. 이 수정안은 AP2 전체에 없는 기능이라는 주장을 하지 않는다. [AP2 구현 문서](https://ap2-protocol.org/ap2/implementation_considerations/)

| 비교 | 이번 시연에서 증명할 추가 가치 |
| --- | --- |
| Direct raster operation | Compare the same operation with delegated agreement, fulfillment checks, and payment. Exclude customers who do not need an independent provider. |
| Deterministic automatic payment | Measure additional AI contribution separately from delegated-commerce savings against human-operated transactions. Exclude unsupported AI-superiority claims. |
| PayPal 멱등 요청 | 합의·검사·수취인 연결, 한도 동시성, 응답 유실 복구까지 묶은 거래 상태 |
| AP2의 위임·결제 증거 | 제공자 작업 의무와 좁은 완료 검사 결과를 PayPal 지급 조건에 연결한 구체적 데모. 우월성·상호운용성은 미검증 |

The negotiated image amendment adds supported image conditions to the same negotiation comparison.
Both flows receive identical source availability, dimensions, background RGB candidates, rule restrictions, and submission budgets.
The deterministic comparator selects the first compatible complete candidate under the same ordering.
The changing-condition cases include an unavailable requested source and a supported provider counterproposal.
Do not give the AI flow alternatives or preparation information unavailable to the comparator.

**Delegated commerce evaluation, clarified on 2026-10-25:** The primary benefit concerns human conditions followed by agent-operated buying and selling.
The primary comparator uses humans to arrange the same task, coordinate conditions, check delivery, and initiate payment.
Measure both parties' interventions, active time, setup, condition conversion, preparation, and total transaction costs.
Keep exception handling separate from routine transaction measurements.
Section 2 retains its customer sampling and initial rejection thresholds.
The [measurement clarification](feasibility/g5-delegated-commerce-20261025.md) defines counting rules and evidence limits.

The deterministic comparator answers a separate question about additional AI contribution.
Both automated flows retain identical candidates, participant restrictions, checks, storage, payment, and recovery infrastructure.
The comparator selects the first mutually permitted complete candidate or rejects without payment.
Retain ten constant-condition cases and ten changing-condition cases for this secondary comparison.
Record interventions, restriction violations, feasible agreements, infeasible rejections, elapsed time, and model costs.
The previous requirement for two fewer interventions than deterministic selection no longer controls the primary delegated-commerce claim.
The user clarified that claim on 2026-10-25.
Equal deterministic performance prevents AI-superiority claims without disproving savings against human-operated commerce.
Existing measurements do not become customer evidence through this correction.
Freeze the revised procedure before collecting new comparative measurements.

증거 묶음에는 양측 위임·서명·검사·PayPal 식별값·실제 조회 결과를 넣는다. 분쟁용 설명은 구조화된 기록에서 만들고 근거 없는 내용을 제외한다.
이번 영상에서는 “증거 묶음 내보내기”만 시연한다. Disputes API 제출, PayPal 접수, 승소를 표시하지 않는다. 자동 제출은 별도 위임과 계정 실증이 필요한 후속 범위다.

| 시간 | 2분 45초 영상 내용 |
| --- | --- |
| 0:00~0:15 | 반복 외주 고객의 문제와 이번 가설, 결과 파일 예시 |
| 0:15~0:35 | 입력 범위·양측 한도·최초 PayPal 동의 완료 기록 |
| 0:35~1:30 | 실제 협상·동일 서명·승인·작업·검사·지급·다운로드 |
| 1:30~2:00 | 전경 훼손 결과 거부, 추가 지급 0건, 재작업 또는 종료 |
| 2:00~2:20 | 응답 유실 후 같은 결제 조회 복구와 재사용 차단 |
| 2:20~2:45 | 실제 측정값·증거 묶음·지원 범위·남은 한계 |

핵심 55초는 한 거래 상세 화면의 세 부분으로 구성한다.

1. 첫 15초: 거래 번호·양측 위임·같은 합의 해시·금액·기한을 보여 준다.
2. 다음 20초: 입력·출력 미리보기와 출력 해시를 보여 준다. 같은 합의에 연결된 검사 결과를 함께 표시한다.
3. 마지막 20초: 같은 합의·검사·출력 해시를 참조하는 지급 기록을 보여 준다. PayPal ID·조회 상태와 내려받은 파일 해시를 대조한다.

짧게 표시한 해시를 누르면 전체값과 원문 증거를 볼 수 있게 설계한다. 거래 번호를 화면에 고정해 서로 다른 거래의 기록을 이어 붙이지 않는다. 이 구성의 실제 소요 시간은 미검증이다.

시간을 맞추려고 거래 성공을 합성하지 않는다. 영상·소개·실행 지침에 영어 또는 영어 번역을 제공한다. 실행 가능한 빌드와 공개 저장소·라이선스·완전한 재현 지침은 별도 제출 게이트다. [공식 규정 §4](https://paypalaihackathon.devpost.com/rules)

## 10. 구현 순서와 통과 증거

**GD adoption and document consistency:** The user requested GD execution on 2026-10-24.
The [adoption record](feasibility/gd-reconciliation-20261024.md) records all 24 ADR dispositions and PACT, glossary, README, and proposal reconciliation.
The retained design conditions apply to subsequent implementation.
G3 requires the boundaries in the reviewed [G1 acceptance](feasibility/g1-acceptance-20261024.md) and [G2 acceptance](feasibility/g2-acceptance-20261024.md).
Local feasibility tests and bounded Sandbox observations cannot substitute for those reviews.
The [2026-10-25 evidence matrix](feasibility/g3-g4-evidence-matrix-20261025.md) updates implementation evidence without granting G3 or G4 acceptance.
The table below preserves the 2026-10-24 status snapshot.
The [README](../README.md) links subsequent acceptance records and current implementation evidence.
The [source exchange report](feasibility/image-exchange-20261025.md) records the implemented request, replacement, browser, and shared submission limit.
The [G5 preflight](feasibility/g5-comparator-preflight-20261025.md) identifies a comparator conflict without changing the original acceptance threshold.

| Order | Gate | Required evidence | Current status on 2026-10-24 |
| --- | --- | --- | --- |
| 1 | G1 payment flow | Reviewed consent, unattended authorization, separate capture, readback, account bindings, and recovery conditions | Accepted within the reviewed Sandbox scope. Query-only recovery restrictions remain. |
| 2 | G2 checker | Frozen rule and independent first-run evaluation with false acceptance and rejection counts | Accepted for prepared rectangular photographic panels. Broader image populations remain unqualified. |
| 3 | GD document consistency | Adoption record, all ADR dispositions, and consistent project documents | Adopted and reconciled. Verification appears in the adoption record. |
| 4 | G3 transaction safety | Counterexample tests and restart evidence below | In progress: [merchant consent](feasibility/g3-merchant-linkage-20261024.md) and [buyer Vault linkage](feasibility/g3-buyer-linkage-20261024.md) have local tests. Actual account ownership and full transaction safety remain unverified. |
| 5 | G4 complete user flow | Failure, stop, post-payment delivery retry, and access recovery evidence | Not implemented. |
| 6 | G5 value and submission | Section 2 applicability and economic measurements, section 9 comparator, and separate submission checks | Not executed. |

G3 must test concurrent JPY 6 agreements against a JPY 10 limit.
G3 must test both commit orders for revocation versus finalization and emergency stop versus payment submission.
G3 must reject changed agreements, merchants, or files.
G3 must prevent additional payments when an agreement is submitted again.
G3 must test restart after capture response loss, missing request identifiers, and expired idempotency retention.
각 반례는 허용된 결제 수·예약액·최종 상태를 검증한다. 응답 유실 실험은 실제 sandbox 결제를 수행한 뒤 로컬 수신·저장을 차단한다. 외부 결제 자체를 모의한 테스트와 구분한다.
G3에는 구매자 A의 합의에 사용자 C의 저장 결제수단을 붙이는 경우와 제공자 B의 합의에 다른 Principal 소유 판매자 M을 붙이는 경우를 추가한다. 확정·지급 제출 양쪽에서 거부하고 외부 호출 0건을 확인한다.
G3에는 `지급 제출 커밋 → HTTP 전 종료 → 정지 → 재시작`을 추가한다. 정상 승인·멱등 지원 조건에서 기존 요청 ID로 결제 정확히 1건, 확인 전 예약 유지, 성공 확인 후 예약 0·소비액 증가·지급 완료가 기대 결과다. 결과 불명이면 결제 수를 단정하지 않고 예약 유지·`지급 상태 확인 중`이어야 한다.
G3에는 `지급 제출 커밋 → HTTP 전 종료 → 합의 기한 만료 → 재시작`을 추가한다. 외부 승인이 유효하고 G1의 안전한 재시도 조건을 만족하면 기존 요청을 계속한다. 성공 확인 전 예약을 유지하고 확인 뒤 한 번만 소비한다. 지급 제출 전 만료라면 발송 0건이어야 한다. 외부 승인도 만료됐다면 기존 지급을 조회하고 §6의 세 확인 결과에 따라 상태·예약을 처리한다.
G3에는 다른 Principal의 계정 연결·파일·긴급 정지 ID를 세션 요청에 넣는 반례를 추가한다. 서버는 정보 공개·상태 변경·외부 호출 전에 거부한다. 로그인 난수 재사용, 서명 목적 변경, PayPal 복귀 상태값 불일치도 거부한다. 운영자의 파일 접근·계정 변경·새 지급 요청은 거부한다.
G4에는 장기 불명 지급의 완료 확인·미지급 및 지급 불가능 확인·확인 불가 사례를 추가한다. 권한 없는 운영 변경과 출처 불명 증거를 거부한다. 허용 전이, 감사 기록, 문의·이의 제기 표시와 확인 불가 시 예약 유지를 검사한다.
G5 evaluates section 2 applicability and economics separately from G2 image quality.
Section 9 evaluates delegated-commerce savings and additional AI contribution as separate questions.
Submission material readiness remains outside design completeness scores.

G4 필수 통과는 `출력 저장 직후 재시작 → 같은 해시 파일 읽기`와 `결제 직후 접근권 저장 전 재시작 → 접근권 복구·같은 해시 파일 다운로드`다. 출력 저장 실패와 다운로드 장애 후 재시도도 확인한다. 영구 파일 소실은 미해결 상태와 수동 지원을 보여야 하며 필수 통과를 대체하지 못한다.

## 11. 최초 지적 추적

The table below preserves the original finding dispositions and evidence requirements.
Acceptance of a finding does not establish closure.
Section 10 and the [closure plan](feasibility/g1-closure-plan-20261024.md) record current evidence and remaining conditions.

| ID | 결정 | 수정 위치 | 필요한 통과 증거 / 남는 항목 |
| --- | --- | --- | --- |
| R1 | 수용 | §3 | G1. 실제 계정 권한과 API 조합 미확정 |
| R2 | 수용 | §5 | G3 동시 예약·해제. 다중 서버는 범위 밖 |
| R3 | 수용 | §6 | G3 실제 응답 유실. 장기 불명 상태는 수동 확인 |
| R4 | 수용 | §4 | G1·G3 지급자 소유/수취인/파일 불일치 거부. 서버 신뢰 잔존 |
| R5 | 수용 | §5·§6 | G3 취소·정지 경합. 외부 발송 취소 보장 없음 |
| R6 | 수용 | §8 | G4 실패·재작업·정지 화면과 행동 |
| R7 | 수용 | §8 | G4 접근 복구·동일 파일 재전달. 지급·인도 보장 없음 |
| R8 | 수용 | §2 | G5 비교 측정·수요 확인. 고객 가설 미검증 |
| R9 | 수용 | §7 | G2 독립 평가. 제한 밖 품질 보장 없음 |
| R10 | 수용 | §9 | G5 비교·실제 데모. 새 범용 규격의 독창성 미입증 |
| R11 | 수용 | §9 | G5 2분45초 실제 영상. 제작 전 |
| R12 | 수용·자동 제출 보류 | §9 | 내보내기와 실제 제출의 구분. Disputes API 미검증 |
| R13 | 수용 | §9·§10 | G5 새 환경 실행·라이선스·영어 자료. 제출 적격성 미확정 |

## 12. 후속 문서 변경 목록

GD adopted the narrowed scope and reconciled PACT, README, GLOSSARY, and all 24 ADR dispositions on 2026-10-24.
The [adoption record](feasibility/gd-reconciliation-20261024.md) identifies retained and amended decisions with source sections and verification scope.
The original proposal remains the detailed baseline for sections 1–9 and the counterexamples in section 10.
No new ADR is required for this scope.
Historical review scores and experiment reports retain their original scope.
GD adoption does not pass G1, G2, G3, G4, or G5.
Language review and remaining evidence limitations appear in the adoption record.
