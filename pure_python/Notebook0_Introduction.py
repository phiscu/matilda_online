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
# # Introduction

# %% [markdown]
# Welcome to **MATILDA-Online**, the Python-based workflow for **Modeling Water Resources in Glacierized Catchments**! This book describes the comprehensive toolkit in detail and guides you step-by-step from data acquisition to analysis of climate change impacts on the selected catchment. Designed with flexibility and accessibility in mind, MATILDA integrates robust scientific models, public data sources, and user-friendly tools to make sophisticated glacio-hydrological modeling accessible to researchers, practitioners, and students alike.
#
# The workflow is divided into a series of interactive notebooks, each focused on a specific component of the modeling process. These notebooks streamline complex tasks such as catchment delineation, data processing, model calibration, and climate scenario analysis, ensuring clarity and reproducibility at each step:
#
# - **[Notebook 1 - Catchment Delineation](Notebook1_Catchment_delineation.ipynb):** Delineate your catchment and retrieve static geospatial data, including digital elevation models, glacier outlines, and ice thickness distributions.
#   
# - **[Notebook 2 - Forcing Data](Notebook2_Forcing_data.ipynb):** Acquire and process ERA5-Land reanalysis data, preparing inputs for glacio-hydrological model calibration.
#
# - **[Notebook 3 - CMIP6 Climate Data](Notebook3_CMIP6.ipynb):** Download and process historical and future climate data from the Coupled Model Intercomparison Project Phase 6 (CMIP6) for two emission scenarios.
#
# - **[Notebook 4 - MATILDA Model](Notebook4_MATILDA.ipynb):** Run the MATILDA model with default parameters and calibrate it based on mutiple objectives.
#
# - **[Notebook 5 - Scenario Simulations](Notebook5_MATILDA_scenarios.ipynb):** Apply your calibrated parameter set to run the model over all CMIP6 ensemble members for robust scenario-based analysis.
#
# - **[Notebook 6 - Result Analysis & Impact Assessment](Notebook6_Analysis.ipynb):** Visualize model output in interactive plots across ensemble simulations, extract key meteorological and hydrological indicators of of climate change impacts, and create a visual summary.
#
#
# The workflow below is demonstrated using a sample site in the Tian Shan Mountains of Kyrgyzstan. To try the toolkit for yourself, simply click on the rocket icon in the toolbar above to launch an online environment hosted by [mybinder.org](https://mybinder.org/). There you can run any notebook with the sample data or upload your own and edit the config file accordingly. Note that while most of the workflow will work fine in the binder, calibrating the model is computationally intensive and will be slow to run on a single CPU. For a comprehensive calibration that takes full advantage of the [spotpy](https://spotpy.readthedocs.io/en/latest/) library, we recommend downloading the notebooks and running them on a local machine with multi-core processing capabilities. Additional options to reduce calibration time are described in Notebook 4.
#
# Have fun exploring and happy modeling!
#
# ![flowchart](images/workflow_detailed_2024_-Full_legend.png)

# %% [markdown]
# ## Signing up for Google Earth Engine (GEE)

# %% [markdown]
# Much of the data acquisition will be done using the [Google Earth Engine Python API](https://developers.google.com/earth-engine/tutorials/community/intro-to-python-api). This not only allows us to access an unique collection of public datasets but to "outsource" most of their preprocessing to Google servers. 
#
# <div class="alert alert-block alert-info">
#     <b>Note:</b> Currently, every user must use their own Google Cloud Project to access MATILDA-Online. However, the latest updates to the Google Cloud Services website and security policy now require users to answer a questionnaire when registering their projects as non-commercial in order to use the service for free. We are currently working on outsourcing the GEE processes to improve the user experience.
# </div>
#
#
# If you already have a Google Cloud project from previous work, continue with [authorization of GEE](#gee-auth). If you have never used GEE or another Google Cloud service before, sign up as follows.

# %% [markdown]
# 1. To start visit the [Earth Engine website](https://earthengine.google.com/) and click on *Get Started* in the top right corner.
#
# ![enter image description here](https://i.postimg.cc/nzMyrSfG/start2.png)

# %% [markdown]
# 2. Log into your Google account or [create one](https://accounts.google.com/signup) using any email adress.
#
# ![enter image description here](https://i.postimg.cc/7YQqNzm6/sign-in-google.png)

# %% [markdown]
# 3. Once you signed in, click on *Continue* to agree that your e-mail address is used by the Earth Engine Code Editor.
#
# ![gcloud_tut_1](images/gcloud_tut_1.png)

# %% [markdown]
# 4. Next, click *Allow* to grant the Code Editor the required permissions.
#
# ![gcloud_tut_2](images/gcloud_tut_2.png)

# %% [markdown]
# <a id="step-5">5. </a>A default cloud project called "My Project" is created for you. If you click on the project name in the tool bar (**1**)...
#
#
# ![gcloud_tut_3](images/gcloud_tut_3.png)
#
# ... you will see a pop-up window where you can add, delete or rename cloud projects. You can also see the cloud ID of your project (here *refined_grammar_100722*). You will need **your** ID later to tell MATILDA-Online which cloud project to use.
#
# ![gcloud_tut_3_1](images/gcloud_tut_3_1.png)
#
# Close the pop-up window, to continue to register your project as either commercial or non-commercial. In the current setup, MATILDA-Online is designed as a *non-commercial* tool. Therefore, we only describe the process for scientific or educational applications. To do so, click on *Get started* in the lower box (**2**).

# %% [markdown]
# 6. On the following page click *Get started* once again.
#
# ![gcloud_tut_4](images/gcloud_tut_4.png)

# %% [markdown]
# 7. Complete the questionnaire with your background and institution and click *Register* to submit it. A free community plan is sufficient for using the tool.
#
# ![gcloud_tut_5](images/gcloud_tut_5.png)

# %% [markdown]
# 8. Finally, *enable* the Earth Engine API and wait for the process to finish.
#
# ![gcloud_tut_6](images/gcloud_tut_6.png)

# %% [markdown]
# 9. When you see the green confirmation box, you have sucessfully registered a Google Cloud Project and can continue to use MATILDA-Online.
#
# ![gcloud_tut_7](images/gcloud_tut_7.png)

# %% [markdown] pycharm={"name": "#%% md\n"}
# <a id="gee-auth"></a>
# ## Authorize access for Google Earth Engine

# %% [markdown]
# <div class="alert alert-block alert-info">
#     <b>Note:</b> If you run into any problems regarding authorization, please try the procedure in a <b>private browser tab</b> before contacting us.
# </div>
#
# The Notebooks that use GEE (1-3) include a cell for initialization and authentification similar to the one below. If it is the first time the GEE API is initialized, a hyperlink will be generated and (if your browser allows) opened in a pop-up window. *(If there is no pop-up, just copy-paste the url in a browser tab.)*
#
# ![auth_link](images/auth_link.png)
#
# This brings you to a GEE log-in page. There you need to ...

# %% [markdown] pycharm={"name": "#%% md\n"}
# 1. Choose your account and project and click on *GENERATE TOKEN*. Make sure to **choose the correct combination of account and project** since Google is very strict in terms of account roles and permissions.
#
# ![enter image description here](images/nb0_gee_token_1.png)

# %% [markdown] pycharm={"name": "#%% md\n"}
# 2. If not done already, you will need to sign in to your Google Account. You'll get a security notification for unverified apps. Click *continue*.
#
# ![enter image description here](https://i.postimg.cc/8PzQmGk8/continue.png)  

# %% [markdown] pycharm={"name": "#%% md\n"}
# 3. Next, grant your Earth Engine Notebook Client access to your account and click *Continue*.
#
# ![enter image description here](images/nb0_gee_token_3.png)

# %% [markdown]
# 4. Finally, copy the authorisation code ...
#  
# ![enter image description here](images/nb0_gee_token_4.png)

# %% [markdown] pycharm={"name": "#%% md\n"}
# 5. ... and paste it into the designated field in the notebook.
#
# ![enter image description here](https://i.postimg.cc/ZnfQM9bG/enter-code.png)

# %% [markdown] pycharm={"name": "#%% md\n"}
# 6. You should get a message saying *Successfully saved authorization token.* You are now ready to start with the MATILDA workflow. Before we dive into data handling, let's have a look at ...

# %% [markdown]
# ## The *config.ini* file

# %% [markdown]
# This file contains a list of essential information for the workflow and allows customization. If you want to try MATILDA-Online with the example dataset, you only need to edit the entry ```CLOUD_PROJECT``` and change it to your projects name from <a href="#step-5">Step 5</a>.  If you want to use your own data, replace the file with the discharge observation in the ```input/``` folder and adapt the reference coordinates accordingly.

# %% [markdown]
# 1. The first section ```[FILE_SETTINGS]``` allows you to **edit paths and file names for in- and outputs**. This can especially be useful if you model multiple catchments in the same copy of the repository.
#
# 2. In the ```[CONFIG]``` section you can ...
#    - ... specify your **Google Cloud project**. This information is **mandatory** to use the GEE in the workflow. The current project ```matilda-edu``` is set up for demonstration purposes and is not publicly accessible.
#    - ... specify your **reference coordinates** (usually your gauging station location) and select the calibration period. The latter should cover your observation period plus a few years before as a spin-off.
#    - ... specify the calibration period of the hydrlogical model depending on your data.
#    - ... change the **digital elevation model** used.
#    - ... choose download option from GEE (direct download or via ```xarray```).
#    - ... choose whether to create scenario-based **projections** or just model the past.
#    - ... disable the generation of **live maps**.
#    - ... configure the **style of output figures**. More information about the available styles can be found in the **[SciencePlots manual](https://github.com/garrettj403/SciencePlots/wiki/Gallery)**.
#    - ... choose between a faster (```.pickle```) and a more compact (```.parquet```) format for intermediate files.
#    - ... set the number of cores available for computation. If you are in a binder, leave this at 1.
#    - ... decide whether you want to store your output folder in a `.zip` file at the end of every Notebook. This is useful when you work online and want to download your (intermediate) results.
#
# &nbsp;
# 3. The last section ```[MEDIA_SERVER]``` holds credentials for the file access on a file repository of our university and should not be edited if you are not a university member and know what you're doing. The credentials only grant read access to glacier-related public data and are not of value to you.

# %% [markdown]
# With the ```config.ini``` set up, you may now start with **[Notebook 1](Notebook1_Catchment_delineation.ipynb)**.
