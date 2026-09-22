# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.4
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Welcome to MATILDA-Online
#
# MATILDA is a **notebook-based workflow** for modeling water resources in glacierized catchments.
#
# ## 🧭 How this works
#
# MATILDA is a series of **Jupyter notebooks**. They contain a mix of executable code and descriptive text. There is one notebook for each step of the modeling workflow:
#
# - **Notebook 1** — Catchment delineation and static data acquisition
# - **Notebook 2** — ERA5-Land forcing data  
# - **Notebook 3** — CMIP6 climate projection data  
# - **Notebook 4** — MATILDA model setup and calibration  
# - **Notebook 5** — Scenario simulations  
# - **Notebook 6** — Analysis and visualization
#
# ![logo](images/MATILDA_Logo_processes_30perc.png)
#
# ## 🚀 How to launch the tool
#
# You can run the notebooks either **online** or on your **local** computer.
#
# Choose one way to start:
#
# - **Launch online:** click the **rocket icon** (🚀) above and start the online environment called **Binder**.     ➜     ***Less setup, less easy to run!***
# - **Run locally:** click the **GitHub icon** (<img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" width="18">), open the repository, and follow the setup steps in the manual.     ➜     ***More setup, more easy to run!***
#
# > Before launch, please **read the notes on the different versions** below.
#
# ---
# ## ✅ What you need before continuing
#
# To run MATILDA with the **example data**, you mainly need:
#
# - a stable internet connection
# - enough time for the notebooks to finish processing
#
# To run MATILDA with **your own data**, you additionally need:
#
# - discharge observations (in the same format as the example)
# - gauging station coordinates
#
# ---

# %% [markdown]
# ## 🔀 Two ways to run MATILDA
#
# MATILDA can currently be used in **two different workflows**.
#
# ### ☁️ 1. Web-service workflow (*v2.0.0-beta.2*)
#
# This version is connected to a small web service in the background. Some tasks that were previously run directly with Google Earth Engine from inside the notebook are now sent to this service.
#
# For you as a user, this mainly means:
#
# - the setup is simpler
# - you do not need to complete the Earth Engine registration steps in Binder
# - the notebooks are easier to use in teaching and demonstration settings
#
# <div class="alert alert-block alert-info">
#     <b>Please note:</b> MATILDA-Online is currently under peer-review. During this period, the latest version <b>2.0.0-beta.2 requires an API key</b>. If you have not been provided with one, please use version 1.1.0 (see below).
# </div>
#
# You can start this version directly from this website's toolbar via the **rocket icon** (🚀) for the online option oder the **GitHub icon** (<img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" width="18">) for the local installation.

# %% [markdown]
# ### 🖥️ 2. Fully local workflow (*v1.1.0*)
#
# MATILDA can also be run in a more direct way on your own computer. In that case, requests are processed locally through your own setup rather than through the shared web service.
#
# This workflow gives you more independence and control, but it also requires more preparation.
#
# In particular, you need:
#
# - your own **Google Cloud project**
# - access to **Google Earth Engine**
# - preferably a **local MATILDA installation** since the Binder struggles with multi-processing
#
# This option can be useful if you:
#
# - want to work independently from the shared web service
# - need to process many catchments or larger requests
# - already have experience with the GEE Python API
#
# You can access this version here:
#
# > <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" width="18"> [Repository](https://github.com/phiscu/matilda_online/tree/release-1.x)
#
# > 🚀 [Binder](https://mybinder.org/v2/gh/phiscu/matilda_edu/release-1.x?urlpath=lab/tree/matilda_binder_landing_page.md)
#
# <div class="alert alert-block alert-info">
#     <b>Please note:</b> The MATILDA-Online website only shows the workflow of the latest version.
# </div>

# %% [markdown]
# ## ⏱️ What affects run time?
#
# Especially in Binder, processing time can vary from run to run. This is normal.
#
# The most important reasons are:
#
# - **shared online resources:** Binder sessions do not have dedicated computing power
# - **web-service traffic:** several users may send requests at the same time
# - **cold starts:** the first web-service request usually takes longer
# - **request size:** larger catchments or longer time periods usually take more time
# - **internet connection:** data need to be transferred between your notebook and the service
#
# Because of this, a notebook may finish in a few seconds in one case and take clearly longer in another.
#
# <div class="alert alert-block alert-info">
#     <b>Tip:</b> If a step takes longer than expected, this does not automatically mean that something is wrong.
# </div>

# %% [markdown]
# ## ⚙️ The `config.ini` file
#
# This file contains the main settings for the workflow and allows basic customization.
#
# If you only want to try MATILDA with the example dataset, you usually do not need to change much. If you want to use your own data, replace the discharge observation file in the `input/` folder and adapt the reference coordinates accordingly.

# %% [markdown]
# 1. The first section `[FILE_SETTINGS]` allows you to **edit paths and file names for inputs and outputs**. This is especially useful if you work with more than one catchment in the same copy of the repository.
#
# 2. In the `[CONFIG]` section you can ...
#    - ... specify your **reference coordinates** (usually the gauging station location).
#    - ... select the period used for data download and model calibration.
#    - ... choose the **digital elevation model**.
#    - ... define whether scenario-based **projections** should be created or whether the focus is only on past conditions.
#    - ... disable the generation of **live maps** if needed.
#    - ... configure the **style of output figures**.
#    - ... choose between a faster (`.pickle`) and a more compact (`.parquet`) format for intermediate files.
#    - ... set the number of cores available for computation. If you are in Binder, leave this at 1.
#    - ... decide whether you want to store your output folder in a `.zip` file at the end of each Notebook. This is helpful when you work online and want to download intermediate results.
#
# &nbsp;
# 3. Depending on the workflow branch, some settings may be more relevant than others. In the web-service workflow, parts of the remote data access are already handled in the background. In a fully local workflow, you may need to define your own cloud-related settings more explicitly.

# %% [markdown]
# With the basic setup understood, you may now continue with **[Notebook 1](Notebook1_Catchment_delineation.ipynb)**.
