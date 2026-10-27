const element = id => document.getElementById(id);
const storageName = 'pact-session';
let session = null;
let transaction = null;
let after = 0;
let pending = false;
let accountChallenge = null;
let mandateDraft = null;
let imageRequest = null;
let callback = /^\/api\/paypal\/(buyer\/(callback|cancel)|merchant\/callback)$/.test(location.pathname)
  ? location.pathname + location.search : null;
if (callback) history.replaceState(null, '', '/');

function base64(bytes) {
  return btoa(String.fromCharCode(...new Uint8Array(bytes))).replaceAll('+', '-').replaceAll('/', '_');
}

function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (value !== null && typeof value === 'object') {
    return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

async function deviceKey() {
  const database = await new Promise((resolve, reject) => {
    const request = indexedDB.open('pact-device', 1);
    request.onupgradeneeded = () => request.result.createObjectStore('keys');
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(new Error('Device key storage is unavailable.'));
    request.onblocked = () => reject(new Error('Close other PACT tabs and retry.'));
  });
  const read = () => new Promise((resolve, reject) => {
    const request = database.transaction('keys').objectStore('keys').get('identity');
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(new Error('Cannot read the device key.'));
  });
  try {
    let key = await read();
    if (key) return key;
    key = await crypto.subtle.generateKey('Ed25519', false, ['sign', 'verify']);
    try {
      await new Promise((resolve, reject) => {
        const write = database.transaction('keys', 'readwrite');
        write.objectStore('keys').add(key, 'identity');
        write.oncomplete = resolve;
        write.onabort = () => reject(write.error);
        write.onerror = () => {};
      });
    } catch (error) {
      if (error?.name !== 'ConstraintError') throw new Error('Cannot save the device key.');
    }
    return await read();
  } finally {
    database.close();
  }
}

function showSession() {
  const signedIn = session !== null;
  element('principal').textContent = signedIn ? `Principal: ${session.principal}` : 'Signed out.';
  element('login').disabled = signedIn;
  element('logout').disabled = !signedIn;
  for (const id of ['workspace', 'activity', 'safety', 'accounts', 'mandates', 'image-exchange']) element(id).hidden = !signedIn || !!session.support_operator;
  element('operator').hidden = !signedIn || !session.support_operator;
  element('account-return').hidden = !signedIn || !callback;
}

function clearSession() {
  session = null;
  transaction = null;
  after = 0;
  accountChallenge = null;
  imageRequest = null;
  for (const id of ['image-request-form', 'image-load-form', 'image-upload-form']) element(id).reset();
  element('image-upload-form').hidden = true;
  element('image-state').textContent = 'No image request loaded.';
  element('image-conditions').textContent = '';
  element('image-report').textContent = '';
  clearMandateDraft();
  element('mandate-form').reset();
  element('revoke-form').reset();
  element('mandate-state').textContent = 'No Mandate submitted from this view.';
  callback = null;
  try { sessionStorage.removeItem(storageName); } catch { /* Storage can be disabled by browser policy. */ }
  element('transaction').hidden = true;
  for (const id of ['agreement', 'checks', 'payment', 'retention', 'support', 'facts', 'notices']) element(id).replaceChildren();
  element('support-form').reset();
  element('support-cases').textContent = '';
  element('support-review-form').reset();
  element('activity-state').textContent = 'No activity loaded.';
  element('account-target').textContent = '';
  element('account-target').hidden = true;
  element('account-confirm').hidden = true;
  element('account-state').textContent = 'No account connection recorded in this view.';
  showSession();
}

async function api(path, body, contentType = 'application/json') {
  if (session && session.expires <= Date.now() / 1000) {
    clearSession();
    throw new Error('Your session expired. Sign in again.');
  }
  const options = {credentials: 'same-origin', cache: 'no-store', redirect: 'error', headers: {'Accept': 'application/json'}};
  if (body !== undefined) {
    options.method = 'POST';
    options.headers['Content-Type'] = contentType;
    if (session) options.headers['X-PACT-CSRF'] = session.csrf_token;
    options.body = contentType === 'application/json' ? JSON.stringify(body) : body;
  }
  const response = await fetch(path, options);
  if (!response.ok) throw new Error(`Request rejected (${response.status}). Refresh your session if it expired.`);
  return response.json();
}

async function loadImageRequest() {
  imageRequest = null;
  element('image-upload-form').hidden = true;
  element('image-conditions').textContent = '';
  element('image-report').textContent = '';
  const identifier = encodeURIComponent(element('image-load-id').value.trim());
  const conditions = await api(`/api/image-requests/${identifier}/conditions`);
  const report = await api(`/api/image-requests/${identifier}`);
  imageRequest = conditions;
  element('image-conditions').textContent = JSON.stringify(conditions, null, 2);
  element('image-report').textContent = JSON.stringify(report, null, 2);
  const remaining = report.submissions_remaining ?? conditions.request.rule.max_input_submissions;
  const state = {awaiting_input: 'Awaiting the provider source.', resubmit: 'Source rejected. Submit a replacement.',
    ready_to_sign: 'Source accepted. Ready for the agents to sign an agreement.', closed: 'Image request closed.'};
  element('image-state').textContent = `${state[report.status] || report.status} ${remaining} submissions remain. ${(report.reason_codes || []).join(', ')}`;
  element('image-upload-form').hidden = conditions.provider !== session.principal
    || !['awaiting_input', 'resubmit'].includes(report.status);
  element('transaction-id').value = conditions.transaction_id;
  element('status').textContent = 'Image conditions and preflight status loaded.';
}

async function createImageRequest() {
  const color = element('image-background').value;
  const request = {schema_version: 1, request_id: element('image-request-id').value.trim(),
    width: Number(element('image-width').value), height: Number(element('image-height').value),
    background_rgb: [1, 3, 5].map(index => parseInt(color.slice(index, index + 2), 16)),
    rule: await api('/api/image-rule')};
  await api('/api/image-requests', {request, transaction_id: element('image-transaction').value.trim(),
    provider: element('image-provider').value.trim()});
  element('image-load-id').value = request.request_id;
  await loadImageRequest();
}

async function submitImageSource() {
  if (!imageRequest || imageRequest.provider !== session.principal) throw new Error('Load your provider request first.');
  const file = element('image-source').files[0];
  if (!file || file.type !== 'image/png') throw new Error('Select a PNG source.');
  await api(`/api/image-requests/${encodeURIComponent(imageRequest.request.request_id)}/input`, file, 'image/png');
  element('image-upload-form').reset();
  await loadImageRequest();
}

function validateChallenge(challenge, publicKey, purpose, targetFields) {
  const expected = ['browser_sha256', 'expires', 'nonce', 'public_key', 'purpose', 'schema_version', 'service', 'target'];
  if (!challenge || Object.keys(challenge).sort().join(',') !== expected.join(',') || challenge.schema_version !== 1
      || challenge.service !== location.origin || challenge.purpose !== purpose || challenge.public_key !== publicKey
      || typeof challenge.target !== 'object' || challenge.target === null || Array.isArray(challenge.target)
      || Object.keys(challenge.target).sort().join(',') !== [...targetFields].sort().join(',')
      || targetFields.some(name => typeof challenge.target[name] !== 'string'
        || !/^[A-Za-z0-9_-]{1,128}$/.test(challenge.target[name]))
      || !Number.isInteger(challenge.expires) || challenge.expires <= Date.now() / 1000
      || challenge.expires > Date.now() / 1000 + 305 || !/^[A-Za-z0-9_-]{20,128}$/.test(challenge.nonce)
      || !/^[a-f0-9]{64}$/.test(challenge.browser_sha256)) throw new Error('The signing challenge is invalid.');
}

async function login() {
  const key = await deviceKey();
  const publicKey = base64(await crypto.subtle.exportKey('raw', key.publicKey));
  const {challenge} = await api('/api/login/challenge', {public_key: publicKey});
  validateChallenge(challenge, publicKey, 'login', []);
  const signature = base64(await crypto.subtle.sign('Ed25519', key.privateKey, new TextEncoder().encode(canonical(challenge))));
  session = await api('/api/login/finish', {nonce: challenge.nonce, signature});
  sessionStorage.setItem(storageName, JSON.stringify(session));
  showSession();
  element('status').textContent = 'Signed in with this device.';
  await (session.support_operator ? supportCases() : activity());
}

async function connectAccount(role) {
  accountChallenge = null;
  element('account-confirm').hidden = true;
  element('account-target').hidden = true;
  const result = await api(`/api/paypal/${role}/start`, {});
  const url = new URL(result.authorization_url);
  if (url.protocol !== 'https:' || !['sandbox.paypal.com', 'www.sandbox.paypal.com'].includes(url.host)
      || url.username || url.password || url.hash
      || url.pathname !== (role === 'buyer' ? '/agreements/approve' : '/connect')) {
    throw new Error('The Sandbox consent address is invalid.');
  }
  location.assign(url.href);
}

async function reviewAccount() {
  const path = callback;
  callback = null;
  element('account-return').hidden = true;
  if (!path) throw new Error('Start fresh account consent.');
  const result = await api(path);
  if (path.startsWith('/api/paypal/buyer/cancel?')) {
    element('account-state').textContent = 'Buyer consent cancelled. No account connection was signed.';
    element('status').textContent = 'Buyer consent cancelled.';
    return;
  }
  const role = path.startsWith('/api/paypal/buyer/') ? 'buyer' : 'merchant';
  const purpose = role === 'buyer' ? 'buyer_account_binding' : 'merchant_registration';
  const fields = role === 'buyer' ? ['account_binding_version', 'payer_id'] : ['registration', 'merchant_id'];
  const key = await deviceKey();
  const publicKey = base64(await crypto.subtle.exportKey('raw', key.publicKey));
  validateChallenge(result.challenge, publicKey, purpose, fields);
  accountChallenge = {role, challenge: result.challenge, purpose, fields};
  element('account-target').textContent = JSON.stringify(result.challenge.target, null, 2);
  element('account-target').hidden = false;
  element('account-confirm').hidden = false;
  element('account-state').textContent = 'Review the verified account identifiers before signing this connection.';
  element('status').textContent = 'Account returned. Review its identifiers before signing.';
}

async function confirmAccount() {
  const pendingAccount = accountChallenge;
  accountChallenge = null;
  element('account-confirm').hidden = true;
  if (!pendingAccount) throw new Error('Start fresh account consent.');
  const {role, challenge, purpose, fields} = pendingAccount;
  const key = await deviceKey();
  validateChallenge(challenge, base64(await crypto.subtle.exportKey('raw', key.publicKey)), purpose, fields);
  const signature = base64(await crypto.subtle.sign('Ed25519', key.privateKey, new TextEncoder().encode(canonical(challenge))));
  const result = await api(`/api/paypal/${role}/register`, {nonce: challenge.nonce, signature});
  element('account-state').textContent = `Account connected: ${JSON.stringify(result)}`;
  element('status').textContent = 'Account connection recorded. No PACT transaction was authorized.';
}

async function activity() {
  const result = await api(`/api/notifications?after=${after}&limit=50`);
  for (const item of result.items) {
    const row = document.createElement('li');
    row.textContent = `${new Date(item.recorded * 1000).toLocaleString()} · ${item.kind} · ${item.target}`;
    element('notices').append(row);
  }
  after = result.next_after;
  element('activity-state').textContent = result.has_more ? 'More activity is available. Refresh to load it.' : 'Activity is current.';
}

function clearMandateDraft() {
  mandateDraft = null;
  element('mandate-document').textContent = '';
  element('mandate-document').hidden = true;
  element('mandate-confirm').hidden = true;
}

async function reviewMandate() {
  clearMandateDraft();
  const key = await deviceKey();
  const publicKey = base64(await crypto.subtle.exportKey('raw', key.publicKey));
  const agentKey = element('agent-key').value.trim();
  if (!/^[A-Za-z0-9_-]{43}=$/.test(agentKey)) throw new Error('Enter a padded base64url Ed25519 public key.');
  const decoded = Uint8Array.from(atob(agentKey.replaceAll('-', '+').replaceAll('_', '/')), value => value.charCodeAt(0));
  if (decoded.length !== 32 || base64(decoded) !== agentKey || agentKey === publicKey) {
    throw new Error('Use a separate, valid agent public key.');
  }
  const role = element('mandate-role').value;
  const counterparty = element('counterparty').value.trim();
  const transactionLimit = Number(element('transaction-limit').value);
  const periodLimit = Number(element('period-limit').value);
  const now = Math.floor(Date.now() / 1000);
  const expires = Math.floor(new Date(element('mandate-expiry').value).getTime() / 1000);
  if (!session || !['buyer', 'provider'].includes(role) || !/^[A-Za-z0-9_-]{1,128}$/.test(counterparty)
      || counterparty === session.principal || !Number.isSafeInteger(expires) || expires <= now || expires > 1e12
      || [transactionLimit, periodLimit].some(value => !Number.isSafeInteger(value) || value < 1 || value > 1e12)
      || transactionLimit > periodLimit) throw new Error('Check the role, counterparty, JPY limits, and future expiry.');
  mandateDraft = {schema_version: 1, service: location.origin, purpose: 'mandate', principal: session.principal,
    user_key: publicKey, agent_key: agentKey, role, task: 'negotiated_raster', currency: 'JPY',
    transaction_limit: transactionLimit, not_before: now, expires, counterparties: [counterparty],
    periods: [{id: 'demo', starts: now, ends: expires, amount_limit: periodLimit}]};
  element('mandate-document').textContent = JSON.stringify(mandateDraft, null, 2);
  element('mandate-document').hidden = false;
  element('mandate-confirm').hidden = false;
  element('status').textContent = 'Review the agent key, counterparty, limits, and expiry before signing.';
}

async function confirmMandate() {
  const document = mandateDraft;
  if (!document || !session || document.principal !== session.principal || document.expires <= Date.now() / 1000) {
    clearMandateDraft();
    throw new Error('Review a current Mandate before signing.');
  }
  const key = await deviceKey();
  if (base64(await crypto.subtle.exportKey('raw', key.publicKey)) !== document.user_key) {
    throw new Error('The device identity changed. Sign in again.');
  }
  const bytes = new TextEncoder().encode(canonical(document));
  const identifier = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)))
    .map(value => value.toString(16).padStart(2, '0')).join('');
  element('mandate-state').textContent = `Mandate ID: ${identifier}. Registration is not yet confirmed.`;
  const signature = base64(await crypto.subtle.sign('Ed25519', key.privateKey, bytes));
  const result = await api('/api/mandates', {document, signature});
  if (result.mandate !== identifier) throw new Error('The returned Mandate ID does not match the signed document.');
  element('mandate-state').textContent = `Registered Mandate: ${identifier}`;
  element('revoke-id').value = identifier;
  element('mandate-confirm').hidden = true;
  element('status').textContent = 'Mandate registered. No transaction or payment was created.';
  await activity();
}

async function revokeMandate() {
  const identifier = element('revoke-id').value.trim();
  if (!session || !/^[a-f0-9]{64}$/.test(identifier)) throw new Error('Enter the existing Mandate ID.');
  const key = await deviceKey();
  const document = {schema_version: 1, service: location.origin, purpose: 'revoke_mandate',
    principal: session.principal, mandate: identifier};
  const signature = base64(await crypto.subtle.sign('Ed25519', key.privateKey, new TextEncoder().encode(canonical(document))));
  await api('/api/mandates/revoke', {document, signature});
  clearMandateDraft();
  element('mandate-state').textContent = `Revoked Mandate: ${identifier}`;
  element('status').textContent = 'Mandate revoked. Existing agreements remain. A payment already submitted can still complete.';
  await activity();
}

function render(detail) {
  transaction = detail;
  const agreement = detail.agreement.agreement;
  element('transaction-heading').textContent = `Transaction ${detail.transaction_id}`;
  element('facts').replaceChildren();
  const facts = {'Stage': detail.state, 'Role': detail.role, 'Price': `JPY ${agreement.amount_minor}`,
    'Remaining limit': `JPY ${detail.budget.remaining}`, 'Reserved': `JPY ${detail.budget.reserved}`,
    'Consumed': `JPY ${detail.budget.consumed}`, 'Observed': new Date(detail.observed_at * 1000).toLocaleString()};
  for (const [label, value] of Object.entries(facts)) {
    const name = document.createElement('dt');
    const description = document.createElement('dd');
    name.textContent = label;
    description.textContent = value;
    element('facts').append(name, description);
  }
  for (const name of ['agreement', 'checks', 'payment']) element(name).textContent = JSON.stringify(detail[name], null, 2);
  element('retention').textContent = JSON.stringify(detail.retention, null, 2);
  element('support').textContent = JSON.stringify(detail.support, null, 2);
  const retainDate = new Date(Math.max(detail.retention.retention_until, detail.observed_at + 1) * 1000);
  if (retainDate.getUTCHours() || retainDate.getUTCMinutes() || retainDate.getUTCSeconds()) retainDate.setUTCDate(retainDate.getUTCDate() + 1);
  element('retention-until').value = retainDate.toISOString().slice(0, 10);
  element('retention-release').disabled = !detail.retention.holds.some(hold => hold.principal === session.principal);
  let next = 'Refresh this transaction to read its latest recorded status.';
  if (detail.payment.recovery) next = 'The payment result needs verification. Keep the reservation. Do not submit another payment.';
  else if (detail.support.delivery_unresolved) next = 'Delivery remains unresolved. Retry the output download or request support below. Do not pay again.';
  else if (detail.state === 'paid') next = 'Payment is recorded. Download the output and evidence below.';
  else if (detail.state === 'closed') next = 'The payment path is closed. Review the recorded closure evidence.';
  else if (detail.deadline_expired) next = 'The agreement deadline has passed. Review payment and closure status.';
  if (detail.stopped.buyer || detail.stopped.provider) next += ' A Principal has stopped new transaction actions.';
  element('next-action').textContent = next;
  for (const kind of ['input', 'output']) element(`${kind}-download`).disabled = !detail.files[kind].download_permitted;
  element('transaction').hidden = false;
}

async function loadTransaction() {
  transaction = null;
  element('transaction').hidden = true;
  const identifier = element('transaction-id').value.trim();
  if (!identifier || identifier.length > 128) throw new Error('Enter a transaction ID.');
  render(await api(`/api/transactions/${encodeURIComponent(identifier)}`));
}

async function download(kind) {
  if (!transaction) throw new Error('Load a transaction first.');
  const identifier = transaction.transaction_id;
  const recovery = kind === 'output' && transaction.state === 'paid'
    ? ' Payment remains recorded. Retry this download. If it still fails, retain evidence and request support with this transaction ID. Do not pay again.' : '';
  const response = await fetch(`/api/transactions/${encodeURIComponent(identifier)}/${kind}`, {
    credentials: 'same-origin', cache: 'no-store', redirect: 'error'}).catch(() => {
    throw new Error('Download connection failed.' + recovery);
  });
  if (!response.ok) {
    if (kind === 'output') render(await api(`/api/transactions/${encodeURIComponent(identifier)}`));
    throw new Error(`Download rejected (${response.status}).` + recovery);
  }
  const blob = await response.blob();
  if (kind !== 'evidence') {
    const hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', await blob.arrayBuffer())))
      .map(value => value.toString(16).padStart(2, '0')).join('');
    if (hash !== transaction.files[kind].sha256) throw new Error('The downloaded file hash does not match the record.' + recovery);
  }
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.href = url;
  link.download = kind === 'evidence' ? 'pact-evidence.json' : `${kind}.png`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  if (kind === 'output') render(await api(`/api/transactions/${encodeURIComponent(identifier)}`));
  element('status').textContent = kind === 'evidence' ? 'Evidence downloaded. Use the offline verifier to check signatures.'
    : 'File downloaded. Its SHA-256 matches the transaction record.';
}

async function changeRetention(action) {
  if (!transaction) throw new Error('Load a transaction first.');
  const retention_until = Date.parse(element('retention-until').value + 'T00:00:00Z') / 1000;
  if (!Number.isInteger(retention_until)) throw new Error('Select a retention date.');
  await api(`/api/transactions/${encodeURIComponent(transaction.transaction_id)}/retention`, {action, retention_until});
  await loadTransaction();
  element('status').textContent = action === 'hold' ? 'Evidence hold recorded.' : 'Your evidence hold was released. Automatic deletion remains disabled.';
}

async function submitSupport() {
  if (!transaction) throw new Error('Load a transaction first.');
  await api(`/api/transactions/${encodeURIComponent(transaction.transaction_id)}/support`, {
    action: element('support-action').value, message: element('support-message').value});
  element('support-message').value = '';
  await loadTransaction();
  element('status').textContent = 'Support action recorded. No payment was submitted.';
}

async function supportCases() {
  element('support-cases').textContent = JSON.stringify(await api('/api/support/cases'), null, 2);
}

async function reviewSupport() {
  const identifier = element('support-transaction').value.trim();
  const action = element('support-operator-action').value;
  const next_check_at = Date.parse(element('support-next-check').value) / 1000;
  if (!/^[A-Za-z0-9_-]{1,128}$/.test(identifier) || !Number.isInteger(next_check_at)
      || next_check_at <= Date.now() / 1000) throw new Error('Enter a transaction ID and a future check time.');
  await api(`/api/support/cases/${encodeURIComponent(identifier)}/${action}`, {next_check_at});
  await supportCases();
  element('status').textContent = 'Support action recorded. This action cannot submit a new payment.';
}

async function act(action) {
  if (pending) return;
  pending = true;
  element('status').textContent = 'Request in progress.';
  try {
    await action();
  } catch (error) {
    element('status').textContent = error.message || 'The request failed.';
  } finally {
    pending = false;
  }
}

element('login').onclick = () => act(login);
element('logout').onclick = () => act(async () => {
  try { await api('/api/logout', {}); } finally { clearSession(); }
  element('status').textContent = 'Signed out. The device signing key remains in this browser.';
});
element('lookup').onsubmit = event => { event.preventDefault(); act(async () => {
  await loadTransaction();
  element('status').textContent = 'Transaction loaded.';
}); };
element('refresh').onclick = () => act(async () => {
  await activity();
  element('status').textContent = 'Activity refreshed.';
});
element('buyer-connect').onclick = () => act(() => connectAccount('buyer'));
element('merchant-connect').onclick = () => act(() => connectAccount('merchant'));
element('account-return').onclick = () => act(reviewAccount);
element('account-confirm').onclick = () => act(confirmAccount);
element('mandate-form').oninput = clearMandateDraft;
element('mandate-form').onsubmit = event => { event.preventDefault(); act(reviewMandate); };
element('image-request-form').onsubmit = event => { event.preventDefault(); act(createImageRequest); };
element('image-load-form').onsubmit = event => { event.preventDefault(); act(loadImageRequest); };
element('image-upload-form').onsubmit = event => { event.preventDefault(); act(submitImageSource); };
element('mandate-confirm').onclick = () => act(confirmMandate);
element('revoke-form').onsubmit = event => { event.preventDefault(); act(revokeMandate); };
element('stop').onclick = () => act(async () => {
  await api('/api/stop', {});
  element('status').textContent = 'Emergency stop recorded. A payment already submitted can still complete.';
  await activity();
  if (transaction) await loadTransaction();
});
for (const kind of ['input', 'output', 'evidence']) element(`${kind}-download`).onclick = () => act(() => download(kind));
for (const action of ['hold', 'release']) element(`retention-${action}`).onclick = () => act(() => changeRetention(action));
element('support-form').onsubmit = event => { event.preventDefault(); act(submitSupport); };
element('support-refresh').onclick = () => act(supportCases);
element('support-review-form').onsubmit = event => { event.preventDefault(); act(reviewSupport); };

try {
  const stored = JSON.parse(sessionStorage.getItem(storageName));
  if (stored && typeof stored.principal === 'string' && typeof stored.csrf_token === 'string'
      && Number.isInteger(stored.expires) && stored.expires > Date.now() / 1000) session = stored;
  else sessionStorage.removeItem(storageName);
  showSession();
  if (session) act(session.support_operator ? supportCases : activity);
  if (callback && !session) element('status').textContent = 'The original session is unavailable. Sign in and start fresh account consent.';
} catch {
  clearSession();
  element('status').textContent = 'Session storage is unavailable. Enable browser storage before signing in.';
}
