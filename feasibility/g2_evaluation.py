"""G2 batch evidence evaluation."""
import datetime
from typing import NoReturn

_ATTACKS = {"transparent", "unchanged", "deleted_foreground", "residual_background", "replacement_object", "resized", "boundary_damaged"}
_CLASSES = _ATTACKS | {"normal", "unsupported"}
_CATEGORIES = {"complex_backgrounds", "shadows", "translucency", "multiple_objects", "invalid_formats"}
_HASH = set("0123456789abcdef")
_METRICS = {"background_alpha": {"numerator", "denominator"}, "foreground_alpha": {"numerator", "denominator"}, "foreground_rgb_error": {"numerator", "denominator", "pixel_denominator"}}
_FORMAT = {"max_encoded_bytes":8388608,"min_dimension":64,"max_dimension":1024,"max_pixels":1048576,"bit_depth":8,"color_types":[2,6],"compression_method":0,"filter_method":0,"interlace_method":0,"scanline_filters":[0,1,2,3,4]}
_RULE_IDS = {"g2-v1":"g2-rule.v1.json", "g2-v2":"g2-rule.v2.json"}
_REASONS = ("provenance_incomplete", "independent_identity_invalid", "chronology_invalid", "calibration_overlap", "case_coverage_incomplete", "result_coverage_incomplete", "first_run_coverage_incomplete", "independent_support_unknown", "independent_label_unknown", "unsupported_category_incomplete", "evidence_class_mismatch")


def _invalid() -> NoReturn:
    raise ValueError("invalid_evaluation")


def _hash(value):
    return isinstance(value, str) and len(value) == 64 and set(value) <= _HASH


def _time(value) -> datetime.datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        _invalid()
    try:
        return datetime.datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        _invalid()


def _same(actual, expected):
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(_same(actual[key], expected[key]) for key in expected)
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(_same(value, item) for value, item in zip(actual, expected))
    return actual == expected


def _result(status, evidence, counts, unsupported, codes):
    return {"status":status, "evidence_class":evidence, "counts":counts, "denominators":{"normal":20,"attack":140,"unsupported":unsupported}, "reason_codes":codes, "gate_review_required":True}


def _metric(value, keys):
    if not isinstance(value, dict) or set(value) != keys:
        _invalid()
    for item in value.values():
        if item is not None and (not isinstance(item, int) or isinstance(item, bool) or item < 0):
            _invalid()


def evaluate(cases, results, freeze):
    if not isinstance(cases, list) or not isinstance(results, list) or not isinstance(freeze, dict):
        _invalid()
    fkeys = {"schema_version", "rule_id", "developer", "evaluator", "frozen_at", "disclosed_at", "manifest_sha256", "calibration_sha256", "checker_sha256", "rule_sha256", "support_scope", "format_restrictions", "runtime_versions", "observed_sha256", "first_run_case_ids"}
    if set(freeze) - fkeys or not freeze:
        _invalid()
    complete_freeze = set(freeze) == fkeys
    pending = {"provenance_incomplete"} if not complete_freeze else set()
    evidence = "local"
    if "schema_version" in freeze and (freeze["schema_version"] != 1 or isinstance(freeze["schema_version"], bool)):
        _invalid()
    rule_id = freeze.get("rule_id", "g2-v1")
    if not isinstance(rule_id, str) or rule_id not in _RULE_IDS:
        _invalid()
    for name in ("developer", "evaluator"):
        if name in freeze and (not isinstance(freeze[name], str) or not freeze[name]):
            _invalid()
    for name in ("frozen_at", "disclosed_at"):
        if name in freeze:
            _time(freeze[name])
    for name in ("manifest_sha256", "rule_sha256"):
        if name in freeze and not _hash(freeze[name]):
            _invalid()
    if "calibration_sha256" in freeze:
        calibration = freeze["calibration_sha256"]
        if not isinstance(calibration, list) or not all(_hash(value) for value in calibration) or len(set(calibration)) != len(calibration):
            _invalid()
    if "checker_sha256" in freeze:
        checker = freeze["checker_sha256"]
        if not isinstance(checker, dict) or not checker or set(checker) & set(_RULE_IDS.values()) or not all(isinstance(name, str) and _hash(value) for name, value in checker.items()):
            _invalid()
    if "support_scope" in freeze:
        scope = freeze["support_scope"]
        if not isinstance(scope, dict) or set(scope) != {"unsupported_categories", "unsupported_count", "selection_reasons"}:
            _invalid()
        categories, count, reasons = scope["unsupported_categories"], scope["unsupported_count"], scope["selection_reasons"]
        if not isinstance(categories, list) or not all(isinstance(value, str) for value in categories) or len(categories) != len(set(categories)) or not set(categories) <= _CATEGORIES:
            _invalid()
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            _invalid()
        if not isinstance(reasons, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in reasons.items()):
            _invalid()
    if "format_restrictions" in freeze and not _same(freeze["format_restrictions"], _FORMAT):
        _invalid()
    if "runtime_versions" in freeze and (not isinstance(freeze["runtime_versions"], dict) or not all(isinstance(name, str) and isinstance(value, str) for name, value in freeze["runtime_versions"].items())):
        _invalid()
    if "observed_sha256" in freeze and (not isinstance(freeze["observed_sha256"], dict) or not all(isinstance(name, str) and _hash(value) for name, value in freeze["observed_sha256"].items())):
        _invalid()
    if "first_run_case_ids" in freeze:
        first_run = freeze["first_run_case_ids"]
        if not isinstance(first_run, list) or not all(isinstance(value, str) for value in first_run) or len(first_run) != len(set(first_run)):
            _invalid()
    if {"developer", "evaluator"} <= set(freeze) and freeze["developer"] == freeze["evaluator"]:
        pending.add("independent_identity_invalid")
    if {"frozen_at", "disclosed_at"} <= set(freeze) and _time(freeze["frozen_at"]) >= _time(freeze["disclosed_at"]):
        pending.add("chronology_invalid")
    if {"checker_sha256", "rule_sha256", "observed_sha256"} <= set(freeze) and freeze["observed_sha256"] != {**freeze["checker_sha256"], _RULE_IDS[rule_id]: freeze["rule_sha256"]}:
        _invalid()
    if complete_freeze:
        calibration = freeze["calibration_sha256"]
        scope = freeze["support_scope"]
        if len(calibration) != 10:
            pending.add("provenance_incomplete")
        categories, count, reasons = scope["unsupported_categories"], scope["unsupported_count"], scope["selection_reasons"]
        if set(reasons) != _CATEGORIES or not all(reasons.values()):
            pending.add("provenance_incomplete")
    else:
        calibration, scope = [], {"unsupported_count": 0, "unsupported_categories": []}

    case_keys = {"case_id", "original_id", "class", "input_sha256", "output_sha256", "reference_mask_sha256", "independent_support", "independent_label", "label_reason", "evidence_class"}
    case_ids, pairs, supported, originals, unsupported = set(), set(), {}, {}, []
    for case in cases:
        if not isinstance(case, dict):
            _invalid()
        extra = {"support_exclusion"} if case.get("class") == "unsupported" else set()
        if set(case) != case_keys | extra:
            _invalid()
        if not all(isinstance(case.get(key), str) and case[key] for key in ("case_id", "original_id", "label_reason")):
            _invalid()
        if case["case_id"] in case_ids or not isinstance(case["class"], str) or case["class"] not in _CLASSES or not _hash(case["input_sha256"]) or not _hash(case["output_sha256"]):
            _invalid()
        case_ids.add(case["case_id"])
        if case["evidence_class"] not in ("local", "mock", "real_external"):
            _invalid()
        if evidence == "local" and not supported and not unsupported:
            evidence = case["evidence_class"]
        elif case["evidence_class"] != evidence:
            pending.add("evidence_class_mismatch")
        if case["independent_support"] not in ("supported", "unsupported", "unknown") or case["independent_label"] not in ("valid", "invalid", "unknown"):
            _invalid()
        if case["independent_support"] == "unknown":
            pending.add("independent_support_unknown")
        if case["independent_label"] == "unknown":
            pending.add("independent_label_unknown")
        if case["class"] == "unsupported":
            if not isinstance(case["support_exclusion"], str) or case["support_exclusion"] not in _CATEGORIES:
                _invalid()
            if case["reference_mask_sha256"] is not None and not _hash(case["reference_mask_sha256"]):
                _invalid()
            unsupported.append(case)
        else:
            if case["independent_support"] == "unsupported" or case["reference_mask_sha256"] is None:
                pending.add("provenance_incomplete")
            elif not _hash(case["reference_mask_sha256"]):
                _invalid()
            known_input = originals.setdefault(case["original_id"], case["input_sha256"])
            if known_input != case["input_sha256"]:
                _invalid()
            pair = (case["original_id"], case["class"])
            if pair in pairs:
                pending.add("case_coverage_incomplete")
            pairs.add(pair)
            supported.setdefault(case["original_id"], set()).add(case["class"])

    rkeys = {"case_id", "input_sha256", "output_sha256", "rule_id", "status", "metrics"}
    result_map = {}
    for result in results:
        if not isinstance(result, dict) or set(result) != rkeys:
            _invalid()
        if not isinstance(result.get("case_id"), str) or result["case_id"] in result_map or not _hash(result.get("input_sha256")) or not _hash(result.get("output_sha256")) or result.get("rule_id") != rule_id or result.get("status") not in ("accepted", "rejected", "indeterminate"):
            _invalid()
        if not isinstance(result.get("metrics"), dict) or set(result["metrics"]) != set(_METRICS):
            _invalid()
        for name, keys in _METRICS.items():
            _metric(result["metrics"][name], keys)
        result_map[result["case_id"]] = result
    if set(result_map) - case_ids:
        pending.add("case_coverage_incomplete")
    if set(result_map) != case_ids:
        pending.add("result_coverage_incomplete")
    for case in cases:
        result = result_map.get(case["case_id"])
        if result is not None and (result["input_sha256"] != case["input_sha256"] or result["output_sha256"] != case["output_sha256"]):
            _invalid()

    if complete_freeze:
        first_run = freeze["first_run_case_ids"]
        if not isinstance(first_run, list) or not all(isinstance(value, str) for value in first_run) or len(first_run) != len(set(first_run)):
            _invalid()
        if set(first_run) != case_ids:
            pending.add("first_run_coverage_incomplete")
        if set(calibration) & {case["input_sha256"] for case in cases if case["class"] != "unsupported"}:
            pending.add("calibration_overlap")
        if len(supported) != 20 or any(classes != {"normal"} | _ATTACKS for classes in supported.values()):
            pending.add("case_coverage_incomplete")
        actual = {case["support_exclusion"] for case in unsupported}
        if actual != _CATEGORIES or set(scope["unsupported_categories"]) != _CATEGORIES:
            pending.add("unsupported_category_incomplete")
        if len(unsupported) != scope["unsupported_count"]:
            pending.add("case_coverage_incomplete")

    denominator = len(unsupported) if unsupported else (scope["unsupported_count"] if complete_freeze else 0)
    counts = {"normal_accepted":0, "attack_accepted":0, "unsupported_rejected":0}
    for case in cases:
        result = result_map.get(case["case_id"])
        if result is None:
            continue
        if case["class"] == "normal" and result["status"] == "accepted":
            counts["normal_accepted"] += 1
        elif case["class"] in _ATTACKS and result["status"] == "accepted":
            counts["attack_accepted"] += 1
        elif case["class"] == "unsupported" and result["status"] == "rejected":
            counts["unsupported_rejected"] += 1
    if pending:
        return _result("blocked", evidence, counts, denominator, [reason for reason in _REASONS if reason in pending])
    codes = []
    if counts["normal_accepted"] < 18:
        codes.append("normal_threshold_failed")
    if counts["attack_accepted"]:
        codes.append("attack_acceptance_detected")
    if any(result_map[case["case_id"]]["status"] == "indeterminate" for case in cases if case["class"] in _ATTACKS):
        codes.append("attack_indeterminate")
    if counts["unsupported_rejected"] != len(unsupported):
        codes.append("unsupported_nonrejection_detected")
    return _result("passed" if not codes else "failed", evidence, counts, denominator, codes)
