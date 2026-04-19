#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path


HIGH_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"\bdatasource\b",
        r"\bpassword\b",
        r"\bsecret\b",
        r"\btoken\b",
        r"\bprivate[-._]?key\b",
        r"\bssl\b",
        r"\btruststore\b",
        r"\bkeystore\b",
        r"\bsecurity\b",
        r"\boauth\b",
        r"\bjwt\b",
        r"\bactuator\b",
        r"\bmanagement\.",
        r"\bhibernate\.ddl-auto\b",
        r"\bh2\.console\b",
    ]
]
MEDIUM_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"\blogging\.",
        r"\bcache\b",
        r"\bredis\b",
        r"\bkafka\b",
        r"\brabbit\b",
        r"\bsqs\b",
        r"\bqueue\b",
        r"\bcors\b",
        r"allowed-origins",
        r"\bendpoint\b",
        r"\burl\b",
        r"\bhost\b",
    ]
]
FRAMEWORK_PREFIXES = (
    "spring.",
    "server.",
    "management.",
    "logging.",
    "jackson.",
    "servlet.",
    "tomcat.",
)
PROD_PROFILE_NAMES = ("prod", "production", "prd", "live")
SOURCE_PROFILE_NAMES = ("qa", "uat", "stage", "staging", "preprod", "pre-prod", "ppe", "perf")
LOW_SIGNAL_PROFILES = {"dev", "local", "test", "tests", "default", "ci", "demo", "sample", "sandbox"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Spring env config via spring-config-dump")
    parser.add_argument("repo", nargs="?", default=".", help="target repo")
    parser.add_argument("--from", dest="from_profile", help="source profile to compare from; use `base` for no profile")
    parser.add_argument("--to", dest="to_profile", help="target profile to compare to; auto-detects prod-like profile by default")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    default_resolver_dir = Path(__file__).resolve().parent.parent / "tools" / "spring-config-dump"
    parser.add_argument(
        "--resolver-dir",
        default=str(default_resolver_dir),
        help="directory containing spring-config-dump run.sh / target jar",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()
    resolver_dir = Path(args.resolver_dir).resolve()
    config_files = sorted(find_config_files(repo))
    detected_profiles = detect_profiles(repo, config_files)
    selection = select_compare_profiles(detected_profiles, args.from_profile, args.to_profile)

    base_raw = run_resolver(resolver_dir, repo, None)
    to_raw = run_resolver(resolver_dir, repo, selection["to_profile"])
    base = snapshot_to_internal(base_raw, None)
    if selection["from_profile"] is None:
        from_cfg = base
    else:
        from_raw = run_resolver(resolver_dir, repo, selection["from_profile"])
        from_cfg = snapshot_to_internal(from_raw, selection["from_profile"])
    to_cfg = snapshot_to_internal(to_raw, selection["to_profile"])
    code_usage = analyze_code_usage(repo, to_cfg)
    analysis = compare_configs(base, from_cfg, to_cfg)

    payload = {
        "repo": str(repo),
        "spring_boot_version": to_raw.get("bootVersion") or base_raw.get("bootVersion"),
        "compared": {"from": selection["from_label"], "to": selection["to_profile"]},
        "profile_selection": selection,
        "config_files": config_files,
        "base": base,
        "from": from_cfg,
        "to": to_cfg,
        "analysis": analysis,
        "code_usage": code_usage,
    }

    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(render_markdown(payload))
    return 0


def run_resolver(resolver_dir: Path, repo: Path, profile: str | None) -> dict:
    jar = next((resolver_dir / "target").glob("spring-config-dump-*.jar"), None)
    if jar and jar.is_file() and not jar.name.startswith("original-"):
        command = ["java", "-jar", str(jar)]
    else:
        runner = resolver_dir / "run.sh"
        if not runner.is_file():
            raise SystemExit(f"Missing resolver at {runner}")
        command = [str(runner)]

    command.extend(["--repo", str(repo)])
    if profile:
        command.extend(["--profile", profile])

    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or result.stdout.strip() or f"resolver failed: {' '.join(command)}")
    return json.loads(result.stdout)


def detect_profiles(repo: Path, config_files: list[str]) -> list[str]:
    detected = set()
    for rel_path in config_files:
        path = repo / rel_path
        for token in profiles_from_filename(path.name):
            detected.add(token)
        text = path.read_text(encoding="utf-8", errors="ignore")
        for token in profiles_from_text(text):
            detected.add(token)
    return sorted(detected)


def profiles_from_filename(name: str) -> list[str]:
    match = re.match(r"^(?:application|bootstrap)-([^.]+)\.(?:properties|ya?ml)$", name)
    if not match:
        return []
    return [normalize_profile_token(token) for token in match.group(1).split(",") if normalize_profile_token(token)]


def profiles_from_text(text: str) -> list[str]:
    detected = set()
    for line in text.splitlines():
        stripped = line.split("#", 1)[0].strip()
        if not stripped:
            continue
        for pattern in (
            r"spring\.config\.activate\.on-profile\s*[:=]\s*(.+)$",
            r"spring\.profiles(?:\.(?:active|include|default|group\.[^.:\s=]+))?\s*[:=]\s*(.+)$",
        ):
            match = re.search(pattern, stripped)
            if not match:
                continue
            for token in tokenize_profile_values(match.group(1)):
                detected.add(token)
    return sorted(detected)


def tokenize_profile_values(raw: str) -> list[str]:
    cleaned = raw.strip().strip("[]")
    tokens = []
    for part in re.split(r"[\s,]+", cleaned):
        token = normalize_profile_token(part)
        if token:
            tokens.append(token)
    return tokens


def normalize_profile_token(token: str) -> str | None:
    cleaned = token.strip().strip("'\"")
    if not cleaned or cleaned.startswith("${") or cleaned in {"!", "&", "|"}:
        return None
    if not re.fullmatch(r"[A-Za-z0-9._-]+", cleaned):
        return None
    return cleaned.lower()


def select_compare_profiles(detected_profiles: list[str], from_arg: str | None, to_arg: str | None) -> dict:
    to_profile = normalize_cli_profile(to_arg)
    to_mode = "explicit" if to_profile else "auto"
    if not to_profile:
        to_profile = choose_profile(detected_profiles, PROD_PROFILE_NAMES)
        if not to_profile:
            detail = ", ".join(detected_profiles) if detected_profiles else "none"
            raise SystemExit(f"Could not auto-detect a prod profile. Detected profiles: {detail}. Pass --to explicitly.")

    from_profile = normalize_cli_profile(from_arg)
    from_mode = "explicit" if from_arg is not None else "auto"
    if from_profile == "base":
        from_profile = None
    if from_arg is None:
        from_profile = choose_profile([p for p in detected_profiles if p != to_profile], SOURCE_PROFILE_NAMES)
        if from_profile is None:
            from_profile = None
    return {
        "detected_profiles": detected_profiles,
        "from_profile": from_profile,
        "from_label": from_profile or "base",
        "to_profile": to_profile,
        "from_mode": from_mode,
        "to_mode": to_mode,
    }


def normalize_cli_profile(profile: str | None) -> str | None:
    if profile is None:
        return None
    value = profile.strip().lower()
    return value or None


def choose_profile(candidates: list[str], preferred: tuple[str, ...]) -> str | None:
    candidate_set = {candidate for candidate in candidates if candidate}
    for name in preferred:
        if name in candidate_set:
            return name
    return None


def snapshot_to_internal(snapshot: dict, profile: str | None) -> dict:
    effective = snapshot["effectiveProperties"]
    return {
        "target_profile": profile,
        "applied_docs": snapshot["appliedPropertySources"],
        "properties": {key: item["value"] for key, item in effective.items()},
        "sources": {key: item["origin"] or item["propertySource"] for key, item in effective.items()},
        "layers": {
            key: [{"value": layer["value"], "source": layer["origin"] or layer["propertySource"]} for layer in layers]
            for key, layers in snapshot["layers"].items()
        },
    }


def compare_configs(base: dict, from_cfg: dict, to_cfg: dict) -> dict:
    base_props = base["properties"]
    from_props = from_cfg["properties"]
    to_props = to_cfg["properties"]

    qa_only = [
        {
            "key": key,
            "from_value": redact(key, from_props[key]),
            "source": from_cfg["sources"][key],
            "severity": severity_for(key),
        }
        for key in sorted(from_props)
        if key not in to_props
    ]
    prod_only = [
        {
            "key": key,
            "to_value": redact(key, to_props[key]),
            "source": to_cfg["sources"][key],
            "severity": severity_for(key),
        }
        for key in sorted(to_props)
        if key not in from_props
    ]
    different_values = [
        {
            "key": key,
            "from_value": redact(key, from_props[key]),
            "to_value": redact(key, to_props[key]),
            "from_source": from_cfg["sources"][key],
            "to_source": to_cfg["sources"][key],
            "severity": severity_for(key),
        }
        for key in sorted(from_props)
        if key in to_props and from_props[key] != to_props[key]
    ]
    override_gaps = [
        {
            "key": key,
            "base_value": redact(key, base_props[key]),
            "from_value": redact(key, from_props[key]),
            "to_value": redact(key, to_props[key]),
            "base_source": base["sources"][key],
            "from_source": from_cfg["sources"][key],
            "to_source": to_cfg["sources"][key],
            "severity": severity_for(key),
        }
        for key in sorted(base_props)
        if key in from_props
        and key in to_props
        and from_props[key] != base_props[key]
        and to_props[key] == base_props[key]
    ]
    override_chains = []
    for key in sorted(set(base["layers"]) | set(from_cfg["layers"]) | set(to_cfg["layers"])):
        base_chain = base["layers"].get(key, [])
        from_chain = from_cfg["layers"].get(key, [])
        to_chain = to_cfg["layers"].get(key, [])
        values = {item["value"] for item in [*base_chain, *from_chain, *to_chain]}
        if max(len(base_chain), len(from_chain), len(to_chain)) <= 1 and len(values) <= 1:
            continue
        override_chains.append(
            {
                "key": key,
                "severity": severity_for(key),
                "base": base_chain,
                "from": from_chain,
                "to": to_chain,
            }
        )

    completeness = [
        {**item, "gap_type": "qa_only", "summary": "set in qa but missing in prod"}
        for item in qa_only
    ] + [
        {**item, "gap_type": "base_fallback", "summary": "qa overrides base but prod falls back to base"}
        for item in override_gaps
    ]
    completeness.sort(key=lambda item: (severity_rank(item["severity"]), item["key"]))

    return {
        "qa_only": qa_only,
        "prod_only": prod_only,
        "different_values": different_values,
        "override_gaps": override_gaps,
        "override_chains": override_chains,
        "prod_override_completeness_gaps": completeness,
        "smells": prod_smells(to_cfg),
    }


def prod_smells(config: dict) -> list[dict]:
    props = config["properties"]
    findings: list[dict] = []

    def add(severity: str, summary: str, key: str, value: str | None = None) -> None:
        findings.append(
            {
                "severity": severity,
                "summary": summary,
                "key": key,
                "value": redact(key, value),
                "source": config["sources"].get(key),
            }
        )

    if truthy(props.get("spring.h2.console.enabled")):
        add("high", "H2 console enabled in prod", "spring.h2.console.enabled", props.get("spring.h2.console.enabled"))

    ddl_auto = str(props.get("spring.jpa.hibernate.ddl-auto", ""))
    if ddl_auto in {"create", "create-drop"}:
        add("high", "dangerous ddl-auto in prod", "spring.jpa.hibernate.ddl-auto", ddl_auto)
    elif ddl_auto == "update":
        add("medium", "ddl-auto=update in prod", "spring.jpa.hibernate.ddl-auto", ddl_auto)

    exposure = str(props.get("management.endpoints.web.exposure.include", ""))
    if "*" in [item.strip() for item in exposure.split(",")]:
        add("high", "all actuator endpoints exposed", "management.endpoints.web.exposure.include", exposure)

    for endpoint in ("env", "configprops", "beans", "mappings", "heapdump", "threaddump", "loggers", "shutdown"):
        key = f"management.endpoint.{endpoint}.enabled"
        if truthy(props.get(key)):
            add("medium", "sensitive actuator endpoint enabled", key, props.get(key))

    if props.get("management.endpoint.health.show-details") == "always":
        add("medium", "health details always exposed", "management.endpoint.health.show-details", "always")

    if str(props.get("logging.level.root", "")).upper() in {"DEBUG", "TRACE"}:
        add("medium", "verbose root logging in prod", "logging.level.root", props.get("logging.level.root"))

    for key in ("server.error.include-stacktrace", "server.error.include-message"):
        if props.get(key) == "always":
            add("medium", "dev-style error detail enabled in prod", key, "always")

    cors_keys = [key for key in props if re.search(r"allowed-origins|allowedOriginPatterns|cors", key, re.I)]
    for key in cors_keys:
        if "*" in str(props[key]):
            add("medium", "broad CORS origin policy in prod", key, props[key])
            break

    return findings


def analyze_code_usage(repo: Path, prod_cfg: dict) -> dict:
    exact_refs, prefix_refs = scan_code_refs(repo)
    prod_keys = prod_cfg["properties"].keys()

    exact_missing = [ref for ref in exact_refs if ref["key"] not in prod_keys]
    prefix_missing = [ref for ref in prefix_refs if not any(key == ref["key"] or key.startswith(f"{ref['key']}.") for key in prod_keys)]

    coverage = []
    for key in sorted(prod_keys):
        exact_matches = [ref for ref in exact_refs if ref["key"] == key]
        prefix_matches = [ref for ref in prefix_refs if key == ref["key"] or key.startswith(f"{ref['key']}.")]
        framework = framework_key(key)
        if exact_matches:
            status = "application_exact"
        elif prefix_matches:
            status = "application_prefix"
        elif framework:
            status = "framework_managed"
        else:
            status = "not_found"
        coverage.append(
            {
                "key": key,
                "value": redact(key, prod_cfg["properties"][key]),
                "source": prod_cfg["sources"][key],
                "status": status,
                "severity": severity_for_unused(key),
                "exact_matches": exact_matches,
                "prefix_matches": prefix_matches,
            }
        )

    unused = [item for item in coverage if item["status"] == "not_found"]
    return {
        "exact_refs": exact_refs,
        "prefix_refs": prefix_refs,
        "exact_missing_in_prod": exact_missing,
        "prefix_missing_in_prod": prefix_missing,
        "prod_property_coverage": coverage,
        "prod_properties_without_code": unused,
    }


def scan_code_refs(repo: Path) -> tuple[list[dict], list[dict]]:
    exact_refs: list[dict] = []
    prefix_refs: list[dict] = []
    patterns = ("*.java", "*.kt", "*.groovy")

    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in {".java", ".kt", ".groovy"}:
            continue
        if any(part in {"build", "target", "node_modules", ".git"} for part in path.parts):
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = str(path.relative_to(repo))
        for line_no, line in enumerate(text.splitlines(), start=1):
            for match in re.findall(r'@Value\(\s*"([^"]+)"\s*\)', line):
                for key in parse_placeholders(match):
                    exact_refs.append(ref_entry(rel, line_no, "value", key))
            for match in re.findall(r'(?:getProperty|getRequiredProperty|containsProperty)\(\s*"([^"]+)"', line):
                exact_refs.append(ref_entry(rel, line_no, "environment", match))
            for match in re.findall(r'\.bind\(\s*"([^"]+)"', line):
                prefix_refs.append(ref_entry(rel, line_no, "binder", match))
            for match in re.findall(r'@ConfigurationProperties\(\s*(?:prefix\s*=\s*)?"([^"]+)"', line):
                prefix_refs.append(ref_entry(rel, line_no, "configuration_properties", match))

    return dedupe_refs(exact_refs), dedupe_refs(prefix_refs)


def ref_entry(file_path: str, line: int, kind: str, key: str) -> dict:
    return {"file": file_path, "line": line, "kind": kind, "key": key}


def parse_placeholders(raw: str) -> list[str]:
    keys = []
    for inner in re.findall(r"\$\{([^}]+)\}", raw):
        key = inner.split(":", 1)[0].strip()
        if key and not re.fullmatch(r"[A-Z0-9_]+", key):
            keys.append(key)
    return keys


def dedupe_refs(items: list[dict]) -> list[dict]:
    seen = {}
    for item in items:
        seen[(item["file"], item["line"], item["kind"], item["key"])] = item
    return [seen[key] for key in sorted(seen, key=lambda item: (item[3], item[0], item[1]))]


def find_config_files(repo: Path) -> list[str]:
    matches = []
    for pattern in ("**/application*.properties", "**/application*.yml", "**/application*.yaml", "**/bootstrap*.properties", "**/bootstrap*.yml", "**/bootstrap*.yaml"):
        for path in repo.glob(pattern):
            if path.is_file():
                matches.append(str(path.relative_to(repo)))
    return matches


def redact(key: str, value: str | None) -> str | None:
    if value is None:
        return None
    if re.search(r"password|secret|token|private[-._]?key|credential", key, re.I):
        return "[redacted]"
    return str(value)


def truthy(value: str | None) -> bool:
    return str(value).strip().lower() == "true"


def severity_for(key: str) -> str:
    if any(pattern.search(key) for pattern in HIGH_PATTERNS):
        return "high"
    if any(pattern.search(key) for pattern in MEDIUM_PATTERNS):
        return "medium"
    return "low"


def severity_for_unused(key: str) -> str:
    if re.search(r"datasource|security|password|secret|token|ssl|keystore|truststore", key):
        return "high"
    if re.search(r"url|host|queue|kafka|redis|cache|cors|feature", key):
        return "medium"
    return "low"


def severity_rank(severity: str) -> int:
    return {"high": 0, "medium": 1}.get(severity, 2)


def framework_key(key: str) -> bool:
    return key.startswith(FRAMEWORK_PREFIXES)


def render_markdown(payload: dict) -> str:
    analysis = payload["analysis"]
    code_usage = payload["code_usage"]
    from_label = payload["compared"]["from"]
    to_label = payload["compared"]["to"]
    coverage_counts = Counter(item["status"] for item in code_usage["prod_property_coverage"])
    top_unmapped = [
        item
        for item in sorted(
            code_usage["prod_properties_without_code"],
            key=lambda item: (severity_rank(item["severity"]), item["key"]),
        )
        if item["severity"] in {"high", "medium"}
    ][:20]

    override_note = (
        f"- Override gaps mean `{from_label}` diverged from base while `{to_label}` stayed on the base value."
        if from_label != "base"
        else f"- With source `base`, override gaps highlight values `{to_label}` left on the base value."
    )

    lines = [
        "# Spring Env Audit",
        "",
        f"- Repo: `{payload['repo']}`",
        f"- Spring Boot: `{payload['spring_boot_version'] or 'unknown'}`",
        f"- Compared: `{from_label}` -> `{to_label}`",
        f"- Selection: from `{payload['profile_selection']['from_mode']}`, to `{payload['profile_selection']['to_mode']}`",
        f"- Detected profiles: {', '.join(payload['profile_selection']['detected_profiles']) or 'none'}",
        f"- Config files: {len(payload['config_files'])}",
        f"- Base docs applied: {len(payload['base']['applied_docs'])}",
        "",
        f"## Prod override completeness gaps ({len(analysis['prod_override_completeness_gaps'])})",
        *render_prod_override_gaps(analysis["prod_override_completeness_gaps"], from_label, to_label),
        "",
        f"## {from_label} set, missing in {to_label} ({len(analysis['qa_only'])})",
        *render_key_list(analysis["qa_only"], "from_value"),
        "",
        f"## Different values ({len(analysis['different_values'])})",
        *render_diff_list(analysis["different_values"]),
        "",
        f"## Override gaps vs base ({len(analysis['override_gaps'])})",
        *render_override_gaps(analysis["override_gaps"], from_label, to_label),
        "",
        f"## Override chains ({len(analysis['override_chains'])})",
        *render_override_chains(analysis["override_chains"], from_label, to_label),
        "",
        f"## Prod smells ({len(analysis['smells'])})",
    ]
    if analysis["smells"]:
        for item in analysis["smells"]:
            value = f" = `{item['value']}`" if item.get("value") else ""
            source = f" from `{item['source']}`" if item.get("source") else ""
            lines.append(f"- [{item['severity']}] `{item['key']}` {item['summary']}{value}{source}")
    else:
        lines.append("- none detected from effective repo-local config")

    lines.extend(
        [
            "",
            f"## Code references missing in prod ({len(code_usage['exact_missing_in_prod']) + len(code_usage['prefix_missing_in_prod'])})",
            *render_code_missing(code_usage),
            "",
            "## Prod property coverage summary",
            f"- application_exact: {coverage_counts.get('application_exact', 0)}",
            f"- application_prefix: {coverage_counts.get('application_prefix', 0)}",
            f"- framework_managed: {coverage_counts.get('framework_managed', 0)}",
            f"- not_found: {coverage_counts.get('not_found', 0)}",
            "",
            f"## Highest-signal prod properties likely unused by application code ({len(top_unmapped)})",
            *render_unused_prod_properties(top_unmapped),
            "",
            "## Notes",
            "- Diff is based on effective Spring Boot config resolution from `spring-config-dump`.",
            override_note,
            "- Code-usage scan is heuristic: it checks `@Value`, `Environment#getProperty`, binder calls, and `@ConfigurationProperties` prefixes.",
            "- Review manifests and secrets managers before treating missing prod keys as confirmed issues.",
            "- Use `--format json` when you need the full property-by-property coverage matrix.",
        ]
    )
    return "\n".join(lines)


def render_key_list(items: list[dict], value_key: str) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- [{item['severity']}] `{item['key']}` from `{item['source']}` = `{item[value_key]}`" for item in items]


def render_diff_list(items: list[dict]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- [{item['severity']}] `{item['key']}` `{item['from_value']}` -> `{item['to_value']}`" for item in items]


def render_override_gaps(items: list[dict], from_label: str, to_label: str) -> list[str]:
    if not items:
        return ["- none"]
    return [
        f"- [{item['severity']}] `{item['key']}` base `{item['base_value']}` -> {from_label} `{item['from_value']}` from `{item['from_source']}` while {to_label} stays on base from `{item['to_source']}`"
        for item in items
    ]


def render_override_chains(items: list[dict], from_label: str, to_label: str) -> list[str]:
    if not items:
        return ["- none"]
    lines: list[str] = []
    for item in items[:20]:
        lines.append(f"- [{item['severity']}] `{item['key']}`")
        lines.append(f"  base: {format_chain(item['base'])}")
        if from_label != "base":
            lines.append(f"  {from_label}: {format_chain(item['from'])}")
        lines.append(f"  {to_label}: {format_chain(item['to'])}")
    return lines


def render_prod_override_gaps(items: list[dict], from_label: str, to_label: str) -> list[str]:
    if not items:
        return ["- none"]
    lines = []
    for item in items:
        if item["gap_type"] == "qa_only":
            lines.append(
                f"- [{item['severity']}] `{item['key']}` set in `{from_label}` but missing in `{to_label}`: `{from_label}` has `{item['from_value']}` from `{item['source']}`"
            )
        else:
            lines.append(
                f"- [{item['severity']}] `{item['key']}` `{from_label}` overrides base but `{to_label}` falls back to base: base `{item['base_value']}`, `{from_label}` `{item['from_value']}` from `{item['from_source']}`, `{to_label}` stays on base"
            )
    return lines


def render_code_missing(code_usage: dict) -> list[str]:
    lines = []
    for ref in code_usage["exact_missing_in_prod"]:
        lines.append(f"- [exact] `{ref['key']}` referenced from `{ref['file']}:{ref['line']}` via `{ref['kind']}`")
    for ref in code_usage["prefix_missing_in_prod"]:
        lines.append(f"- [prefix] `{ref['key']}` referenced from `{ref['file']}:{ref['line']}` via `{ref['kind']}`")
    return lines or ["- none"]


def render_unused_prod_properties(items: list[dict]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- [{item['severity']}] `{item['key']}` from `{item['source']}` = `{item['value']}`" for item in items[:50]]


def format_chain(chain: list[dict]) -> str:
    if not chain:
        return "none"
    return " -> ".join(f"`{layer['value']}` @ `{layer['source']}`" for layer in chain)


if __name__ == "__main__":
    sys.exit(main())
