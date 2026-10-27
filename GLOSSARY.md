# PACT

두 사용자의 에이전트가 권한 안에서 합의하고 결제하는 과정을 설명하는 공통 언어다.

## Language

**PACT**:
두 사용자 에이전트의 위임, 협상, 동일 조건 합의와 외부 결제를 연결하는 범용 상호 보증 프로토콜이다. 자체 결제망은 아니다.
_Avoid_: 결제망, PayPal 대체 프로토콜

**Principal**:
자신의 권한 일부를 Personal Agent에 위임하는 사람 또는 조직이다. 한 거래에서 지급자 또는 수취인 역할을 가질 수 있다.
_Avoid_: 사용자 계정, 구매자, 판매자

**Personal Agent**:
한 Principal이 발급한 Mandate의 범위 안에서 협상하고 거래하는 소프트웨어 행위자다.
_Avoid_: 결제 주체, PayPal 계정

**Mandate**:
Principal이 Personal Agent에 부여한 취소 가능하고 제한된 권한을 담은 서명 객체다. 거래마다 Principal의 확인을 받지 않고 실행할 수 있는 경계를 정한다.
_Avoid_: 무제한 승인, 거래별 승인

**거래 증거 묶음**:
거래의 위임, 협상, 합의, 이행, 결제와 분쟁 대응 기록을 검증할 수 있게 모은 자료다. 실제 이행과 품질을 보증하지 않는다.
_Avoid_: 모든 대화 원문, 품질 보증서

**분쟁 대응 위임장**:
개인 에이전트가 정해진 범위 안에서 분쟁 자료를 만들고 PayPal에 제출할 수 있게 사용자가 따로 부여한 권한이다.
_Avoid_: 일반 거래 위임장, 무제한 분쟁 처리 권한

**최종 거래 합의서**:
The final transaction agreement contains the same canonical bytes signed by both Personal Agents.
It binds roles, integer JPY amount, obligations, completion criteria, deadline, cancellation, refund, delivery, and retention conditions.
It also binds both Mandates, transaction ID, account binding version, merchant, input hash, and rule hash and version.
The negotiated image amendment adds the image request hash, exact dimensions, and region counts.
Both signatures are prerequisites, but finalization occurs only at the finalization commit.
_Avoid_: 대화 요약, 한쪽만 서명한 주문서

**거래 규칙서**:
특정 거래 종류의 의무, 완료 판단 방법과 필요한 증거를 정한 문서다. 두 개인 에이전트가 같은 규칙서 판을 지원해야 거래할 수 있다.
_Avoid_: 모든 거래에 강제하는 단일 완료 기준

**제안 기록**:
협상 중에 오간 서명된 제안을 순서대로 연결한 기록이다. 각 제안은 바로 전 제안이 바뀌지 않았음을 확인하는 값을 담는다.
_Avoid_: 서명 없는 대화 기록, 최종 가격만 남긴 기록

**결제 승인**:
최종 합의 뒤 실제 이행을 시작하기 전에 PayPal이 나중의 결제 실행을 허용한 상태다. 실제 지급이나 지급 성공을 보장하지 않는다.
_Avoid_: 결제 완료, 결제 금액 확보, 지급 보장

**자동 이행 확인 도구**:
제출된 증거가 거래 규칙서의 완료 조건을 만족하는지 자동으로 검사하는 도구다. 결제 실행 여부만 정하며 분쟁의 승패를 판단하지 않는다.
_Avoid_: 분쟁 판정자, 품질 보증자

**거래 번호**:
하나의 최종 거래 합의서와 하나의 PayPal 결제 흐름을 연결하는 고유한 값이다. 같은 요청이 반복돼도 새 결제를 만들지 않는 기준으로 사용한다.
_Avoid_: 재사용 가능한 주문 번호

**거래 신원**:
PACT 문서의 서명을 확인하는 공개 열쇠다. 실명, 회사명 또는 PayPal 계정의 실제 신원을 뜻하지 않는다.
_Avoid_: 실명 인증, PayPal 계정 인증

**사용자 서명 열쇠**:
사용자가 위임장과 열쇠 변경 기록에 서명할 때 쓰는 열쇠다. 비밀 부분은 사용자 기기 밖으로 내보내지 않는다.
_Avoid_: 에이전트 서명 열쇠, 서버가 보관하는 사용자 비밀 열쇠

**에이전트 서명 열쇠**:
개인 에이전트가 위임 범위 안에서 제안, 합의서와 거래 기록에 서명할 때 쓰는 별도 열쇠다.
_Avoid_: 사용자 서명 열쇠

**위임 취소 기록**:
A revocation record is a signed user record that prevents new finalization under the referenced Mandate.
The server checks it inside the finalization transaction.
Revocation committed first rejects finalization.
A later revocation does not erase a previously committed agreement.
_Avoid_: 이미 확정된 거래의 자동 취소

**복구 열쇠**:
사용자 서명 열쇠를 잃거나 바꿔야 할 때 열쇠 변경 기록에 서명하도록 사용자가 별도로 보관하는 열쇠다.
_Avoid_: 중앙 관리자의 임의 복구 권한

**공개 기록판**:
The public ordering record exposes hashes, record types, signer references, sequence, and timestamps without original documents or payment secrets.
SQLite commit order determines revocation and finalization in this implementation.
Signed receipts permit comparison against retained copies, not proof against consistent server lies or collusion.
_Avoid_: 거래 원문 공개, 비밀 증거 저장소

**긴급 정지**:
Emergency stop prevents new finalization, new payment submission commits, and new evidence submissions.
A payment submission commit recorded first preserves that existing payment intent, even before HTTP transmission.
Later stop does not cancel that intent or erase existing obligations.
_Avoid_: 기존 거래의 자동 취소, 분쟁 확정

**보관 종료일**:
The retention end date is the earliest permitted deletion date under applicable dispute periods and required retention obligations.
Disputes, unknown payment results, and objections suspend related evidence deletion.
The server records an applicable new date after those holds end.
_Avoid_: 모든 자료의 영구 보관, 분쟁 중 자동 삭제

**사용자 백업**:
개인 에이전트가 자기 사용자의 거래 자료를 사용자가 선택한 저장소에 암호화해 복사하는 선택 기능이다. 사용자가 복호화 열쇠를 관리하며 백업 저장소는 거래 기록의 신뢰 근거가 아니다.
_Avoid_: 상대방의 비공개 자료 복사, 암호화하지 않은 외부 저장

## GD terms adopted on 2026-10-24

**Account binding version**:
An immutable server record links a Principal to the buyer identity and payment token obtained during consent.
The signed agreement references this version, which account changes cannot overwrite.
_Avoid_: caller-selected token, mutable account alias

**Merchant registration**:
A server record links the provider Principal to the fixed PayPal merchant identity.
_Avoid_: agent-selected payee, proof of account ownership from a signature alone

**Finalization commit**:
The database commit validates both signed Mandates, reserves both original period limits, and records the agreement in order.
Revocation, expiry, stop, and limit checks occur in that same transaction.
_Avoid_: last signature time, HTTP payment transmission

**Reservation**:
An agreement amount remains withheld from its original Mandate period limit until confirmed consumption or confirmed release.
Unknown payment results retain reservations.
Release requires confirmed nonpayment and impossibility of payment through the existing path.
_Avoid_: PayPal authorization, automatic release after timeout

**Payment submission commit**:
The database commit validates payment conditions and records the immutable payment intent before the external request.
It rechecks stop, deadline, accepted output, account ownership, and delegated authority.
A later stop or agreement deadline expiry does not cancel this existing intent.
_Avoid_: PayPal receipt time, finalization commit

**Unknown payment result**:
The available evidence cannot confirm payment success or payment impossibility.
Reservations remain active while supported recovery or evidence review seeks an outcome.
_Avoid_: assumed payment failure, permission to create another order

**Delivery retry**:
The system attempts to provide the same paid output file again without another payment.
_Avoid_: replacement payment, automatic refund

The [GD adoption record](docs/feasibility/gd-reconciliation-20261024.md) records the definition changes and language review.
Unchanged Korean entries retain their existing meanings.

## Negotiated image terms adopted on 2026-10-24

**Submission request**:
A submission request specifies source dimensions, background RGB, and the complete versioned image rule before final agreement.
_Avoid_: provider-selected completion criteria

**Raster operation**:
A raster operation changes explicitly defined pixels without identifying products, shadows, or photographic quality.
_Avoid_: semantic background removal, product recognition

**Preflight**:
Preflight checks exact source bytes against a submission request before final agreement or payment authorization.
_Avoid_: payment approval, provider assertion

**Image terms**:
Image terms bind the submission request, source, rule, dimensions, and region counts into the final transaction agreement.
_Avoid_: unsigned replacement agreement

The [negotiated image amendment](docs/feasibility/negotiated-image-contract-20261024.md) records the scope change and language review.
