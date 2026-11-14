from argparse import ArgumentParser
from pathlib import Path
import csv

import numpy as np
from scipy.stats import spearmanr


def main():
    parser = ArgumentParser()

    parser.add_argument(
        "--input",
        type=Path,
        required=True
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True
    )

    args = parser.parse_args()

    with args.input.open(
        encoding="utf-8",
        newline=""
    ) as file:
        rows = list(
            csv.DictReader(file)
        )

    clarity_gt = []
    gradient_p90 = []

    groups = {}

    for row in rows:
        try:
            gt = float(
                row["clarity_gt"]
            )

            metric = float(
                row["clarity_gradient_p90"]
            )

        except (
            ValueError,
            TypeError,
            KeyError
        ):
            continue

        if not (
            np.isfinite(gt)
            and np.isfinite(metric)
        ):
            continue

        clarity_gt.append(gt)
        gradient_p90.append(metric)

        groups.setdefault(
            gt,
            []
        ).append(metric)

    clarity_gt = np.asarray(
        clarity_gt,
        dtype=float
    )

    gradient_p90 = np.asarray(
        gradient_p90,
        dtype=float
    )

    rho, p_value = spearmanr(
        clarity_gt,
        gradient_p90
    )

    lines = []

    lines.append(
        "=== DeepDRiD — Gradient P90 vs claridad experta ==="
    )

    lines.append(
        f"Observaciones válidas: {len(clarity_gt)}"
    )

    lines.append("")

    lines.append(
        "Distribución por nivel de claridad:"
    )

    for gt in sorted(groups):
        values = np.asarray(
            groups[gt],
            dtype=float
        )

        lines.append(
            f"Clarity={gt:g}: "
            f"n={len(values)} | "
            f"mediana={np.median(values):.6f} | "
            f"Q25={np.percentile(values, 25):.6f} | "
            f"Q75={np.percentile(values, 75):.6f}"
        )

    lines.append("")

    lines.append(
        f"Spearman rho: {rho:.6f}"
    )

    lines.append(
        f"p-value: {p_value:.6e}"
    )

    lines.append("")

    if rho > 0:
        lines.append(
            "Dirección: POSITIVA "
            "(mayor Gradient P90 se asocia "
            "con mayor claridad experta)."
        )
    elif rho < 0:
        lines.append(
            "Dirección: NEGATIVA."
        )
    else:
        lines.append(
            "Dirección: SIN ASOCIACIÓN MONÓTONA."
        )

    lines.append("")

    lines.append(
        "Referencia previa — Laplaciano:"
    )

    lines.append(
        "rho = 0.300061"
    )

    lines.append(
        "p = 2.173659e-26"
    )

    lines.append("")

    if rho > 0.300061:
        lines.append(
            "Gradient P90 presenta una asociación "
            "ordinal mayor que el Laplaciano previo."
        )
    elif rho > 0:
        lines.append(
            "Gradient P90 mantiene la dirección "
            "esperada, aunque su asociación ordinal "
            "es menor que la del Laplaciano previo."
        )
    else:
        lines.append(
            "Gradient P90 no mantiene la dirección "
            "esperada en DeepDRiD."
        )

    text = "\n".join(lines)

    print(text)

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    args.output.write_text(
        text + "\n",
        encoding="utf-8"
    )

    print()
    print(
        f"Resultado: {args.output}"
    )


if __name__ == "__main__":
    main()
