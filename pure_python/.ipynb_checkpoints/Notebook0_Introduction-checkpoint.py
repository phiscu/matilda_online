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
# ---
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
# In this branch, the online version is designed to be simple to use. Some data-processing steps are handled through a **web service** in the background instead of running fully inside Binder.
#
# Choose one way to start:
#
# - **Launch online:** open the Binder environment and work through the notebooks in your browser.
# - **Run locally:** download the repository and run the notebooks on your own computer.
#
# ---
# ## ✅ What you need before continuing
#
# To run MATILDA with the **example data** in this branch, you mainly need:
#
# - a stable internet connection
# - enough time for the notebooks to finish processing
#
# To run MATILDA with **your own data**, you additionally need:
#
# - discharge observations (in the same format as the example)
# - gauging station coordinates
#
# If you decide to use the **fully local workflow** instead of the web-service workflow, you will also need:
#
# - your own **Google Cloud / Earth Engine project**
# - permission to use that project
#
# ---
#
# ## 📝 By the end of this Notebook you will have ...
#
# 1. understood how the MATILDA workflow is organized
# 2. learned the difference between the web-service and local workflows
# 3. understood why run times can vary in Binder
# 4. checked the most important settings in the `config.ini`
#
# <div class="alert alert-block alert-info">
#     <b>Good to know:</b> In this branch, you do <b>not</b> need to register Google Earth Engine inside Binder to get started.
# </div>
#
# After that, continue with **Notebook 1**.
#
# ---

# %% [markdown]
# ## ☁️ Two ways to run MATILDA
#
# MATILDA can currently be used in **two different workflows**.
#
# ### 1. Web-service workflow (this branch)
#
# This Binder version is connected to a small web service in the background. Some tasks that were previously run directly with Google Earth Engine from inside the notebook are now sent to this service.
#
# For you as a user, this mainly means:
#
# - the setup is simpler
# - you do not need to complete the Earth Engine registration steps in Binder
# - the notebooks are easier to use in teaching and demonstration settings
#
# <div class="alert alert-block alert-warning">
#     <b>Please note:</b> A simpler setup does not always mean a faster workflow. Run times can still vary depending on server load, internet connection, request size, and the complexity of your catchment.
# </div>

# %% [markdown]
# ### 2. Fully local workflow
#
# MATILDA can also be run in a more direct way on your own computer. In that case, requests are processed locally through your own setup rather than through the shared web service.
#
# This workflow gives you more independence and control, but it also requires more preparation.
#
# In particular, you need:
#
# - your own **Google Cloud project**
# - access to **Google Earth Engine**
# - a local Python environment with the required packages
#
# This option can be useful if you:
#
# - want to work more independently from the shared online environment
# - need to process many catchments or larger requests
# - already have experience with local scientific Python workflows

# %% [markdown]
# ## 🔀 How to switch between workflows
#
# The different MATILDA setups are provided through different **Git branches**.
#
# So, if you want to use another workflow, you usually do **not** need a different tool. You simply use a **different branch** of the repository.
#
# The Binder for the branch with the current web-service based setup can be opened here:
#
# [Launch Binder for the `no_outputs` branch](https://mybinder.org/v2/gh/phiscu/matilda_edu/no_outputs?urlpath=lab/tree/matilda_binder_landing_page.md)

# %% [markdown]
# ## ⏱️ What affects run time?
#
# Especially in Binder, processing time can vary from run to run. This is normal.
#
# The most important reasons are:
#
# - **shared online resources:** Binder sessions do not have dedicated computing power
# - **web-service traffic:** several users may send requests at the same time
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
# ## 📌 Summary
#
# In the current Binder branch, MATILDA is set up to be easier to use:
#
# - no Earth Engine registration is required inside Binder
# - some remote data tasks are handled through a web service
# - run times may still vary because Binder and the service are shared resources
#
# If you prefer a more independent setup, you can use the local workflow on a different branch. This requires your own Google Cloud / Earth Engine project.
#
# With the basic setup understood, you may now continue with **[Notebook 1](Notebook1_Catchment_delineation.ipynb)**.
