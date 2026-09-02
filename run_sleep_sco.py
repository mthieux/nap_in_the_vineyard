"""
# Nap_in_the_vineyard - V1 - 26/08/2026 - Adapted by Marine Thieux (UR2NF-CRCN/LN2T - ULB), built for python => 3.9

Based on Combrisson E, Vallat R, Eichenlaub J-B, O’Reilly C,Lajnef T, Guillot A, Ruby P and Jerbi K (2017).  
         Sleep: An Open-Source Python Software for Visualization, Analysis, and Staging of Sleep Data. Front. Neuroinform. 11:60.  
         doi:10.3389/fninf.2017.00060 
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence

import mne
import numpy as np
from sleep_scoring.gui import Sleep


STAGE_MAPPING = {
    "W": 0,
    "WAKE": 0,
    "N1": 1,
    "N2": 2,
    "N3": 3,
    "R": 4,
    "REM": 4,
    "ART": -1,
    "A": -1,
    "U": -1,
    "UNKNOWN": -1,
}
EEG_CHANNEL_RENAME = {
    "eegch1": "T9",
    "eegch2": "Fp1",
    "eegch3": "Fp2",
    "eegch4": "T10",
}


def read_recording(edf_path: str | os.PathLike[str]) -> tuple[np.ndarray, float, list[str], datetime | None]:
    path = Path(edf_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"EDF file not found: {path}")

    raw = mne.io.read_raw(path, preload=True)
    if "eeg" in path.name.lower() and "tsss" not in path.name.lower():
        rename = {
            old: new
            for old, new in EEG_CHANNEL_RENAME.items()
            if old in raw.ch_names
        }
        if rename:
            raw.rename_channels(rename)
            raw.set_montage(
                mne.channels.make_standard_montage("standard_1020"),
                on_missing="warn",
            )

    return (
        raw.get_data().astype(np.float32),
        float(raw.info["sfreq"]),
        list(raw.info["ch_names"]),
        raw.info["meas_date"],
    )


def csv_to_hypnogram(
    csv_path: str | os.PathLike[str],
    sf: float,
    edf_start_time: datetime | None,
    n_samples: int,
    epoch_duration: float = 30,
    csv_to_edf_offset_hours: float = 1,
) -> np.ndarray:
    path = Path(csv_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Hypnogram CSV not found: {path}")
    if edf_start_time is None:
        raise ValueError("The EDF has no measurement start time; CSV alignment is unavailable.")
    if sf <= 0 or epoch_duration <= 0 or n_samples < 0:
        raise ValueError("sf, epoch_duration, and n_samples must be valid positive values.")

    if path.suffix.lower() == ".txt":
        with path.open() as text_file:
            text_values = [
                line.split()[0]
                for line in text_file
                if line.strip() and not line.lstrip().startswith("#")
            ]
        if not text_values:
            raise ValueError("Hypnogram text file is empty.")

        def parse_stage(value: str) -> int:
            label = value.strip().upper()
            if label in STAGE_MAPPING:
                return STAGE_MAPPING[label]
            try:
                numeric = float(label)
            except ValueError as error:
                raise ValueError(f"Invalid sleep stage in text file: {value}") from error
            if not np.isfinite(numeric) or numeric not in {-1, 0, 1, 2, 3, 4}:
                raise ValueError(f"Invalid sleep stage in text file: {value}")
            return int(numeric)

        text_stages = np.asarray([parse_stage(value) for value in text_values], dtype = np.int16)
        if len(text_stages) == n_samples:
            return text_stages
        hypnogram = np.repeat(text_stages, round(sf * epoch_duration))
        if len(hypnogram) < n_samples:
            hypnogram = np.pad(hypnogram, (0, n_samples - len(hypnogram)), constant_values = -1)
        return hypnogram[:n_samples]

    with path.open(newline = "") as csv_file:
        rows = list(csv.reader(csv_file))
    if not rows:
        raise ValueError("Hypnogram CSV is empty.")

    header = [column.strip() for column in rows[0]]
    required_columns = {"sleep_stage", "timestamps"}
    missing_columns = required_columns.difference(header)
    if missing_columns:
        # Converted hypnograms contain one numeric stage per sample and no header.
        if len(header) == 1:
            sample_values = [row[0].strip() for row in rows if row]
            try:
                sample_stages = np.asarray(sample_values, dtype = np.float64)
            except ValueError as error:
                raise ValueError(
                    "Sample-level hypnogram contains invalid stage values."
                ) from error
            if not np.isfinite(sample_stages).all():
                raise ValueError("Sample-level hypnogram contains invalid stage values.")
            hypnogram = sample_stages.astype(np.int16)
            if len(hypnogram) < n_samples:
                hypnogram = np.pad(
                    hypnogram, (0, n_samples - len(hypnogram)), constant_values = -1
                )
            return hypnogram[:n_samples]
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"CSV is missing required column(s): {missing}")

    timestamp_index = header.index("timestamps")
    stage_index = header.index("sleep_stage")
    timestamped_rows = []
    for row in rows[1:]:
        if len(row) <= max(timestamp_index, stage_index):
            continue
        try:
            timestamp = float(row[timestamp_index])
        except ValueError:
            continue
        if np.isfinite(timestamp):
            timestamped_rows.append((timestamp, row[stage_index]))
    if not timestamped_rows:
        raise ValueError("No valid timestamps found in CSV.")

    csv_start = datetime.fromtimestamp(
        timestamped_rows[0][0],
        tz=timezone.utc,
    )
    hypnogram_start = csv_start + timedelta(hours = csv_to_edf_offset_hours)
    if edf_start_time.tzinfo is None:
        edf_start_time = edf_start_time.replace(tzinfo = timezone.utc)
    offset_samples = round((hypnogram_start - edf_start_time).total_seconds() * sf)

    stages = np.asarray(
        [STAGE_MAPPING.get(stage.strip().upper(), -1) for _, stage in timestamped_rows],
        dtype=np.int16,
    )
    samples_per_epoch = round(sf * epoch_duration)
    hypnogram = np.repeat(stages, samples_per_epoch)

    if offset_samples > 0:
        hypnogram = np.concatenate((np.full(offset_samples, -1, dtype=np.int16), hypnogram))
    elif offset_samples < 0:
        hypnogram = hypnogram[abs(offset_samples):]

    if len(hypnogram) < n_samples:
        hypnogram = np.pad(hypnogram, (0, n_samples - len(hypnogram)), constant_values = -1)
    return hypnogram[:n_samples]


def select_file(title: str, file_filter: str) -> str | None:
    from PyQt5.QtWidgets import QApplication, QFileDialog

    app = QApplication.instance() or QApplication([])
    selected, _ = QFileDialog.getOpenFileName(None, title, "", file_filter)
    del app
    return selected or None


def launch(
    edf_path: str | os.PathLike[str],
    hypnogram_path: str | os.PathLike[str] | None = None,
    epoch_duration: float = 30,
    csv_to_edf_offset_hours: float = 1,
) -> None:
    data, sf, channels, edf_start_time = read_recording(edf_path)
    hypnogram = np.zeros(data.shape[1], dtype = np.int16)
    if hypnogram_path is not None:
        hypnogram = csv_to_hypnogram(
            hypnogram_path,
            sf,
            edf_start_time,
            data.shape[1],
            epoch_duration,
            csv_to_edf_offset_hours,
        )

    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance()
    owns_app = app is None
    if owns_app:
        app = QApplication(sys.argv)
    sleep_gui = Sleep(data=data, sf=sf, channels=channels, hypno=hypnogram)
    sleep_gui.show()
    if owns_app:
        sys.exit(app.exec_())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument("edf", nargs = "?", help = "EDF recording; omit to choose it in a file dialog")
    parser.add_argument("--hypnogram", help = "optional CSV hypnogram")
    parser.add_argument("--epoch-duration", type = float, default = 30, help = "hypnogram epoch duration in seconds (default: 30)")
    parser.add_argument("--csv-to-edf-offset-hours", type = float, default = 1, help = "timestamp correction (default: 1)")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    edf_path = args.edf or select_file(
        "Select recording",
        "Supported recordings (*.edf *.bdf *.gdf *.vhdr *.eeg *.cnt *.set *.egi *.rec *.trc);;All files (*)",
    )
    if not edf_path:
        print("No EDF selected.")
        return

    hypnogram_path = args.hypnogram
    if hypnogram_path is None:
        hypnogram_path = select_file(
            "Select hypnogram (Cancel for none)",
            "Hypnogram files (*.csv *.txt);;CSV files (*.csv);;Text files (*.txt);;All files (*)",
        )

    launch(
        edf_path,
        hypnogram_path,
        args.epoch_duration,
        args.csv_to_edf_offset_hours,
    )


if __name__ == "__main__":
    main()
