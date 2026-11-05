# Nap in the Vineyard 🍇

A lightweight Python launcher for visualizing and scoring sleep / EEG recordings, adapted from the [sleep-scoring](https://pypi.org/project/sleep-scoring/) software and configured for the data formats and workflows used in the UR2NF / LN2T lab. 

<p align="center"> <img src="nap_in_the_vineyard.png" alt="Nap in the Vineyard" width="250"> </p>

## What is this?
Nap in the vineyard is a small standalone wrapper around the Python [sleep-scoring](https://pypi.org/project/sleep-scoring/) software. 
It provides a simple way to: 
- open EEG recordings in common electrophysiological formats, 
- optionnally load an existing hypnogram,
- visualize recordings for sleep scoring. 
The project is intented for lab use. 

## What to see:
- `run_sleep_sco.py`: the application launcher and hypnogram conversion logic
- `launch.sh` and `setup.sh`: macOS/Linux helpers for starting the application and creating its environment
- `requirements.txt`: pinned package versions
- `README.md`: this guide

Every user should create a separate Python environment for this project.

## Prerequisites
The application was initially developed and tested on macOS (Apple Silicon). Python 3.9 is the recommended version for both macOS and Windows. The Windows instructions below use native Windows Python; Windows support has not been tested across all hardware and graphics drivers.

The GUI uses Qt, VisPy, and OpenGL. Windows Subsystem for Linux (WSL) can have display or OpenGL compatibility issues, so run the application directly on Windows instead of through WSL. Keep your graphics drivers up to date.

Install Python 3.9 from [python.org](https://www.python.org/downloads/release/python-3913/) or use a Conda environment. Confirm Python is available:

```bash
python3.9 --version
```
The pinned packages come from PyPI. Other Python versions or platforms may need adjustments. In VS Code, install the Microsoft **Python** extension.

## One-time installation
### macOS

Open Terminal, move to the project folder, and run:

```bash
cd /path/to/nap_in_the_vineyard-main
./setup.sh
```

The script creates `.venv`, upgrades `pip`, and installs the packages listed in `requirements.txt`. If Python 3.9 is not the default `python3`, specify its path:

```bash
PYTHON_BIN=/full/path/to/python3.9 ./setup.sh
```

### Windows (PowerShell)

Open PowerShell in the project folder. Create a virtual environment and install the dependencies:

```powershell
py -3.9 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Alternatively, create and activate a Conda environment, then install the same requirements:

```powershell
conda create -n nap-in-the-vineyard python=3.9
conda activate nap-in-the-vineyard
python -m pip install -r requirements.txt
```

Run the setup once per environment. Reinstall the requirements after they change.

## Run the application
### macOS

Use the project launcher, which runs `run_sleep_sco.py` with the local `.venv`:

```bash
./launch.sh
```

The recording picker opens first, followed by an optional hypnogram picker. Cancel the hypnogram picker to continue without one. You can also pass paths directly:

```bash
./launch.sh /path/to/recording.edf --hypnogram /path/to/stages.csv
```

### Windows (PowerShell)

Run the script directly with the Python interpreter in `.venv`; do not use the Bash launcher:

```powershell
.\.venv\Scripts\python.exe .\run_sleep_sco.py
```

The recording picker opens first, followed by an optional hypnogram picker. To pass paths directly, use Windows paths in quotes:

```powershell
.\.venv\Scripts\python.exe .\run_sleep_sco.py "C:\data\recording.edf" --hypnogram "C:\data\stages.csv"
```

The application needs a real desktop and an available OpenGL graphics driver. Do not set `QT_QPA_PLATFORM` to `offscreen`. Keep the terminal open while the application is running; close the application window to end the process.

## Supported files
Recording formats include `.edf`, `.bdf`, `.gdf`, `.vhdr`, `.eeg`, `.cnt`, `.set`, `.egi`, `.rec`, and `.trc`. EEGLAB `.set` files are supported through MNE and the `pymatreader` dependency included in `requirements.txt`. Some formats require companion files in the same folder, such as BrainVision `.vhdr`, `.eeg`, and `.vmrk`.

Hypnograms can be `.csv` or `.txt`. A TXT file contains one stage per line, either labels (`W`, `N1`, `N2`, `N3`, `R`, `U`) or numeric values (`-1` to `4`) with: 
- W / WAKE = 0 
- N1 = 1
- N2 = 2
- N3 = 3
- R / REM = 4
- ART / A / U / UNKNOWN = -1 
Epoch labels are expanded using the default 30-second epoch duration.

The converted sample-level CSV can also be used directly. On macOS:

```bash
./launch.sh recording.edf --hypnogram stages_converted.csv
```
On Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe .\run_sleep_sco.py "C:\data\recording.edf" --hypnogram "C:\data\stages_converted.csv"
```

For timestamped hypnograms, the timestamps are used to align the hypnogram with the time stored in the EEG file. 
The default timestamp correction is +1 hour, which specific to the data workflow for which this adaptation was developed. 
Check the timestamps before using a different value. This can be changed on macOS:

```bash
./launch.sh recording.edf --hypnogram stages.csv --csv-to-edf-offset-hours 2
```
Or on Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe .\run_sleep_sco.py "C:\data\recording.edf" --hypnogram "C:\data\stages.csv" --csv-to-edf-offset-hours 2
```

## VS Code
Use **Python: Select Interpreter** and choose:

```text
macOS:  /path/to/nap_in_the_vineyard-main/.venv/bin/python
Windows: .venv\Scripts\python.exe
```

On macOS, run `./launch.sh` from the integrated terminal. On Windows, run `run_sleep_sco.py` with the selected project interpreter. Avoid system Python interpreters that do not have the project dependencies installed.

## Lab-specific adaptations
This project adapt the original software to the EEG files used in our lab. 

For EEG-MEG recordings whose filename contains *tsss*, the channel names are kept unchanged.

For Muse® recordings whose filename contains *eeg*, a standard 10-20 montage is applied and the following channel names are automatically renamed: 
- eegch1 = T9
- eegch2 = Fp1
- eegch3 = Fp2
- eegch4 = T10

If needed, modify the EEG_CHANNEL_RENAME in `run_sleep_sco.py`

## Expected warnings
Some EEG files may report that channels have no standard 10-20 montage position. The launcher keeps those channels and continues. The laucher may also warn about data amplitude; inspect the recording units before making scientific interpretations.

## Origin and attribution
This project is an adaptation of [sleep-scoring](https://github.com/x64-bit/sleep-scoring/tree/main) software. 

The original work is: 
Combrisson E, Vallat R, Eichenlaub J-B, O’Reilly C,Lajnef T, Guillot A, Ruby P and Jerbi K (2017). Sleep: An Open-Source Python Software for Visualization, Analysis, and Staging of Sleep Data. Front. Neuroinform. 11:60. doi:[10.3389/fninf.2017.00060](https://www.frontiersin.org/journals/neuroinformatics/articles/10.3389/fninf.2017.00060/full) 

This repository is intented to be useful to UR2NF / LN2T members. 
Please fork the repository and adapt it to your own workflow. 

Adapted by Marine Thieux with contributions from Dimitri Voisin, and Burgundy roots. 