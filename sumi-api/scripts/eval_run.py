"""
Harness de evals — disparado manualmente pelo dev (nunca no pytest/CI).

    uv run python scripts/eval_run.py                      # estágio roteiro, juiz local
    uv run python scripts/eval_run.py --stage image        # gera N imagens + juiz de visão
    uv run python scripts/eval_run.py --stage calib        # calibra o juiz com PNGs fixos
    uv run python scripts/eval_run.py --judge remote       # juiz gpt-4o (ground truth)
    uv run python scripts/eval_run.py --stage image --samples 2

Estágios:
- `roteiro` (texto, barato): gera o roteiro com o gerador REAL do produto
  (`generate_roteiro`, OpenAI) e um juiz LLM avalia o JSON contra o briefing.
- `image` (visão, caro): para cada caso, define o prompt base — `image_prompt` do caso
  (isola o gpt-image-1) ou, na ausência, o quadro de estabelecimento do roteiro — gera
  N imagens com `gpt-image-1` e o juiz de visão avalia cada uma. O caso passa por maioria.
- `calib` (visão, barato): roda o juiz de visão sobre PNGs versionados em `evals/fixtures/`,
  cada um com um veredito esperado, e mede a taxa de acerto do juiz. Não chama gpt-image-1.

O juiz roda local (Ollama) por padrão. Requer, para gerar roteiro/imagem: DATABASE_URL,
JWT_SECRET_KEY e OPENAI_API_KEY no .env (essa é a parte do produto sob teste).
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "evals"))

from judge import judge_image, judge_roteiro, make_config  # noqa: E402

SEP = "─" * 64

_IMG_PREFIX = (
    "Manga shojo style, black and white screentone, clean ink line art, "
    "no text, no speech bubbles, expressive eyes, high contrast. "
)


def _load_cases(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["cases"]


def _make_cfg(judge_mode: str):  # noqa: ANN202
    key = ""
    if judge_mode == "remote":
        from prompt_clinica.config import settings  # noqa: PLC0415

        key = settings.openai_api_key
    return make_config(judge_mode, openai_api_key=key)


def _gen_roteiro(case: dict) -> dict:
    from prompt_clinica.ai.roteiro import generate_roteiro  # noqa: PLC0415

    return generate_roteiro(
        premise=case["premise"],
        genre=case.get("genre", "Drama"),
        tone=case.get("tone", "Sério"),
        pages=int(case.get("pages", 2)),
        character_names=case.get("characters", []),
    )


def _run_roteiro_stage(cases: list[dict], judge_mode: str, _samples: int) -> list[dict]:
    cfg = _make_cfg(judge_mode)
    print(f"Juiz: {cfg.mode} ({cfg.text_model})")

    results: list[dict] = []
    for case in cases:
        cid = case["id"]
        print(f"\n{SEP}\n▶ {cid}\n{SEP}")
        t0 = time.perf_counter()

        roteiro = _gen_roteiro(case)
        if not roteiro.get("panels"):
            print("  ✗ geração vazia (erro/fallback do gerador — sem painéis).")
            results.append({"id": cid, "passed": False, "reason": "geração vazia"})
            continue

        verdict = judge_roteiro(case, roteiro, cfg)
        verdict["id"] = cid
        verdict["elapsed"] = time.perf_counter() - t0
        results.append(verdict)

        mark = "✓" if verdict["passed"] else "✗"
        print(
            f"  {mark} ambientação={verdict['ambientacao_score']}/5 "
            f"personagens={verdict['personagens_score']}/5"
        )
        if verdict["anacronismos"]:
            print(f"    anacronismos: {', '.join(verdict['anacronismos'])}")
        print(f"    {verdict['justificativa']}")

    return results


def _pick_establishing(panels: list[dict]) -> dict:
    for p in panels:
        if "geral" in str(p.get("framing", "")).lower() or not p.get("character_name"):
            return p
    return panels[0]


def _resolve_base_prompt(case: dict) -> tuple[str | None, str]:
    """Retorna (prompt_base, fonte). prompt_base=None se o roteiro veio vazio."""
    if case.get("image_prompt"):
        return str(case["image_prompt"]), "image_prompt"
    roteiro = _gen_roteiro(case)
    if not roteiro.get("panels"):
        return None, "roteiro"
    panel = _pick_establishing(roteiro["panels"])
    return (panel.get("prompt") or panel.get("caption") or "manga panel"), "roteiro"


def _aggregate_samples(cid: str, samples: list[dict], source: str) -> dict:
    n = len(samples)
    passed_n = sum(1 for s in samples if s["passed"])
    amb = round(sum(s["ambientacao_score"] for s in samples) / n)
    pers = round(sum(s["personagens_score"] for s in samples) / n)
    anac = sorted({a for s in samples for a in s["anacronismos"]})
    rep = next((s for s in samples if not s["passed"]), samples[0])
    return {
        "id": cid,
        "passed": 2 * passed_n > n,  # maioria estrita
        "rate": f"{passed_n}/{n}",
        "ambientacao_score": amb,
        "personagens_score": pers,
        "anacronismos": anac,
        "justificativa": rep["justificativa"],
        "images": [s["image"] for s in samples],
        "source": source,
    }


def _run_image_stage(cases: list[dict], judge_mode: str, samples: int) -> list[dict]:
    from prompt_clinica.ai import ImageRequest, ai  # noqa: PLC0415

    cfg = _make_cfg(judge_mode)
    img_dir = ROOT / "evals" / "reports" / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    print(f"Juiz de visão: {cfg.mode} ({cfg.vision_model}) | amostras/caso: {samples}")

    results: list[dict] = []
    for case in cases:
        cid = case["id"]
        print(f"\n{SEP}\n▶ {cid}\n{SEP}")

        base, source = _resolve_base_prompt(case)
        if base is None:
            print("  ✗ geração de roteiro vazia (sem painéis).")
            results.append({"id": cid, "passed": False, "reason": "roteiro vazio"})
            continue
        print(f"  fonte do prompt: {source}")

        sample_verdicts: list[dict] = []
        for k in range(1, samples + 1):
            resp = ai.image(
                ImageRequest(prompt=_IMG_PREFIX + base, size="1024x1024", quality="medium")
            )
            if not resp.b64_json:
                print(f"    [{k}] ✗ provider não retornou imagem.")
                continue
            img_bytes = base64.b64decode(resp.b64_json)
            name = f"{cid}_{k}.png"
            (img_dir / name).write_bytes(img_bytes)

            v = judge_image(case, img_bytes, cfg)
            v["image"] = name
            sample_verdicts.append(v)
            mark = "✓" if v["passed"] else "✗"
            print(
                f"    [{k}] {mark} amb={v['ambientacao_score']}/5 "
                f"pers={v['personagens_score']}/5 → {name}"
            )

        if not sample_verdicts:
            results.append({"id": cid, "passed": False, "reason": "sem imagem"})
            continue

        rec = _aggregate_samples(cid, sample_verdicts, source)
        results.append(rec)
        mark = "✓" if rec["passed"] else "✗"
        print(f"  {mark} taxa {rec['rate']}  (amb≈{rec['ambientacao_score']} pers≈{rec['personagens_score']})")
        if rec["anacronismos"]:
            print(f"    anacronismos: {', '.join(rec['anacronismos'])}")

    return results


def _run_calib_stage(_cases: list[dict], judge_mode: str, _samples: int) -> list[dict]:
    cfg = _make_cfg(judge_mode)
    fx_dir = ROOT / "evals" / "fixtures"
    fixtures = json.loads((fx_dir / "fixtures.json").read_text(encoding="utf-8"))["fixtures"]
    print(f"Calibração do juiz de visão: {cfg.mode} ({cfg.vision_model}) | {len(fixtures)} fixtures")

    results: list[dict] = []
    for fx in fixtures:
        fid = fx["id"]
        img_bytes = (fx_dir / fx["image"]).read_bytes()
        v = judge_image(fx, img_bytes, cfg)
        correct = v["passed"] == bool(fx["expect_pass"])
        results.append({
            "id": fid,
            "passed": correct,  # "passed" aqui = juiz acertou o rótulo
            "expect_pass": bool(fx["expect_pass"]),
            "judge_passed": v["passed"],
            "ambientacao_score": v["ambientacao_score"],
            "personagens_score": v["personagens_score"],
            "anacronismos": v["anacronismos"],
            "justificativa": v["justificativa"],
            "image": fx["image"],
        })
        mark = "✓ acerto" if correct else "✗ ERRO"
        print(f"\n▶ {fid}: esperado={'passa' if fx['expect_pass'] else 'reprova'} | "
              f"juiz={'passou' if v['passed'] else 'reprovou'} → {mark}")
        print(f"    {v['justificativa']}")

    return results


# ── Relatório ───────────────────────────────────────────────────────

def _header_for(stage: str) -> tuple[str, str]:
    if stage == "image":
        return (
            "| Caso | Result | Taxa | Fonte | Ambientação | Personagens | Anacronismos | Justificativa |",
            "|---|---|---|---|---|---|---|---|",
        )
    if stage == "calib":
        return (
            "| Fixture | Juiz acertou? | Esperado | Juiz | Ambientação | Personagens | Justificativa |",
            "|---|---|---|---|---|---|---|",
        )
    return (
        "| Caso | Result | Ambientação | Personagens | Anacronismos | Justificativa |",
        "|---|---|---|---|---|---|",
    )


def _row_for(stage: str, r: dict) -> str:
    amb = r.get("ambientacao_score", "—")
    pers = r.get("personagens_score", "—")
    just = str(r.get("justificativa", r.get("reason", ""))).replace("|", "/")
    if stage == "image":
        mark = "✅" if r.get("passed") else "❌"
        anac = ", ".join(r.get("anacronismos", [])) or "—"
        rate = r.get("rate", "—")
        src = r.get("source", "—")
        return f"| {r['id']} | {mark} | {rate} | {src} | {amb} | {pers} | {anac} | {just} |"
    if stage == "calib":
        mark = "✅" if r.get("passed") else "❌"
        exp = "passa" if r.get("expect_pass") else "reprova"
        jud = "passou" if r.get("judge_passed") else "reprovou"
        return f"| {r['id']} | {mark} | {exp} | {jud} | {amb} | {pers} | {just} |"
    mark = "✅" if r.get("passed") else "❌"
    anac = ", ".join(r.get("anacronismos", [])) or "—"
    return f"| {r['id']} | {mark} | {amb} | {pers} | {anac} | {just} |"


def _write_report(results: list[dict], judge_mode: str, out_dir: Path, stage: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")  # noqa: DTZ005
    path = out_dir / f"{stamp}_{stage}_{judge_mode}.md"

    passed = sum(1 for r in results if r.get("passed"))
    total = len(results)
    label = "Acertos do juiz" if stage == "calib" else "Aprovados"
    header, sep = _header_for(stage)

    lines = [
        f"# Eval — estágio {stage} ({judge_mode})",
        "",
        f"- Data: {stamp}",
        f"- {label}: **{passed}/{total}**",
        "",
        header,
        sep,
        *[_row_for(stage, r) for r in results],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


_STAGES = {
    "roteiro": _run_roteiro_stage,
    "image": _run_image_stage,
    "calib": _run_calib_stage,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Harness de evals do roteiro/imagem.")
    parser.add_argument("--stage", choices=list(_STAGES), default="roteiro")
    parser.add_argument("--judge", choices=["local", "remote"], default="local")
    parser.add_argument("--samples", type=int, default=3, help="imagens por caso (estágio image)")
    parser.add_argument("--cases", default=str(ROOT / "evals" / "cases.json"))
    parser.add_argument("--out", default=str(ROOT / "evals" / "reports"))
    args = parser.parse_args()

    cases = _load_cases(Path(args.cases))
    results = _STAGES[args.stage](cases, args.judge, args.samples)

    report = _write_report(results, args.judge, Path(args.out), args.stage)
    passed = sum(1 for r in results if r.get("passed"))
    label = "acertos do juiz" if args.stage == "calib" else "aprovados"
    print(f"\n{SEP}\nResultado: {passed}/{len(results)} {label}")
    print(f"Relatório: {report}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
