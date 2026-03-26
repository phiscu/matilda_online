# MATILDA-Online: Workflow for Modeling Water Resources in Glacierized Catchments
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/phiscu/matilda_edu/no_outputs?urlpath=lab/tree/matilda_binder_landing_page.md) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.15712744.svg)](https://doi.org/10.5281/zenodo.15712744) [![Documentation Status](https://readthedocs.org/projects/matilda-online/badge/?version=latest)](https://matilda-online.readthedocs.io/en/latest/)

Welcome to **MATILDA-Online**, the online companion to the **MATILDA** glacio-hydrological modeling framework. This repository hosts the extended MATILDA workflow in form of a Jupyter Book. Designed for researchers, practitioners, and students, this workflow guides users from data acquisition to the analysis of climate change impacts on glacierized catchments.

📚 **Explore the Jupyter Book** on the [MATILDA-Online Website](https://matilda-online.github.io/jbook).

---

## Installation

> **Note:** You are currently using the **beta version (v2.x-beta)** of MATILDA-Online. This version is designed to test a Google-hosted web service that handles requests to Google Earth Engine. During the current peer-review phase, access requires an API key provided by the developers.  
>
> If you would prefer to use the **stable classic workflow (v1.0.2)** with your own Google Cloud project, please use the ***release-1.x*** branch or follow the links below:  
> 💾 [Repository](https://github.com/phiscu/matilda_online/tree/release-1.x)  
> 🚀 [Binder](https://mybinder.org/v2/gh/phiscu/matilda_edu/release-1.x?urlpath=lab/tree/matilda_binder_landing_page.md)

You can run most of the workflow in an online environment hosted on **mybinder.org**. However, model calibration is computationally intensive and can be slow in Binder because only limited computing resources are available. For more comprehensive calibration runs, we recommend downloading the notebooks and running them **locally** on a machine with multiple CPU cores.

MATILDA-Online is designed to be run in **JupyterLab**.

### 1. Install the required tools

Before you begin, make sure the following are installed on your computer:

- **Git** ([Install Git for Windows](https://git-scm.com/download/win))
- **Conda** (we recommend [Miniconda](https://docs.conda.io/en/latest/miniconda.html))

### 2. Clone the repository

Open a terminal.

- On **macOS / Linux**, use your default terminal.
- On **Windows**, use **Anaconda Prompt** (*recommended*), **PowerShell**, or **Git Bash**.

Then run:

```bash
git clone https://github.com/phiscu/matilda_online.git
cd matilda_online
```

### 3. Create the Python environment

Create a new conda environment from the provided `environment.yml` file:

```bash
conda env create -f binder/environment.yml -n matilda_online
```

This may take a few minutes the first time.

### 4. Activate the environment

Activate the new environment:

```bash
conda activate matilda_online
```

If `conda activate` does not work in Windows PowerShell, open **Anaconda Prompt** and run the same command there.

### 5. Install JupyterLab

If JupyterLab is not already included in your environment, install it with:

```bash
conda install -c conda-forge jupyterlab
```

### 6. Launch MATILDA-Online in JupyterLab

From the root folder of the repository, start JupyterLab:

```bash
jupyter lab
```

JupyterLab should open automatically in your browser. If it does not, copy the local URL shown in the terminal and paste it into your browser.

### 7. Open the notebooks

In JupyterLab, navigate to the cloned `matilda_online` folder and open the notebooks in order, starting with the introduction notebook.

---

### Notes for Windows users

- We recommend using **Anaconda Prompt** if you are unfamiliar with the command line.
- If `git` is not recognized, make sure Git is installed and available in your system PATH.
- If `jupyter lab` is not recognized, check that your conda environment is activated before launching it.

---

### Updating the environment

If the `environment.yml` file changes in a future version of the repository, update the environment with:

```bash
conda env update -f binder/environment.yml -n matilda_online --prune
```
---

## Workflow Overview

The MATILDA-Online workflow is organized into a series of interactive Jupyter notebooks. These cover all key steps of modeling water resources in glacierized catchments, including catchment delineation, data acquisition, model calibration, and scenario analysis. Below is a detailed flowchart of the workflow:

![Workflow Flowchart](images/workflow_detailed_2024_-Full_legend.png)

---

## Core Routines

The core routines of MATILDA, including the temperature-index melt model and HBV hydrological model, are maintained in the [MATILDA repository](https://github.com/cryotools/matilda). The MATILDA-Online workflow integrates these routines into a streamlined educational framework.

---

## Authors

- **Alexander Georgi** ([GitHub](https://github.com/geoalxx))
- **Phillip Schuster** ([GitHub](https://github.com/phiscu))
- **Mia Janzen** ([Github](https://github.com/hoepke))

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.




