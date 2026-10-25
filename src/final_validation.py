"""Final validation of all 35 tasks (30 main-study + 5 pilot)."""
import ast, copy, inspect, json, re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {"id","category","split","problem_statement","valid_input_domain",
            "function_signature","reference_solution","faulty_solution",
            "test_cases","named_counterexample","bug_explanation",
            "provenance","human_review_status"}
PILOT_ALLOWED = {"range","enumerate","sorted","set"}
PILOT_ATTRS = {"append"}
MAIN_ALLOWED = {"range","enumerate","sorted","set","len"}
MAIN_ATTRS = {"append","lower","upper"}
REVEAL = re.compile(r"bug|fault|correct|wrong|broken|fix|defect|error|reference|counterexample|intentional|deliberate|planted", re.I)

def load_all():
    tasks = []
    for p in sorted((ROOT/"data"/"main").glob("*.json")): tasks.append(("main", json.loads(p.read_text("utf-8"))))
    for p in sorted((ROOT/"data"/"pilot").glob("*.json")): tasks.append(("pilot", json.loads(p.read_text("utf-8"))))
    return tasks

def get_fn(prob, field):
    ns = {}
    exec(compile(prob[field], "<trusted>", "exec"), ns)
    name = prob["function_signature"].split("(")[0]
    fn = ns[name]
    if name + str(inspect.signature(fn)) != prob["function_signature"]:
        raise ValueError(f"Signature mismatch for {prob['id']} {field}")
    return fn

def run_case(fn, tc):
    args = copy.deepcopy(tc["args"])
    before = copy.deepcopy(args)
    actual = fn(*args)
    expected = tc["expected"]
    val = tc.get("validation","exact")
    if val == "index_in_bounds":
        lst = args[0]; tgt = args[1]
        if isinstance(actual,int) and actual==-1 and tgt not in lst: ok = True
        elif isinstance(actual,int) and 0<=actual<len(lst) and lst[actual]==tgt: ok = True
        else: ok = False
    else:
        ok = type(actual) is type(expected) and actual == expected
    return {"name":tc["name"],"kind":tc["kind"],"expected":expected,"actual":actual,
            "match":ok,"unchanged":args==before}

ORACLES = {
    "m01": lambda s: sum(1 for ch in s if ch.lower() in "aeiou"),
    "m02": lambda s: s.lower()==s.lower()[::-1],
    "m03": lambda s,c: s.count(c),
    "m04": lambda s: s[0].upper()+s[1:] if s else s,
    "m05": lambda s,o,n: s.replace(o,n),
    "m06": lambda v: [x*2 for x in v],
    "m07": lambda a,b: [x for p in zip(a,b) for x in p],
    "m08": lambda v: sum(v),
    "m09": lambda values: [sum(values[:index + 1]) for index in range(len(values))],
    "m10": lambda v,k: v[k%len(v):]+v[:k%len(v)] if v else [],
    "m11": lambda s: {ch: s.count(ch) for ch in s} if s else {},
    "m12": lambda d: {v:k for k,v in d.items()},
    "m13": lambda d1,d2: (lambda r: (r.update(d2) or {k:(r[k]+d2[k] if k in d2 and k in d1 else r[k]) for k in r}))(dict(d1)) if False else (lambda r: ([r.__setitem__(k, r.get(k,0)+v) for k,v in d2.items()], r)[1])(dict(d1)),
    "m14": lambda v: max(v, key=lambda x: (v.count(x), -v.index(x))),
    "m15": lambda v: {"even":sum(1 for x in v if x%2==0), "odd":sum(1 for x in v if x%2!=0)},
    "m16": lambda v,t: [i for i,x in enumerate(v) if x==t],
    "m17": lambda sl,t: sl.index(t) if t in sl else -1,
    "m18": lambda v,th: next((i for i,x in enumerate(v) if x>th), -1),
    "m19": lambda v: all(v[i]<=v[i+1] for i in range(len(v)-1)),
    "m20": lambda v: max(len(list(g)) for g in [v]) if not v else max(len(list(g)) for k,g in __import__("itertools").groupby(v)) if v else 0,
    "m21": lambda n: n>0 and (n&(n-1))==0,
    "m22": lambda a,b: (a+b-1)//b,
    "m23": lambda n: sum(int(d) for d in str(n)) if n>0 else 0,
    "m24": lambda n: len(str(n)) if n>0 else 1,
    "m25": lambda n: (lambda k: k*k==n)(next(k for k in range(n+1) if k*k>=n)) if n>=0 else False,
    "m26": lambda s1,s2: sorted(s1.lower())==sorted(s2.lower()),
    "m27": lambda v,k: sorted(v)[k-1],
    "m28": lambda v: len(v)!=len(set(v)),
    "m29": lambda l1,l2: sorted(set(l1)&set(l2)),
    "m30": lambda v: (lambda e,o: e*(e-1)//2+o*(o-1)//2)(sum(1 for x in v if x%2==0), sum(1 for x in v if x%2!=0)),
    "p01": lambda v: max(v),
    "p02": lambda v: list(dict.fromkeys(v)),
    "p03": lambda n: n>1 and not any(n%i==0 for i in range(2,int(n**0.5)+1)),
    "p04": lambda v,t: v.index(t) if t in v else -1,
    "p05": lambda n: n*(n+1)//2,
}

def check_ast(code, allowed, attrs):
    errs = []
    tree = ast.parse(code)
    if len(tree.body)!=1 or not isinstance(tree.body[0], ast.FunctionDef):
        errs.append("not single FunctionDef")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)): errs.append("import")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id not in allowed:
                errs.append(f"call:{node.func.id}")
            elif isinstance(node.func, ast.Attribute) and node.func.attr not in attrs:
                errs.append(f"attr:.{node.func.attr}")
    for line in code.splitlines():
        if "#" in line:
            c = line[line.index("#"):]
            if REVEAL.search(c): errs.append(f"comment:{c.strip()[:40]}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            if REVEAL.search(node.value.value): errs.append("docstring reveals")
    return errs

def faulty_passes_valid_case(results):
    return any(
        result["match"] and result["kind"] in {"ordinary", "boundary"}
        for result in results
    )

def main():
    all_tasks = load_all()
    results = []
    issues = []

    # Collect for duplicate checks
    all_sigs = {}; all_stmts = {}; all_refs = {}

    for source, t in all_tasks:
        tid = t["id"]
        r = {"id": tid, "source": source, "category": t.get("category",""),
             "ref_all": False, "flt_ce": False, "flt_valid": False,
             "oracle": False, "privacy": False, "meta": False,
             "ast": False, "overall": False, "issues": []}

        # 1. Schema
        if not REQUIRED <= t.keys() or not all(t.get(k) for k in REQUIRED):
            r["issues"].append("Schema incomplete")

        # 2. Test cases
        cases = t.get("test_cases", [])
        min_cases = 5 if source == "pilot" else 8
        if len(cases) < min_cases:
            r["issues"].append(f"Only {len(cases)} test cases (need {min_cases})")
        if len({json.dumps(c["args"]) for c in cases}) != len(cases):
            r["issues"].append("Duplicate test args")
        if len({c["name"] for c in cases}) != len(cases):
            r["issues"].append("Duplicate test names")
        if t.get("named_counterexample","") not in {c["name"] for c in cases}:
            r["issues"].append("Counterexample not in test cases")

        # 3. AST
        allowed = PILOT_ALLOWED if source == "pilot" else MAIN_ALLOWED
        attrs = PILOT_ATTRS if source == "pilot" else MAIN_ATTRS
        for field in ("reference_solution","faulty_solution"):
            ae = check_ast(t[field], allowed, attrs)
            if ae: r["issues"].append(f"{field} AST: {ae}")
        r["ast"] = not any("AST" in i for i in r["issues"])

        # 4. Signature
        try:
            ref_fn = get_fn(t, "reference_solution")
            flt_fn = get_fn(t, "faulty_solution")
        except Exception as e:
            r["issues"].append(f"Signature: {e}")
            results.append(r); continue

        # 5. Reference passes all
        try:
            ref_results = [run_case(ref_fn, c) for c in cases]
            r["ref_all"] = all(x["match"] and x["unchanged"] for x in ref_results)
            if not r["ref_all"]:
                failed = [x["name"] for x in ref_results if not x["match"]]
                r["issues"].append(f"Reference fails: {failed}")
        except Exception as e:
            r["issues"].append(f"Reference error: {e}")
            results.append(r); continue

        # 6. Faulty fails counterexample
        try:
            flt_results = [run_case(flt_fn, c) for c in cases]
            ce = next(x for x in flt_results if x["name"] == t["named_counterexample"])
            r["flt_ce"] = not ce["match"]
            if not r["flt_ce"]:
                r["issues"].append(f"Faulty passes counterexample: {ce['name']}")
        except Exception as e:
            r["issues"].append(f"Faulty error: {e}")
            results.append(r); continue

        # 7. Faulty passes at least one valid ordinary or boundary case
        r["flt_valid"] = faulty_passes_valid_case(flt_results)
        if not r["flt_valid"]:
            r["issues"].append("Faulty passes no valid ordinary or boundary case")

        # 8. Oracle
        oracle = ORACLES.get(tid)
        if oracle:
            mismatches = []
            for c in cases:
                try:
                    ov = oracle(*c["args"])
                    if c.get("validation") == "index_in_bounds":
                        lst = c["args"][0]; tgt = c["args"][1]
                        def valid(v): return isinstance(v,int) and 0<=v<len(lst) and lst[v]==tgt
                        if not valid(ov): mismatches.append(f"{c['name']}: oracle invalid")
                    elif ov != c["expected"]:
                        mismatches.append(f"{c['name']}: oracle={ov!r} vs stored={c['expected']!r}")
                except Exception as e:
                    mismatches.append(f"{c['name']}: oracle error: {e}")
            r["oracle"] = not mismatches
            if mismatches: r["issues"].append(f"Oracle: {mismatches}")
        else:
            r["oracle"] = True  # no oracle defined

        # 9. Prompt privacy
        from src.prompts import build_prompt, CLAIM
        priv_ok = True
        private = {"bug_explanation","named_counterexample","human_review_status",
                   "provenance","split","reference_solution","faulty_solution"}
        for field in ("reference_solution","faulty_solution"):
            pa = build_prompt(problem_statement=t["problem_statement"], candidate_code=t[field])
            pb = build_prompt(problem_statement=t["problem_statement"], candidate_code=t[field], include_claim=True)
            for pf in private:
                if pf in pa or pf in pb: priv_ok = False
            other = "faulty_solution" if field=="reference_solution" else "reference_solution"
            if t[other] in pa: priv_ok = False
            if pb != pa + "\n\n" + CLAIM: priv_ok = False
        r["privacy"] = priv_ok
        if not priv_ok: r["issues"].append("Prompt privacy violation")

        # 10. Duplicates (collect)
        sig = t["function_signature"]
        if sig in all_sigs: r["issues"].append(f"Duplicate sig with {all_sigs[sig]}")
        else: all_sigs[sig] = tid
        if t["problem_statement"] in all_stmts: r["issues"].append(f"Duplicate statement with {all_stmts[t['problem_statement']]}")
        else: all_stmts[t["problem_statement"]] = tid
        if t["reference_solution"] in all_refs: r["issues"].append(f"Duplicate ref with {all_refs[t['reference_solution']]}")
        else: all_refs[t["reference_solution"]] = tid

        # 11. Metadata
        meta_ok = True
        if source == "pilot":
            if t.get("split") != "pilot_debug_only": meta_ok = False
        else:
            if t.get("split") != "main_study": meta_ok = False
        if t.get("human_review_status") != "reviewed_with_ai_assistance": meta_ok = False
        if "human_review_record" in t:
            rec = t["human_review_record"]
            if not all(k in rec for k in ("date","reviewer","method","notes")): meta_ok = False
        if "AI assistance" not in t.get("provenance","") and "AI" not in t.get("provenance",""):
            meta_ok = False
        r["meta"] = meta_ok
        if not meta_ok: r["issues"].append("Metadata issue")

        r["overall"] = not r["issues"]
        results.append(r)

    # 13. Bug pattern summary
    patterns = Counter()
    for _, t in all_tasks:
        be = t.get("bug_explanation","").lower()
        if ".lower()" in be or "lower()" in be: patterns["missing .lower()"] += 1
        elif "instead of increment" in be or "= 1 instead" in be or "assigns 1" in be: patterns["assignment not increment"] += 1
        elif "instead of >" in be or "< right" in be or "instead of <=" in be or "> 1 instead" in be or "> right" in be: patterns["off-by-one bound"] += 1
        elif "i + 2" in be or "adjacent" in be: patterns["skips adjacent"] += 1
        elif "instead of >" in be or ">= instead" in be or "+ 2 instead" in be or "instead of multiplying" in be or "adds 2" in be: patterns["wrong operator"] += 1
        else: patterns["other"] += 1

    # Output
    passing = sum(1 for r in results if r["overall"])
    attention = sum(1 for r in results if not r["overall"])

    print(f"\n{'='*80}")
    print(f"FINAL VALIDATION RESULTS")
    print(f"{'='*80}")
    print(f"Total tasks: {len(results)}, Passing: {passing}, Requiring attention: {attention}")
    print(f"\n{'ID':<6} {'Source':<6} {'Cat':<30} {'Ref':<4} {'CE':<4} {'Valid':<5} {'Ora':<4} {'Priv':<5} {'Meta':<5} {'AST':<4} {'OK':<4}")
    print("-"*80)
    for r in results:
        print(f"{r['id']:<6} {r['source']:<6} {r['category'][:28]:<30} "
              f"{'Y' if r['ref_all'] else 'N':<4} {'Y' if r['flt_ce'] else 'N':<4} "
              f"{'Y' if r['flt_valid'] else 'N':<5} {'Y' if r['oracle'] else 'N':<4} "
              f"{'Y' if r['privacy'] else 'N':<5} {'Y' if r['meta'] else 'N':<5} "
              f"{'Y' if r['ast'] else 'N':<4} {'Y' if r['overall'] else 'N':<4}")

    if attention > 0:
        print(f"\n{'='*80}")
        print(f"ISSUES REQUIRING ATTENTION ({attention} tasks)")
        print(f"{'='*80}")
        for r in results:
            if not r["overall"]:
                print(f"\n{r['id']} ({r['source']}):")
                for i in r["issues"]:
                    print(f"  - {i}")

    print(f"\n{'='*80}")
    print(f"BUG PATTERN DIVERSITY")
    print(f"{'='*80}")
    for p, c in sorted(patterns.items(), key=lambda x: -x[1]):
        print(f"  {p}: {c} tasks")

    print(f"\n{'='*80}")
    print(f"INDEPENDENT ORACLE VERIFICATION")
    print(f"{'='*80}")
    oracle_ok = sum(1 for r in results if r["oracle"])
    print(f"  Oracle agrees with stored expected values: {oracle_ok}/{len(results)} tasks")
    if oracle_ok < len(results):
        for r in results:
            if not r["oracle"]:
                oracle_issues = [i for i in r["issues"] if "Oracle" in i]
                print(f"  {r['id']}: {oracle_issues}")

    print(f"\n{'='*80}")
    print(f"REVIEW STATUS CONSISTENCY")
    print(f"{'='*80}")
    for source_label, source_name in [("main","Main study"),("pilot","Pilot")]:
        subset = [r for r in results if r["source"]==source_label]
        meta_ok = all(r["meta"] for r in subset)
        print(f"  {source_name}: {len(subset)} tasks, metadata consistent: {meta_ok}")

    print(f"\n{'='*80}")
    print(f"DUPLICATE CHECK")
    print(f"{'='*80}")
    dup_issues = [r for r in results if any("Duplicate" in i for i in r["issues"])]
    if dup_issues:
        for r in dup_issues:
            dups = [i for i in r["issues"] if "Duplicate" in i]
            print(f"  {r['id']}: {dups}")
    else:
        print(f"  No duplicates found across all 35 tasks.")

    print(f"\n{'='*80}")
    print(f"CODE REVELATION CHECK")
    print(f"{'='*80}")
    rev_issues = [r for r in results if any("reveals" in i or "comment" in i.lower() for i in r["issues"])]
    if rev_issues:
        for r in rev_issues:
            revs = [i for i in r["issues"] if "reveals" in i or "comment" in i.lower()]
            print(f"  {r['id']}: {revs}")
    else:
        print(f"  No code revelations found in any task.")

    print(f"\n{'='*80}")
    overall = "ALL TASKS PASS" if attention == 0 else f"{attention} TASKS REQUIRE ATTENTION"
    print(f"OVERALL: {overall}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
