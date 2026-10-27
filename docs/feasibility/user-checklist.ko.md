# 사용자가 준비할 작업

G1은 Sandbox 범위에서 독립 에이전트 검토까지 완료했습니다.
새 토큰 발급 동의를 녹화하고, 추가 승인 클릭 없이 JPY 1 승인·별도 지급·재조회를 확인했습니다.
기존 승인 취소와 응답 유실 복구 증거도 독립 검토를 통과했습니다.
[최종 G1 통과 기록](g1-acceptance-20261024.md)을 참고하세요.
현재 누적 한도 JPY 2500 중 보수적으로 JPY 12를 사용했고 JPY 2488이 남습니다.
G1을 위해 사용자가 추가로 준비할 작업은 없습니다.
G2는 [제한된 이미지 규칙 범위](g2-acceptance-20261024.md)에서 통과했습니다.
현재 사용자가 추가로 설정할 항목은 없습니다.
서버 재시작, 보관 보류·해제, 다운로드 장애 후 재시도는 추가 결제 없이 검증했습니다.
지원 요청·답변과 별도 운영자의 재확인도 검증했습니다. 운영자는 파일 다운로드나 새 결제를 할 수 없습니다.
이의 제기 후 최신 결제 정보를 조회하고 충돌을 기록하는 기능을 보완했습니다. 이의 제기와 결제 상태는 유지합니다.
[이의 제기 증거 검증 기록](g4-objection-evidence-20261025.md)을 참고하세요.
실제 JPY 1 결제 직후 작업자를 종료한 뒤, 재청구 없이 조회로 결제와 다운로드를 복구했습니다.
[중단·복구 검증 기록](integrated-recovery-20261025.md)과 [남은 검증 항목](g3-g4-evidence-matrix-20261025.md)을 참고하세요.
G3는 [제한된 거래 안전성 범위](g3-acceptance-20261025.md)에서 독립 검토를 통과했습니다.
운영 주체와 서비스 대상은 모두 JP로 반영했습니다. [JP 보관 기준 조사](retention-jp-addendum-20261025.md)를 참고하세요.
G4는 [Sandbox 전달·복구 범위](g4-acceptance-20261025.md)에서 독립 검토를 통과했습니다.
결제 후 파일 유실 시 재시작해도 결제 완료·전달 미해결·지원 요청·증거 내보내기가 유지됩니다.
전체 테스트 565개가 통과했습니다. 이번 수정은 실제 PayPal·Gemini를 호출하지 않았습니다.
실거래 전 기록별 보관·삭제 정책, 공유 파일 보호, 외부 이의제기 결과 연결을 완료해야 합니다. 삭제는 비활성화 상태입니다.
현재 G4 Sandbox 검증을 위해 사용자가 추가로 설정할 항목은 없습니다.
G5는 사람이 조건을 정한 뒤 에이전트끼리 거래하면서 사람의 작업과 시간이 줄어드는지 평가합니다.
사람이 직접 거래하는 흐름과 비교하며, 조건 입력·최초 동의·위임·사진 준비에 드는 수고도 기록합니다.
AI와 일반 자동화의 비교는 별도 평가입니다. 실제 고객의 시간 절약량은 아직 측정하지 않았습니다.
[수정된 평가 기준](g5-delegated-commerce-20261025.md)에 측정 범위와 미검증 항목을 정리했습니다.
기존 위임을 유지한 역제안·합의·모의 결제·양측 다운로드와 완료 후 재실행을 확인했습니다.
단일 실행 명령을 연결한 현재 소스의 전체 테스트 559개가 통과했습니다. [검증 기록](evidence/single-command-commerce-20261025.json)을 참고하세요.
이번 검증은 실제 PayPal·Gemini를 호출하지 않았으며, 누적 사용액은 JPY 12로 유지됩니다.

## 최신 추가 검증

G4 수정이 포함된 전달용 소스 499개를 별도 디렉터리에 복원했고, 전체 테스트 565개가 통과했습니다. 기존 설치 의존성을 재사용했습니다.
[복원 검증 기록](evidence/source-archive-post-g4-20261025.json)을 참고하세요. 추가 결제는 없습니다.
영상의 브라우저 구간에는 스크롤 중에도 거래 ID가 보이도록 고정 표시를 추가했습니다.

실제 Gemini를 연결한 단일 명령도 통과했습니다. 사진 교체·합의·작업·검사·양측 다운로드를 확인했습니다.
이 추가 실행의 PayPal 응답은 모의 처리이며, 추가 결제는 0엔입니다. 누적 사용액은 JPY 12로 유지됩니다.
2분 45초짜리 비공개 시연 영상에 실제 명령 실행과 검증 결과를 추가했습니다.

```sh
mpv "$HOME/.local/state/pact-demo-recording-20261025/pact-review-v3-165s.mp4"
```

영상은 서버 로컬 파일입니다. 이 명령은 같은 환경에 `mpv`가 설치된 경우에만 사용할 수 있습니다.
로그인 동의와 실제 결제 중단·복구 장면은 보관 기록으로 표시했습니다. 공개 업로드는 하지 않았습니다.
고객 측정용 빈 양식도 준비했습니다. [측정 절차와 복사 명령](g5-measurement-templates/README.md)을 참고하세요.
양식에는 실제 고객 데이터가 없으며, G5 통과로 처리하지 않았습니다.
비공개 양식은 `$HOME/.local/state/pact-g5-measurements/`에 준비했습니다.
G5 완료에는 실제 참여 고객 3명과 고객별 최근 연속 의뢰 20건, 작업 시간·비용 비교가 필요합니다.
이 자료를 준비할 수 없다면 G5는 미검증으로 남습니다. 추가 PayPal 설정은 필요하지 않습니다.

## 조건을 준비한 뒤 한 번에 실행하기

`trade`는 사진 교환·AI 협상·작업·검사·결제를 연결합니다. **실제 Sandbox 결제가 발생할 수 있습니다.**
기존 계정 연결과 유효한 위임, 완전한 조건 후보를 담은 비공개 작업 파일이 필요합니다.
아래 경로의 파일은 예시입니다. 실제 준비한 새 거래의 작업 파일을 지정하세요.

```sh
/tmp/pact-opencv-venv/bin/python -m pact.server trade \
  --state-dir "$HOME/.local/state/pact-sandbox" \
  --sandbox-env ./sandbox.env \
  --gemini-env ./gemini.env \
  --job-file /private/negotiation.json \
  --service-origin https://server-debian-dev.tailffdbc2.ts.net \
  --max-amount-jpy 1
```

- 허용된 경우에만 재작업을 최대 1회 진행합니다.
- 실행 결과의 `execution.status`가 `paid`인지 확인하세요. 종료 코드 0만으로 결제 완료를 판단하지 마세요.
- 협상 거절 시 `execution`은 `null`이며 결제 작업을 시작하지 않습니다.
- 응답 유실이나 중단 시 `trade`를 다시 실행하지 마세요. 기존 거래와 제안 기록부터 확인하세요.
- 합의가 확정된 거래의 복구에는 아래 명령으로 **같은 거래 번호**를 사용하세요.

```sh
/tmp/pact-opencv-venv/bin/python -m pact.server work \
  --state-dir "$HOME/.local/state/pact-sandbox" \
  --sandbox-env ./sandbox.env \
  --service-origin https://server-debian-dev.tailffdbc2.ts.net \
  --transaction-id '<기존 거래 번호>'
```

`--max-amount-jpy 1`은 거래 후보별 상한입니다. 기존 누적 한도 JPY 2500을 추가하거나 초기화하지 않습니다.
현재 자연어 조건을 실행 조건으로 자동 변환하는 기능은 없습니다. 이번 변경으로 합의 후 별도 작업 명령은 필요 없어졌습니다.
현재 사용자가 새로 설정할 항목은 없습니다.

## 이전 준비 및 실험 기록

아래 기록은 각 실험 당시의 상태입니다. G1 미완료라는 과거 설명은 위 통과 기록으로 대체됩니다.

## 1. PayPal sandbox 준비

[PayPal Developer](https://developer.paypal.com/)에 로그인하고 다음을 준비하세요.

- Sandbox REST 앱의 Client ID와 Secret
- 구매자용 개인 sandbox 계정과 판매자용 비즈니스 sandbox 계정
- 판매자 계정의 국가와 저장 결제수단 기능 사용 가능 여부

기능이 없거나 권한을 확인할 수 없으면 해당 상태만 알려 주세요.
계정 조건은 [PayPal 공식 안내](https://developer.paypal.com/api/payment-tokens/save-without-purchase/paypal/)를 참고하세요.

현재 보고된 상태는 판매자 국가 `JP`, Vault 활성화 완료입니다.
사용자의 저장·결제 테스트 요청에 따라 최초 동의, 결제수단 저장, 후속 승인과 별도 capture를 실행했습니다.
저장된 `vault_id`로 추가 로그인·승인 클릭 없이 JPY 5000 한 건을 지급했습니다.
capture와 재조회 모두 `COMPLETED`를 확인했습니다.
구매자·판매자·주문·승인·지급 연결도 일치했습니다.
판매자는 인증된 Sandbox 앱의 기본 수취인에 연결했으며, 국가 JP는 사용자 보고 상태입니다.
인증정보와 거래 식별자를 제외한 [검증 기록](evidence/g1-storage-payment-20261024.json)을 남겼습니다.
허용된 JPY 5000은 이번 한 건에 전부 사용했습니다.
추가 테스트는 이후 허용한 총 JPY 2500 범위에서 진행합니다.
JPY 1을 승인한 뒤 취소했고, 재조회에서도 `VOIDED`를 확인했습니다.
이 승인 취소 실험에서는 실제 지급이 없었습니다.
그다음 재동의를 녹화하고 JPY 1을 별도로 지급했으며, 재조회도 `COMPLETED`였습니다.
응답 유실 복구 실험에서도 JPY 1 지급 한 건을 실행했습니다.
응답 유실 실험 시점에는 취소된 1엔과 지급된 2엔으로 총 JPY 3를 사용했습니다.
이후 새 토큰 검증에 JPY 1을 추가해 현재 사용액은 JPY 4, 남은 허용액은 JPY 2496입니다.
[응답 유실 복구 검증 기록](evidence/g1-response-loss-recovery-20261024.json)을 참고하세요.
[녹화·지급 검증 기록](evidence/g1-recorded-payment-20261024.json)을 참고하세요.
이 금액은 테스트 허용액이며 PayPal 계좌 잔액이나 계정 한도가 아닙니다.
[승인 취소 검증 기록](evidence/g1-void-20261024.json)을 참고하세요.
검증 중 권한 오류가 발생하면 PayPal 지원 담당자에게 아래 내용으로 확인을 요청하세요.

```text
JP 판매자의 Sandbox REST 앱에서 Vault를 활성화했습니다.
Payment Method Tokens API로 PayPal Wallet 저장을 검증하려고 합니다.
이 sandbox 계정과 앱의 지원 여부 및 필요한 활성화 절차를 알려 주세요.
Billing Agreements / Reference Transactions 승인 필요 여부도 확인해 주세요.
```

지원 요청에 Secret·액세스 토큰·구매자 비밀번호를 넣지 마세요.

## 1-1. G1 검증 순서

G1은 최초 동의 이후 추가 승인 없이 결제 승인·별도 지급·조회를 수행할 수 있는지 확인합니다.
설계 통화는 사용자 결정에 따라 JPY로 변경했습니다.
최초 로컬 준비와 제한된 API 확인 이후, 별도 요청으로 저장·결제 테스트를 실행했습니다.
아래 3~5단계의 실제 동의·저장·무인 승인·지급·조회를 확인했습니다.
6단계의 미지급 승인 취소와 재조회도 확인했습니다.
이미 알고 있는 주문·승인에서 지급 응답을 잃은 경우는 추가 지급 없이 조회로 복구했습니다.
1~2단계의 독립 검토, 주문 생성 결과 불명, 식별자 유실과 보관 기간 경과 검증은 남아 있습니다.
전체 G1 통과로 처리하지 않습니다.
최초 JPY 5000 거래의 동의 녹화는 없습니다.
새 녹화는 기존 구매자의 재동의이므로, 설계의 녹화 조건 충족 여부를 독립 검토해야 합니다.
녹화에는 계정 정보가 포함되어 있어 공개하지 않고 접근 제한된 로컬 증거로 보관했습니다.
[남은 증거와 승인 취소 계획](g1-closure-plan-20261024.md)에 다음 절차를 정리했습니다.

1. **계정 자격 확인:** 판매자 계정과 Sandbox 앱이 PayPal Wallet 저장 및 Billing Agreements / Reference Transactions를 지원하는지 확인합니다.
   공식 안내의 자격 확인 경로는 `Account Settings → Payment Preferences → Save PayPal and Venmo payment methods`입니다.
   해당 메뉴가 없거나 Sandbox 적용 범위가 불명확하면 위 문구로 PayPal 지원에 문의합니다.
   운영 계정의 자격 상태만으로 Sandbox 앱 권한을 확정하지 않습니다.
2. **실행 절차 검토:** 계정 연결, 요청 필드, JPY 금액, 동의 URL, 요청 ID, 실패 복구와 승인 취소 범위를 독립 검토합니다.
   JPY 5000을 승인 취소 실험에 추가로 사용할 수 있다고 해석하지 않습니다.
3. **최초 동의:** 검토된 절차에 따라 setup token을 만들고 구매자가 브라우저에서 한 번 동의합니다.
   승인된 setup token을 payment token으로 교환합니다.
   이 단계는 저장·동의 확인이며, 무인 결제 성공을 뜻하지 않습니다.
4. **무인 후속 승인:** 저장된 `vault_id`로 `intent: AUTHORIZE` 주문과 승인을 수행합니다.
   추가 로그인·승인 클릭이 필요하면 무인 거래 성공으로 처리하지 않습니다.
5. **별도 지급과 조회:** 승인 ID로 별도 capture를 수행하고 거래 상태를 다시 조회합니다.
   지급의 `COMPLETED`, JPY 금액, 판매자와 주문·승인·지급 ID 연결을 확인합니다.
   주문의 `COMPLETED`만으로 지급 완료를 판정하지 않습니다.
6. **취소와 실패 확인:** 별도로 검토한 미지급 승인에서 void와 후속 상태 조회를 확인합니다.
   시간 초과나 결과 불명이면 새 주문·승인·지급을 만들지 않고 검토된 조회 절차를 따릅니다.

계정 자격 확인 결과와 최초 동의·추가 클릭 0회·별도 지급·조회·승인 취소 증거를 검토해야 G1 통과를 판단할 수 있습니다.
공개 자료에는 Secret, 토큰, 비밀번호와 계정 식별정보를 넣지 않습니다.
구체적인 요청 필드와 보관 기간은 [G1 API 조사](g1-api-research-20261023.md)를 참고하세요.
계정 조건은 [PayPal 저장 결제수단 안내](https://developer.paypal.com/api/payment-tokens/save-without-purchase/paypal/)를 따릅니다.

## 2. 인증정보를 로컬 파일에 저장

이미 보안 설정 파일이 있으면 새로 만들지 말고 기존 경로만 알려 주세요.
새로 만들 때는 다음 명령을 실행하세요.

```sh
mkdir -p "$HOME/.config/pact"
chmod 700 "$HOME/.config/pact"
touch "$HOME/.config/pact/sandbox.env"
chmod 600 "$HOME/.config/pact/sandbox.env"
"${EDITOR:-vi}" "$HOME/.config/pact/sandbox.env"
```

편집기에 아래 내용을 넣고 실제 값으로 바꾸세요.
로컬 서버는 `--sandbox-env`로 지정한 파일에서 `PAYPAL_CLIENT_ID`와 `PAYPAL_CLIENT_SECRET`을 읽습니다.
나머지 계정 정보는 서버 설정으로 사용하지 않습니다.

```sh
PAYPAL_CLIENT_ID='실제 sandbox Client ID'
PAYPAL_CLIENT_SECRET='실제 sandbox Secret'
PAYPAL_MERCHANT_ID='sandbox 판매자 ID'
```

비밀번호·Secret·토큰은 채팅이나 저장소에 붙여 넣지 마세요.
구매자 로그인은 최초 동의 단계에서 브라우저로 진행합니다.

## 3. G2 독립 평가 담당자 지정

G2는 이미지 검사기의 품질을 독립 자료로 검증하는 단계입니다.
개발자와 다른 평가 담당자를 한 명 지정하세요.
다음 준비 범위를 담당자에게 전달하세요.

- 조정용 원본 10장과 겹치지 않는 평가용 원본 20장
- 정상 결과와 원본마다 7종의 공격 결과
- 지원 밖 사례: 복잡한 배경, 그림자, 반투명 물체, 여러 물체, 잘못된 형식
- 독립적인 정답 표시와 기준 마스크

공격 종류와 자료 조건은 [평가 준비 문서](external-readiness.md#g2-preparation-and-handoff)를 따릅니다.
검사기와 규칙을 고정하기 전에는 평가 이미지·정답·마스크를 개발자에게 공개하지 마세요.
지금은 담당자와 자료 준비 여부만 전달하면 됩니다.
담당자를 구하지 못했다면 `독립 평가 담당자 없음`으로 알려 주세요.

## 4. 에이전트에게 전달

아래 양식을 채워 채팅으로 보내 주세요.
계정 식별정보와 인증정보의 실제 값은 넣지 마세요.

```text
PayPal 설정 파일: /home/user/workspace/hackerton/2026-11-paypal-ai/sandbox.env
구매자·판매자 sandbox 계정: 준비됨 / 미준비
판매자 계정 국가:
저장 결제수단 기능: 사용 가능 / 사용 불가 / 확인 필요
추가 sandbox 테스트 허용 총액: JPY 2500 (JPY 4 사용, JPY 2496 남음)
독립 평가 담당자: 이름 또는 식별명 / 없음
평가 자료: 준비됨 / 준비 중 / 없음
```

설정 파일을 다른 위치에 만들었다면 실제 절대 경로로 바꾸세요.
금액 전달만으로 결제를 시작하지 않습니다.
추가 실험은 허용한 총 JPY 2500의 남은 금액 안에서 진행합니다.
이번 지급 결과와 별개로 전체 G1에는 독립 검토가 필요합니다.

## 선택: 현재 코드 확인

```sh
cd /home/user/workspace/hackerton/2026-11-paypal-ai
python3 -m venv /tmp/pact-opencv-venv
/tmp/pact-opencv-venv/bin/python -m pip install -r feasibility/requirements-opencv.txt -r pact/requirements.txt
export PATH="/tmp/pact-opencv-venv/bin:$PATH"
./verify.sh
```

로컬 HTTPS 실행 검증 시 전체 테스트 472개가 통과했습니다. [검증 범위](g3-local-runtime-20261024.md)를 참고하세요.
GD 채택과 문서 정합성 작업을 완료했습니다. [채택 기록](gd-reconciliation-20261024.md)에 ADR 24개의 결정과 검증 범위를 정리했습니다.
G1과 G2는 각각 승인된 범위에서 독립 검토를 통과했습니다. 전체 거래 앱 구현과 통합 검증은 남아 있습니다.
JPY 5000은 `amount_minor: 5000`, `currency: JPY`로 기록합니다.
이 명령은 로컬 테스트만 실행합니다. PayPal에 결제를 요청하지 않습니다.
테스트에는 서버 기동이 필요하지 않습니다. 최초 실행 전에는 위 의존성 설치가 필요합니다.

---

## 로컬 HTTPS API 실행

아래 localhost 명령은 로컬 개발용입니다. 실제 Sandbox 연결에는 문서 마지막의 확정 주소와 실행 명령을 사용하세요.

의존성을 설치한 뒤 프로젝트 루트에서 실행하세요. 초기화와 인증서 생성은 처음 한 번만 실행합니다.
기존 `pact-local` 디렉터리가 있으면 초기화를 반복하지 말고 기존 키와 DB를 보존하세요.

```sh
export PATH="/tmp/pact-opencv-venv/bin:$PATH"
umask 077
mkdir -p "$HOME/.local/state"
python -m pact.server init --state-dir "$HOME/.local/state/pact-local"
openssl req -x509 -newkey rsa:2048 -nodes -days 7 \
  -subj '/CN=localhost' -addext 'subjectAltName=DNS:localhost' \
  -keyout "$HOME/.local/state/pact-local/tls.key" \
  -out "$HOME/.local/state/pact-local/tls.crt"
chmod 600 /home/user/workspace/hackerton/2026-11-paypal-ai/sandbox.env
python -m pact.server serve \
  --state-dir "$HOME/.local/state/pact-local" \
  --sandbox-env /home/user/workspace/hackerton/2026-11-paypal-ai/sandbox.env \
  --certificate "$HOME/.local/state/pact-local/tls.crt" \
  --private-key "$HOME/.local/state/pact-local/tls.key"
```

다른 터미널에서 확인합니다.

```sh
curl --cacert "$HOME/.local/state/pact-local/tls.crt" \
  https://localhost:8443/api/records/summary
```

`Ctrl+C`로 종료합니다. 재시작할 때는 같은 파일과 포트로 `serve` 명령만 실행하세요.
인증서는 7일 후 만료됩니다. 인증서를 교체해도 암호화 키 2개, 기록 서명 키와 DB는 유지해야 합니다.
브라우저에서 `https://localhost:8443/`를 열면 로그인, 거래 조회·다운로드, 알림과 긴급 정지 화면을 사용할 수 있습니다.
로컬 인증서를 브라우저가 신뢰해야 합니다. 자동 에이전트 연결과 실제 PayPal 계정 연결 통합 검증은 아직 남아 있습니다.
`Sign in with this device`를 누르면 브라우저에 서명 키를 만듭니다. 브라우저 데이터를 삭제하면 같은 신원을 잃을 수 있습니다.
서버 시작만으로 PayPal 요청이나 결제가 발생하지 않습니다.
실제 동의 요청에는 브라우저 인증서 신뢰와 PayPal 앱의 콜백 URL 설정도 필요하며, 통합 검증은 남아 있습니다.

계정 연결 화면은 모의 응답으로 검증했습니다. 실제 계정 연결은 다음 순서로 진행하며, 지금 추가로 실행할 필요는 없습니다.

1. `Sign in with this device`로 로그인합니다.
2. 구매자는 `Connect buyer account`, 판매자는 `Connect PayPal seller account`를 선택합니다.
3. PayPal Sandbox에서 의도한 계정으로 동의합니다.
4. 돌아온 화면에서 `Review returned account`를 선택합니다.
5. 계정 식별자를 확인한 뒤 `Sign this account connection`을 선택합니다.

콜백 주소는 `/api/paypal/buyer/callback`, `/api/paypal/merchant/callback`입니다. 구매자 취소 주소는 `/api/paypal/buyer/cancel`입니다.
계정 연결은 PACT 거래 위임과 별개입니다. 구매자 동의는 이후 위임 결제에 쓸 결제수단을 저장합니다.
오류가 발생하면 콜백 주소를 다시 열지 말고 새 동의부터 시작해야 합니다. 이미 교환된 요청은 자동 재시도하지 않습니다.

거래 위임은 로그인 후 `Bounded agent Mandate`에서 등록합니다. 지금 추가로 실행할 작업은 없습니다.

1. 구매자·판매자 역할, 별도 에이전트 공개키, 상대방 Principal을 입력합니다.
2. 거래당 JPY 한도, 유효기간 내 총한도와 만료 시각을 입력합니다.
3. `Review Mandate`로 내용을 확인한 뒤 `Sign this Mandate`를 누릅니다.
4. 표시된 Mandate ID를 보관합니다. 철회할 때 해당 ID로 `Sign Mandate revocation`을 누릅니다.

공개키는 패딩을 포함한 base64url Ed25519 형식입니다. 기기 로그인 키와 다른 키를 사용해야 합니다.
위임 등록만으로 거래나 결제가 발생하지 않습니다. 철회는 새 합의를 막으며, 이미 전송된 결제는 완료될 수 있습니다.

## 서명 완료된 거래 실행

기존 거래에 양측 서명과 결제 권한이 있을 때만 실행하세요. 이 명령은 Sandbox 결제를 발생시킬 수 있습니다.
지금 사용자가 추가로 실행할 작업은 없습니다. 아래 명령은 거래 준비가 끝난 뒤 사용하는 운영 명령입니다.

```sh
export PACT_TRANSACTION_ID='기존 거래 ID'
python -m pact.server work \
  --state-dir "$HOME/.local/state/pact-local" \
  --sandbox-env /home/user/workspace/hackerton/2026-11-paypal-ai/sandbox.env \
  --transaction-id "$PACT_TRANSACTION_ID"
```

서버와 같은 상태 디렉터리와 포트를 사용하세요. 기본 포트는 `8443`이며, 다르면 `--port`를 추가하세요.
결과가 불명확하거나 중단되면 DB와 키를 보존하고 같은 거래 ID로 복구하세요. 새 거래로 결제를 재시도하지 마세요.
종료 코드가 0이어도 JSON의 거래 상태를 확인하세요. `unknown`이나 보류 상태는 결제 완료를 뜻하지 않습니다.
이 명령은 거래 협상이나 위임 서명을 자동으로 만들지 않습니다. 실제 Sandbox 통합 실행 검증은 남아 있습니다.

작성 예외: 사용자 요청에 따라 이 문서를 한국어로 작성했습니다.
Sandbox 저장·결제 한 건을 완료했습니다.
승인 취소와 재동의 녹화도 완료했습니다. 동의 증거의 적합성 판단과 독립 검토·평가는 남아 있습니다.

## 실제 Gemini 협상 검증

`gemini.env`에는 실제 API 키만 입력하세요. 한글 설명이나 예시 문구를 키 값에 넣지 마세요.
키를 채팅에 보내지 마세요.

```sh
cd /home/user/workspace/hackerton/2026-11-paypal-ai
chmod 600 gemini.env
/tmp/pact-opencv-venv/bin/python -m feasibility.gemini_negotiation \
  --gemini-env ./gemini.env \
  --output /tmp/pact-gemini-live.json
```

실제 Gemini로 합의·거절을 확인하고, 이미지 생성과 모의 결제·다운로드까지 검사합니다.
이 명령은 PayPal에 접속하지 않으므로 Sandbox 결제액은 JPY 0입니다. Gemini 사용료는 별도일 수 있습니다.
기존 거래 상태를 사용하는 운영 명령은 [연결 안내](g3-gemini-negotiation-20261024.md)에 있습니다.
운영 명령의 JPY 2500 제한은 기존 누적 결제 허용액을 추가하거나 초기화하지 않습니다.

기존 `gemini-3.8-flash`는 Google 과부하 오류를 반환해 `gemini-3.1-flash-lite`로 모델 항목만 변경했습니다.
실제 AI의 합의와 거절을 확인했으며, API 키는 유지했습니다.

## 실제 판매자 로그인 설정

앞서 안내한 localhost Return URL 등록 요청을 철회합니다. PayPal 설정에는 아래 확정 주소를 사용하세요.
로그인에는 에이전트가 제어하는 서버 브라우저를 사용합니다. PC 포트 포워딩은 필요하지 않습니다.

```text
서비스 주소: https://server-debian-dev.tailffdbc2.ts.net
판매자 Return URL: https://server-debian-dev.tailffdbc2.ts.net/api/paypal/merchant/callback
구매자 복귀 주소: https://server-debian-dev.tailffdbc2.ts.net/api/paypal/buyer/callback
구매자 취소 주소: https://server-debian-dev.tailffdbc2.ts.net/api/paypal/buyer/cancel
```

1. [Sandbox 앱 설정](https://developer.paypal.com/dashboard/applications/sandbox)에서 `sandbox.env`와 같은 Client ID의 앱을 여세요.
2. `Log in with PayPal`을 활성화하고 `Advanced Settings`를 여세요.
3. Return URL에 위의 **판매자 Return URL**을 등록하세요.
4. `PayPal account ID (payer ID)`와 `Account verification status` 공유를 허용하세요.
5. 저장하세요. 키나 비밀번호를 채팅에 보내지 마세요.

구매자 복귀·취소 주소는 앱이 Vault 요청에 자동으로 넣습니다. 로그인 Return URL과 구분하세요.
Privacy policy URL과 User agreement URL 입력을 요구하면 Sandbox 테스트에는 `https://example.com`을 사용할 수 있습니다.
출처: [PayPal 로그인 설정](https://developer.paypal.com/log-in/build/).

서버 브라우저에서 앱 접속, 기기 로그인, 세션 쿠키와 PayPal 방문 후 세션 유지를 확인했습니다.
HTTPS 인증서는 정상 검증되며, 주소의 포트는 기본 HTTPS 포트인 `443`입니다.
이 주소는 Tailscale 내부 전용입니다. 일반 인터넷 공개 주소가 아니며 사용자 PC 접속은 검증하지 않았습니다.

PayPal의 localhost 허용 여부는 확인하지 못했습니다. 이번 주소는 localhost를 사용하지 않습니다.
설정 저장 후 판매자 로그인·정보 제공 동의와 HTTPS 복귀를 실제로 확인했습니다.
`invalid client_id or redirect_uri`와 `invalid scope`는 더 이상 발생하지 않았습니다.
콜백의 추가 `scope` 항목을 앱이 거부하던 문제도 수정했습니다.
이후 계정정보 요청 형식을 수정하고 새 판매자 계정으로 로그인·동의·기기 서명 등록을 완료했습니다.
앱은 계정 소유와 고정 payer ID를 확인합니다. Business 유형이나 결제 가능 여부를 보증하지 않습니다.
구매자의 실제 Vault 동의·토큰 조회·기기 서명 등록도 완료했습니다. 이번 연결 검증의 결제액은 JPY 0입니다.
이후 실제 Gemini 협상부터 이미지 검사·JPY 6 결제·결과물 다운로드까지 한 건의 통합 검증을 완료했습니다.
누적 사용액은 보수적으로 JPY 10, 기존 JPY 2500 한도의 잔여액은 JPY 2490입니다.
지금은 대시보드 설정을 더 바꾸지 않아도 됩니다. 보관 제어와 장애·복구 통합 검증은 남아 있습니다.
상세 기록: [판매자 연결 범위](merchant-verification-scope-20261024.md), [구매자 연결 검증](buyer-vault-live-20261025.md).
거래 결과: [실제 AI·Sandbox 통합 검증](integrated-sandbox-20261025.md).
출처: [PayPal Return URL 일치 조건](https://www.paypal.com/au/cshelp/article/how-do-i-set-a-redirect-url-for-the-paypal-identity-api-ts1995).

앱은 현재 아래 명령으로 실행 중입니다. 재시작할 때 기존 프로세스를 먼저 종료하고 같은 명령을 사용하세요.
이 명령은 결제를 요청하지 않습니다.

```sh
cd /home/user/workspace/hackerton/2026-11-paypal-ai
/tmp/pact-opencv-venv/bin/python -m pact.server serve \
  --state-dir /home/user/.local/state/pact-sandbox \
  --sandbox-env ./sandbox.env \
  --service-origin https://server-debian-dev.tailffdbc2.ts.net \
  --local-tls-proxy --port 3000
```

기존 Tailscale HTTPS 전달 설정은 `443 → http://127.0.0.1:3000`입니다. 앱은 loopback에만 연결합니다.
`--local-tls-proxy`는 이 로컬 HTTPS 프록시를 신뢰합니다. 외부 연결을 받는 HTTP 서버로 바꾸지 마세요.
`work`와 `negotiate`도 같은 상태 디렉터리와 `--service-origin`을 사용해야 합니다.
기존 다른 주소의 DB·키를 덮어쓰거나 거래를 옮기지 마세요. 새 주소용 상태를 별도로 만들었습니다.
이번 조사·접속 검증의 결제액은 JPY 0입니다. 기존 JPY 2500 누적 허용액은 추가되거나 초기화되지 않습니다.
