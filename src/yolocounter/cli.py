"""Linha de comando: `yolo-counter count ...`, `yolo-counter evaluate ...` e `yolo-counter serve`."""
from __future__ import annotations

import argparse
import json
import sys

from .geometry import Line


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="yolo-counter", description="Contagem de objetos em vídeo com YOLO.")
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("count", help="contar objetos que cruzam uma linha")
    c.add_argument("source", help="arquivo de vídeo, URL RTSP/HTTP ou índice da webcam (ex.: 0)")
    c.add_argument("--model", default="yolo11n.pt", help="pesos YOLO (padrão: yolo11n.pt, baixado na primeira execução)")
    c.add_argument("--line", type=Line.parse, help='linha "x1,y1,x2,y2" em pixels (padrão: horizontal no meio)')
    c.add_argument("--classes", nargs="+", help="classes a contar, ex.: person car (padrão: todas)")
    c.add_argument("--conf", type=float, default=0.35, help="confiança mínima da detecção")
    c.add_argument("--imgsz", type=int, default=640)
    c.add_argument("--tracker", default="bytetrack.yaml", choices=["bytetrack.yaml", "botsort.yaml"])
    c.add_argument("--anchor", default="bottom", choices=["bottom", "center"], help="ponto da caixa usado na contagem")
    c.add_argument("--device", help='"cpu" ou índice da GPU (padrão: automático)')
    c.add_argument("--output", help="grava o vídeo anotado (.mp4)")
    c.add_argument("--report", help="grava o resumo e os eventos em JSON")
    c.add_argument("--show", action="store_true", help="mostra a janela durante o processamento")

    e = sub.add_parser("evaluate", help="comparar contagens previstas com anotações")
    e.add_argument("predicted", help='JSON {"video": {"in": n, "out": n}}')
    e.add_argument("ground_truth", help="JSON no mesmo formato, com as contagens corretas")

    s = sub.add_parser("serve", help="sobe a interface web")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "count":
        from .pipeline import CountConfig, run_count

        cfg = CountConfig(source=args.source, model=args.model, line=args.line, classes=args.classes,
                          conf=args.conf, imgsz=args.imgsz, tracker=args.tracker, anchor=args.anchor,
                          device=args.device)

        def progress(r):
            if r.index % 50 == 0:
                print(f"\rquadro {r.index}  entradas={r.totals['in']} saídas={r.totals['out']}", end="", file=sys.stderr)

        summary = run_count(cfg, output_video=args.output, show=args.show, progress=progress)
        print(file=sys.stderr)
        print(json.dumps(summary.totals, ensure_ascii=False, indent=2))
        if args.report:
            with open(args.report, "w", encoding="utf-8") as f:
                json.dump(summary.to_dict(), f, ensure_ascii=False, indent=2)
        return 0

    if args.command == "evaluate":
        from .evaluate import count_errors

        with open(args.predicted, encoding="utf-8") as f:
            pred = json.load(f)
        with open(args.ground_truth, encoding="utf-8") as f:
            gt = json.load(f)
        print(json.dumps(count_errors(pred, gt), ensure_ascii=False, indent=2))
        return 0

    if args.command == "serve":
        import uvicorn

        uvicorn.run("yolocounter.web:app", host=args.host, port=args.port)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
