import argparse
import csv
import os
import re

import matplotlib.pyplot as plt


LOSS_RE = re.compile(r"Epoch:\s*(\d+),\s*Batch:\s*\d+,\s*Loss:\s*([0-9.]+)")
IOU_RE = re.compile(r"\b(\d+)/(\d+)\s*=\s*([0-9.]+)")


def parse_log(log_path):
    losses = {}
    ious = {}
    pending_validation_epoch = None

    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            loss_match = LOSS_RE.search(line)
            if loss_match:
                epoch = int(loss_match.group(1))
                loss = float(loss_match.group(2))
                losses.setdefault(epoch, []).append(loss)
                continue

            if "Validating" in line:
                previous_epochs = sorted(losses)
                if previous_epochs:
                    pending_validation_epoch = previous_epochs[-1]
                continue

            iou_match = IOU_RE.search(line)
            if iou_match and pending_validation_epoch is not None:
                ious[pending_validation_epoch] = float(iou_match.group(3))
                pending_validation_epoch = None

    avg_losses = {
        epoch: sum(values) / len(values)
        for epoch, values in losses.items()
        if values
    }
    return avg_losses, ious


def main():
    parser = argparse.ArgumentParser(description="Plot training loss and validation IoU from Project4 log.log files.")
    parser.add_argument("log_dirs", nargs="+", help="Training run directories under logs/")
    parser.add_argument("--output", default="training_curves.png", help="Output PNG path")
    parser.add_argument("--csv-output", default="training_curves.csv", help="Output CSV path")
    args = parser.parse_args()

    losses = {}
    ious = {}
    for log_dir in args.log_dirs:
        log_path = os.path.join(log_dir, "log.log")
        run_losses, run_ious = parse_log(log_path)
        losses.update(run_losses)
        ious.update(run_ious)

    epochs = sorted(set(losses) | set(ious))
    if not epochs:
        raise RuntimeError("No epoch data found in the provided logs.")

    with open(args.csv_output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["epoch", "train_loss", "val_iou"])
        for epoch in epochs:
            writer.writerow([epoch, losses.get(epoch, ""), ious.get(epoch, "")])

    fig, ax_loss = plt.subplots(figsize=(9, 5))
    loss_epochs = sorted(losses)
    iou_epochs = sorted(ious)

    ax_loss.plot(loss_epochs, [losses[e] for e in loss_epochs], marker="o", label="Training Loss", color="#1f77b4")
    ax_loss.set_xlabel("Epoch")
    ax_loss.set_ylabel("Training Loss", color="#1f77b4")
    ax_loss.tick_params(axis="y", labelcolor="#1f77b4")
    ax_loss.grid(True, alpha=0.3)

    ax_iou = ax_loss.twinx()
    ax_iou.plot(iou_epochs, [ious[e] for e in iou_epochs], marker="s", label="Validation IoU", color="#d62728")
    ax_iou.set_ylabel("Validation IoU", color="#d62728")
    ax_iou.tick_params(axis="y", labelcolor="#d62728")
    ax_iou.set_ylim(0, 1.05)

    lines_1, labels_1 = ax_loss.get_legend_handles_labels()
    lines_2, labels_2 = ax_iou.get_legend_handles_labels()
    ax_loss.legend(lines_1 + lines_2, labels_1 + labels_2, loc="best")

    plt.title("Training Loss and Validation IoU")
    fig.tight_layout()
    fig.savefig(args.output, dpi=200)
    print(f"Saved {args.output}")
    print(f"Saved {args.csv_output}")


if __name__ == "__main__":
    main()
