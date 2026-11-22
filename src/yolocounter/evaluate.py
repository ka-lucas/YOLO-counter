"""Compara contagens previstas com contagens anotadas à mão (verdade de campo)."""
from __future__ import annotations


def count_errors(predicted: dict[str, dict], ground_truth: dict[str, dict]) -> dict:
    """predicted / ground_truth: {nome_do_video: {"in": n, "out": n}}.

    Retorna o erro absoluto por vídeo e as médias: MAE das contagens e erro relativo do total.
    """
    rows = []
    for name, gt in ground_truth.items():
        pred = predicted.get(name)
        if pred is None:
            raise KeyError(f"sem previsão para o vídeo {name!r}")
        row = {"video": name}
        for k in ("in", "out"):
            row[f"{k}_gt"], row[f"{k}_pred"] = gt.get(k, 0), pred.get(k, 0)
            row[f"{k}_abs_err"] = abs(row[f"{k}_pred"] - row[f"{k}_gt"])
        total_gt = row["in_gt"] + row["out_gt"]
        total_pred = row["in_pred"] + row["out_pred"]
        row["total_rel_err"] = abs(total_pred - total_gt) / total_gt if total_gt else float(total_pred > 0)
        rows.append(row)
    n = len(rows)
    return {
        "videos": rows,
        "mae_in": sum(r["in_abs_err"] for r in rows) / n,
        "mae_out": sum(r["out_abs_err"] for r in rows) / n,
        "mean_total_rel_err": sum(r["total_rel_err"] for r in rows) / n,
    }
