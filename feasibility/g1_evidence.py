"""G1 manifest validation without external execution."""
import datetime
import json
import sys
from typing import NoReturn

_STAGES = ("order", "authorization", "capture", "query", "cancellation_capability")
_HASH = set("0123456789abcdef")


def _invalid() -> NoReturn:
    raise ValueError("invalid_manifest")


def _identifier(value):
    return isinstance(value, str) and 1 <= len(value) <= 128


def _description(value):
    return isinstance(value, str) and len(value) <= 2048


def _hash(value):
    return isinstance(value, str) and len(value) == 64 and set(value) <= _HASH


def _time(value) -> datetime.datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        _invalid()
    try:
        return datetime.datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        _invalid()


def _keys(value, allowed):
    if not isinstance(value, dict) or set(value) - set(allowed):
        _invalid()


def _reference(value, official=False):
    keys = ["path", "sha256", "evidence_class", "reviewer"]
    if official:
        keys += ["section", "captured_at"]
    _keys(value, keys)
    path = value.get("path")
    if not isinstance(path, str) or not path or path.startswith("/") or ".." in path.split("/"):
        _invalid()
    if not _hash(value.get("sha256")) or value.get("evidence_class") not in ("local", "mock", "real_external"):
        _invalid()
    if not _identifier(value.get("reviewer")):
        _invalid()
    if official and (not _description(value.get("section")) or _time(value.get("captured_at")) is None):
        _invalid()


def _missing(record, names, output, prefix):
    for name in names:
        if name not in record:
            output.append(prefix + name)


def validate_manifest(manifest):
    if not isinstance(manifest, dict):
        _invalid()
    top = {"schema_version", "experiment", "procedure", "accounts", "consent", "expected", "operations", "limitations"}
    if set(manifest) - top or manifest.get("schema_version") != 1 or isinstance(manifest.get("schema_version"), bool):
        _invalid()
    limitations = manifest.get("limitations", [])
    if not isinstance(limitations, list) or len(limitations) > 256 or not all(_description(item) for item in limitations):
        _invalid()
    missing, inconsistent = [], []
    for name in top - {"schema_version", "limitations"}:
        if name not in manifest:
            missing.append(name)

    experiment = manifest.get("experiment")
    started = ended = None
    if "experiment" in manifest:
        experiment = manifest["experiment"]
        _keys(experiment, ["id", "evidence_class", "actor", "started_at", "ended_at"])
        if not _identifier(experiment.get("id")) or experiment.get("evidence_class") not in ("local", "mock", "real_external") or not _identifier(experiment.get("actor")):
            _invalid()
        started, ended = _time(experiment.get("started_at")), _time(experiment.get("ended_at"))
        if ended < started:
            inconsistent.append("experiment_chronology_invalid")

    refs, bindings = {}, {}
    procedure = manifest.get("procedure")
    if "procedure" in manifest:
        procedure = manifest["procedure"]
        _keys(procedure, ["product", "references", "bindings", "reviewer"])
        if not _identifier(procedure.get("product")) or not _identifier(procedure.get("reviewer")) or not isinstance(procedure.get("references"), list) or not isinstance(procedure.get("bindings"), list):
            _invalid()
        for reference in procedure["references"]:
            _reference(reference, True)
            refs.setdefault(reference["sha256"], reference)
        fields = ["stage", "reference_sha256", "source_section", "request_fields", "response_fields", "final_statuses", "recovery_notes"]
        for binding in procedure["bindings"]:
            _keys(binding, fields)
            stage = binding.get("stage")
            if stage not in _STAGES or stage in bindings or not _hash(binding.get("reference_sha256")) or not _description(binding.get("source_section")):
                _invalid()
            if not all(isinstance(binding.get(name), list) and all(_description(value) for value in binding[name]) for name in fields[3:]):
                _invalid()
            bindings[stage] = binding
            if binding["reference_sha256"] not in refs:
                missing.append("procedure.binding_ref")
        if set(bindings) != set(_STAGES):
            missing.append("procedure.bindings")

    accounts = manifest.get("accounts")
    if "accounts" in manifest:
        accounts = manifest["accounts"]
        _keys(accounts, ["payer_ref", "merchant_ref", "application_ref", "capabilities", "permissions"])
        if not all(_identifier(accounts.get(name)) for name in ("payer_ref", "merchant_ref", "application_ref")):
            _invalid()
        if not all(isinstance(accounts.get(name), list) and all(_identifier(value) for value in accounts[name]) for name in ("capabilities", "permissions")):
            _invalid()

    consent = manifest.get("consent")
    if "consent" in manifest:
        consent = manifest["consent"]
        fields = ["evidence", "session_ref", "token_type", "storage_scope", "payer_linkage", "additional_approvals"]
        _keys(consent, fields)
        _reference(consent.get("evidence"))
        if not all(_identifier(consent.get(name)) for name in fields[1:5]):
            _invalid()
        if not isinstance(consent.get("additional_approvals"), int) or isinstance(consent["additional_approvals"], bool) or consent["additional_approvals"] < 0:
            _invalid()
        if consent["additional_approvals"]:
            missing.append("consent.additional_approvals")

    expected = manifest.get("expected")
    if "expected" in manifest:
        expected = manifest["expected"]
        _keys(expected, ["amount_minor", "currency", "merchant_ref", "payer_ref"])
        amount = expected.get("amount_minor")
        if not isinstance(amount, int) or isinstance(amount, bool) or not 1 <= amount <= 2147483647:
            _invalid()
        if expected.get("currency") not in ("USD", "JPY") or not _identifier(expected.get("merchant_ref")) or not _identifier(expected.get("payer_ref")):
            _invalid()

    operations = manifest.get("operations")
    known = {"order_ref": None, "authorization_ref": None, "capture_ref": None}
    if "operations" in manifest:
        operations = manifest["operations"]
        if not isinstance(operations, list) or len(operations) > 256:
            _invalid()
        fields = ["stage", "actor", "at", "binding_ref", "request_ref", "response_ref", "request_id", "order_ref", "authorization_ref", "capture_ref", "amount_minor", "currency", "merchant_ref", "payer_ref", "observed_status", "outcome", "idempotency_support", "retention_seconds", "limitation_codes"]
        seen, request_ids, last = set(), set(), started
        for index, operation in enumerate(operations):
            _keys(operation, fields)
            _missing(operation, fields, missing, "operation.")
            stage = operation.get("stage")
            if stage not in _STAGES or stage in seen:
                _invalid()
            seen.add(stage)
            if index < len(_STAGES) and stage != _STAGES[index]:
                inconsistent.append("operation_order_invalid")
            if "actor" in operation and not _identifier(operation["actor"]):
                _invalid()
            if "at" in operation:
                _time(operation["at"])
            if "binding_ref" in operation and not _hash(operation["binding_ref"]):
                _invalid()
            for name in ("request_ref", "response_ref"):
                if name in operation:
                    _reference(operation[name])
            for name in ("request_id", "merchant_ref", "payer_ref", "observed_status"):
                if name in operation and not _identifier(operation[name]):
                    _invalid()
            if "amount_minor" in operation:
                amount = operation["amount_minor"]
                if not isinstance(amount, int) or isinstance(amount, bool) or not 1 <= amount <= 2147483647:
                    _invalid()
            if "currency" in operation and operation["currency"] not in ("USD", "JPY"):
                _invalid()
            if "outcome" in operation and operation["outcome"] not in ("observed_success", "observed_failure", "unknown", "capability_only"):
                _invalid()
            if "limitation_codes" in operation and (not isinstance(operation["limitation_codes"], list) or not all(_identifier(code) for code in operation["limitation_codes"])):
                _invalid()
            if "idempotency_support" in operation and operation["idempotency_support"] is not None and not isinstance(operation["idempotency_support"], bool):
                _invalid()
            if "retention_seconds" in operation:
                retention = operation["retention_seconds"]
                if retention is not None and (not isinstance(retention, int) or isinstance(retention, bool) or retention < 0):
                    _invalid()
            for field in ("order_ref", "authorization_ref", "capture_ref"):
                if field in operation and operation[field] is not None and not _identifier(operation[field]):
                    _invalid()
            required = ("actor", "at", "binding_ref", "request_ref", "response_ref", "request_id", "merchant_ref", "payer_ref", "observed_status", "outcome", "amount_minor", "currency", "limitation_codes")
            if any(name not in operation for name in required):
                continue
            if not _identifier(operation["actor"]) or not _identifier(operation["request_id"]) or not _identifier(operation["merchant_ref"]) or not _identifier(operation["payer_ref"]) or not _identifier(operation["observed_status"]) or not _hash(operation["binding_ref"]):
                _invalid()
            at = _time(operation["at"])
            if (last is not None and at < last) or (ended is not None and at > ended):
                inconsistent.append("operation_chronology_invalid")
            last = at
            _reference(operation["request_ref"])
            _reference(operation["response_ref"])
            if operation["request_id"] in request_ids:
                inconsistent.append("request_id_duplicate")
            request_ids.add(operation["request_id"])
            if operation["binding_ref"] not in refs or bindings.get(stage, {}).get("reference_sha256") != operation["binding_ref"]:
                missing.append("operation.binding_ref")
            amount = operation["amount_minor"]
            if not isinstance(amount, int) or isinstance(amount, bool) or not 1 <= amount <= 2147483647 or operation["currency"] not in ("USD", "JPY"):
                _invalid()
            if expected is not None and (amount != expected["amount_minor"] or operation["currency"] != expected["currency"] or operation["merchant_ref"] != expected["merchant_ref"] or operation["payer_ref"] != expected["payer_ref"]):
                inconsistent.append("operation_linkage_inconsistent")
            if operation["outcome"] not in ("observed_success", "observed_failure", "unknown", "capability_only"):
                _invalid()
            if operation["outcome"] in ("unknown", "observed_failure"):
                missing.append("operation.observation")
            codes = operation["limitation_codes"]
            if not isinstance(codes, list) or not all(_identifier(code) for code in codes):
                _invalid()
            for field, code in (("order_ref", "order_unknown"), ("authorization_ref", "authorization_unknown"), ("capture_ref", "capture_unknown")):
                value = operation.get(field)
                if value is None:
                    if code not in codes:
                        _invalid()
                    missing.append("operation." + field)
                elif not _identifier(value):
                    _invalid()
                elif known[field] is None:
                    known[field] = value
                elif known[field] != value:
                    inconsistent.append("operation_linkage_inconsistent")
            idem, retention = operation.get("idempotency_support"), operation.get("retention_seconds")
            if idem is not None and not isinstance(idem, bool):
                _invalid()
            if retention is not None and (not isinstance(retention, int) or isinstance(retention, bool) or retention < 0):
                _invalid()
            if (idem is None and "idempotency_unknown" not in codes) or (retention is None and "retention_unknown" not in codes):
                _invalid()
            if idem is None or retention is None:
                missing.append("operation.capability")
        if set(seen) != set(_STAGES):
            missing.append("operations")

    if accounts is not None and expected is not None and (accounts["payer_ref"] != expected["payer_ref"] or accounts["merchant_ref"] != expected["merchant_ref"]):
        inconsistent.append("account_linkage_inconsistent")
    if accounts is not None and consent is not None and accounts["payer_ref"] != consent["payer_linkage"]:
        inconsistent.append("consent_linkage_inconsistent")
    status = "inconsistent" if inconsistent else "incomplete" if missing else "complete"
    return {"status": status, "missing_fields": missing, "inconsistencies": inconsistent, "limitations": list(limitations)}


def _no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate")
        result[key] = value
    return result


def main(argv):
    if len(argv) != 1 or not argv[0].endswith(".json"):
        print("invalid input. external review required.")
        return 2
    try:
        with open(argv[0], "rb") as stream:
            raw = stream.read(1048577)
        if len(raw) >= 1048577:
            raise ValueError("input")
        result = validate_manifest(json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicates))
    except Exception:
        print("invalid input. external review required.")
        return 2
    print(result["status"] + ". external review required.")
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
