"""Restricted G2 image checker."""
import hashlib
from .png import decode_png

_RULE = {"schema_version":1,"rule_id":"g2-v1","format":{"max_encoded_bytes":8388608,"min_dimension":64,"max_dimension":1024,"max_pixels":1048576,"bit_depth":8,"color_types":[2,6],"compression_method":0,"filter_method":0,"interlace_method":0,"scanline_filters":[0,1,2,3,4]},"support":{"opaque_alpha":255,"perimeter_distance_max":8,"foreground_distance_min":32,"erosion_radius":1,"uncertain_percent_numerator":5,"uncertain_percent_denominator":100},"acceptance":{"background_alpha_max":5,"background_pass_numerator":99,"background_pass_denominator":100,"foreground_alpha_min":250,"foreground_pass_numerator":99,"foreground_pass_denominator":100,"foreground_rgb_error_sum_per_pixel_max":9}}
_RULE_V2 = {"schema_version":2,"rule_id":"g2-v2","format":{"max_encoded_bytes":8388608,"min_dimension":64,"max_dimension":1024,"max_pixels":1048576,"bit_depth":8,"color_types":[2,6],"compression_method":0,"filter_method":0,"interlace_method":0,"scanline_filters":[0,1,2,3,4]},"support":{"opaque_alpha":255,"perimeter_distance_max":8,"foreground_distance_min":32,"erosion_radius":1,"uncertain_percent_numerator":5,"uncertain_percent_denominator":100,"require_separable_foreground":True},"acceptance":{"background_alpha_max":5,"background_pass_numerator":99,"background_pass_denominator":100,"foreground_alpha_min":250,"foreground_pass_numerator":99,"foreground_pass_denominator":100,"foreground_rgb_error_sum_per_pixel_max":9,"boundary_alpha_min":250,"boundary_rgb_error_sum_per_pixel_max":9}}

def _validate(rule):
    def same(actual, expected):
        if type(actual) is not type(expected): return False
        if isinstance(expected, dict):
            return actual.keys() == expected.keys() and all(same(actual[k], expected[k]) for k in expected)
        if isinstance(expected, list): return len(actual) == len(expected) and all(same(a, b) for a, b in zip(actual, expected))
        return actual == expected
    if not same(rule, _RULE) and not same(rule, _RULE_V2): raise ValueError("invalid_rule")

def _empty(data, reason, rule_id="g2-v1"):
    return {"status":"unsupported", "input_sha256":hashlib.sha256(data).hexdigest() if isinstance(data, bytes) else None, "width":None, "height":None, "rule_id":rule_id, "region_counts":dict.fromkeys(["total","background","foreground_candidate","foreground","uncertain","foreground_components"]), "reason_codes":[reason]}

def _unavailable_metrics():
    return {"background_alpha":{"numerator":None,"denominator":None}, "foreground_alpha":{"numerator":None,"denominator":None}, "foreground_rgb_error":{"numerator":None,"denominator":None,"pixel_denominator":None}}

def _regions(data, rule):
    _validate(rule)
    try: w,h,p = decode_png(data)
    except ValueError as error: return None, _empty(data, str(error), rule["rule_id"])
    n=w*h; perimeter=[]
    for x in range(w): perimeter += [x, (h-1)*w+x]
    for y in range(1,h-1): perimeter += [y*w, y*w+w-1]
    reference=[sorted(p[4*i+c] for i in perimeter)[(len(perimeter)-1)//2] for c in range(3)]
    dist=lambda i:max(abs(p[4*i+c]-reference[c]) for c in range(3))
    b=set(i for i in range(n) if dist(i)<=8)
    connected=set(); stack=[i for i in perimeter if i in b]
    while stack:
        i=stack.pop()
        if i in connected: continue
        connected.add(i); x,y=i%w,i//w
        stack += [j for j in (i-1 if x else -1,i+1 if x<w-1 else -1,i-w if y else -1,i+w if y<h-1 else -1) if j in b and j not in connected]
    f0={i for i in range(n) if i not in connected and dist(i)>=32}
    f={i for i in f0 if i%w and i%w<w-1 and i//w and i//w<h-1 and all(j in f0 for j in (i-1,i+1,i-w,i+w,i-w-1,i-w+1,i+w-1,i+w+1))}
    u=set(range(n))-connected-f
    seen=set(); components=0
    for start in f0:
        if start in seen: continue
        components+=1; stack=[start]
        while stack:
            i=stack.pop()
            if i in seen: continue
            seen.add(i); x,y=i%w,i//w
            stack += [j for j in (i-1 if x else -1,i+1 if x<w-1 else -1,i-w if y else -1,i+w if y<h-1 else -1) if j in f0 and j not in seen]
    reasons=[]
    if any(p[4*i+3] != 255 for i in range(n)): reasons.append("input_alpha_not_opaque")
    if any(dist(i)>8 for i in perimeter): reasons.append("perimeter_not_uniform")
    if not connected: reasons.append("background_empty")
    if not f: reasons.append("foreground_empty")
    if components != 1: reasons.append("foreground_components_not_one")
    if 100*len(u) > 5*n: reasons.append("uncertain_region_exceeds_limit")
    boundary=f0-f
    if rule["support"].get("require_separable_foreground") and set(range(n))-connected-f0:
        reasons.append("input_boundary_ambiguous")
    result={"status":"supported" if not reasons else "unsupported", "input_sha256":hashlib.sha256(data).hexdigest(), "width":w,"height":h,"rule_id":rule["rule_id"],"region_counts":{"total":n,"background":len(connected),"foreground_candidate":len(f0),"foreground":len(f),"uncertain":len(u),"foreground_components":components},"reason_codes":reasons}
    return (w,h,p,connected,f,boundary), result

def check_input(input_png, rule):
    _, result = _regions(input_png, rule); return result

def check_output(input_png, output_png, rule):
    regions, input_result = _regions(input_png, rule)
    input_hash=hashlib.sha256(input_png).hexdigest() if isinstance(input_png,bytes) else None
    output_hash=hashlib.sha256(output_png).hexdigest() if isinstance(output_png,bytes) else None
    if regions is None or input_result["status"] != "supported":
        return {"status":"rejected","input_sha256":input_hash,"output_sha256":output_hash,"dimensions":{"input":None,"output":None},"rule_id":input_result["rule_id"],"metrics":_unavailable_metrics(),"reason_codes":["input_unsupported"]+input_result["reason_codes"]}
    w,h,p,b,f,boundary=regions
    try: ow,oh,out=decode_png(output_png)
    except ValueError as error:
        code={"invalid_type":"output_invalid_type", "invalid_png":"output_invalid_png", "unsupported_format":"output_unsupported_format", "resource_limit":"output_resource_limit"}[str(error)]
        return {"status":"rejected","input_sha256":input_hash,"output_sha256":output_hash,"dimensions":{"input":{"width":w,"height":h},"output":None},"rule_id":input_result["rule_id"],"metrics":_unavailable_metrics(),"reason_codes":[code]}
    dimensions={"input":{"width":w,"height":h},"output":{"width":ow,"height":oh}}
    if (w,h)!=(ow,oh): return {"status":"rejected","input_sha256":input_hash,"output_sha256":output_hash,"dimensions":dimensions,"rule_id":input_result["rule_id"],"metrics":_unavailable_metrics(),"reason_codes":["dimension_mismatch"]}
    ba=sum(out[4*i+3] <= 5 for i in b); fa=sum(out[4*i+3] >= 250 for i in f); rgb=sum(abs(out[4*i+c]-p[4*i+c]) for i in f for c in range(3))
    metrics={"background_alpha":{"numerator":ba,"denominator":len(b)},"foreground_alpha":{"numerator":fa,"denominator":len(f)},"foreground_rgb_error":{"numerator":rgb,"denominator":3*len(f),"pixel_denominator":len(f)}}
    reasons=[]
    if 100*ba < 99*len(b): reasons.append("background_alpha_threshold_failed")
    if 100*fa < 99*len(f): reasons.append("foreground_alpha_threshold_failed")
    if rgb > 9*len(f): reasons.append("foreground_rgb_threshold_failed")
    if rule["rule_id"] == "g2-v2":
        if any(out[4*i+3] < rule["acceptance"]["boundary_alpha_min"] for i in boundary): reasons.append("boundary_alpha_threshold_failed")
        if any(sum(abs(out[4*i+c]-p[4*i+c]) for c in range(3)) > rule["acceptance"]["boundary_rgb_error_sum_per_pixel_max"] for i in boundary): reasons.append("boundary_rgb_threshold_failed")
    return {"status":"accepted" if not reasons else "rejected","input_sha256":input_hash,"output_sha256":output_hash,"dimensions":dimensions,"rule_id":input_result["rule_id"],"metrics":metrics,"reason_codes":reasons}
