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
# You can run the notebooks either **online** or on your **local** computer. *Note that the online environment has only limited computing capacities!*
#
# Choose one way to start from the icons on the left:
#
# - **Launch online:** click the **rocket icon** (🚀) above and start the online environment called **Binder**.
# - **Run locally:** click the **GitHub icon** (<img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" width="18">), open the repository, and follow the setup steps in the manual.
#
# ---
# ## ✅ What you need before continuing
#
# Much of the data acquisition will be done using the [Google Earth Engine](https://earthengine.google.com/) (from here on called **GEE**). So before we can start, we need to **register with GEE and link it to MATILDA**.
#
# To run MATILDA with the **example data**, you need:
#
# - a valid **Google Cloud project ID**
# - permission to use that project
#
# To run MATILDA with **your own data**, you additionally need:
#
# - **discharge observations** (in the same format as the example)
# - **gauging station coordinates**
# ---
#
# ## 📝 By the end of this Notebook you will have ...
#
# 1. understand how the MATILDA workflow is organized
# 2. prepared Google Cloud / Earth Engine access
# 3. found or created a valid Cloud project
# 4. authorized access to this project
# 5. prepared the `config.ini`
#
# <div class="alert alert-block alert-warning">
#     <b>Most important:</b> Without your unique <b>Cloud project ID</b>, you won't be able to use the tool!
# </div>
#
# After that, continue with **Notebook 1**.
#
# ---

# %% [markdown]
# ## ☁️ Google Cloud project: where to start
#
# MATILDA currently requires each user to have her or his own **Google Cloud project ID**.
#
# #### If you already used Google Earth Engine or another Google Cloud service ![gcloud_logo](images/gcloud_logo_30x.png) 
#
# > ➡️ Continue with the <a href="#gee-auth">Authorization tutorial</a>
#
# #### If you are new to these services
#
# > ➡️ Continue with **signing up** right below ⬇️
#
# ---

# %% [markdown]
# ## 🌏 Signing up for Google Earth Engine (GEE)

# %% [markdown]
# <div class="alert alert-block alert-info">
#     <b>Note:</b> We are aware that the Google Cloud setup is getting increasingly complicated. We are currently working on outsourcing the GEE processes to improve the user experience.
# </div>

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
# 9. When you see the green confirmation box, you have sucessfully registered a Google Cloud Project and can continue to use MATILDA-Online 🎉.
#
# ![gcloud_tut_7](images/gcloud_tut_7.png)

# %% [markdown] pycharm={"name": "#%% md\n"}
# <a id="gee-auth"></a>
# ## 🔑 Authorize access for Google Earth Engine

# %% [markdown]
# ### Find your project ID
#
# To tell MATILDA which cloud project to use, we need to store the **projects unique ID** in the *config.ini* file. You can find your project ID when you click on the project name in the tool bar (**1**) of your [Google Cloud Console](http://console.cloud.google.com/) home screen.
#
# ![gcloud_tut_3](images/gcloud_tut_3_2.png)
#
# In the pop-up window you can see the cloud ID in the last column (here *refined_grammar_100722*).
#
# ![gcloud_tut_3_1](images/gcloud_tut_3_1.png)
#

# %% [markdown]
# ### Use your project ID in the notebooks
#
# 1. In the ```config.ini``` file edit the entry ```CLOUD_PROJECT``` and change it to your projects ID.

# %% [markdown]
# 2. The Notebooks that use GEE (1-3) include a cell for initialization and authentification similar to the one below. If it is the first time the GEE API is initialized, a hyperlink will be generated and opened in a pop-up window. *(If there is no pop-up, just copy-paste the url in a browser tab.)*
#
# <div class="alert alert-block alert-info">
#     <b>Note:</b> If you run into any problems regarding authorization, please try the procedure in a <b>private browser tab</b> before contacting us.
# </div>
#
# ![auth_link](images/auth_link.png)
#
# This brings you to a GEE log-in page. There you need to ...

# %% [markdown] pycharm={"name": "#%% md\n"}
# 3. ... choose your account and project and click on *GENERATE TOKEN*. Make sure to **choose the correct combination of account and project** since Google is very strict in terms of account roles and permissions.
#
# ![enter image description here](images/nb0_gee_token_1.png)

# %% [markdown] pycharm={"name": "#%% md\n"}
# 4. If not done already, you will need to sign in to your Google Account. You'll get a security notification for unverified apps. Click *continue*.
#
# ![enter image description here](images/nb0_gee_token_2.png)  

# %% [markdown] pycharm={"name": "#%% md\n"}
# 5. Next, grant your Earth Engine Notebook Client access to your account and click *Continue*.
#
# ![enter image description here](images/nb0_gee_token_3.png)

# %% [markdown]
# 6. Finally, copy the authorization code ...
#  
# ![enter image description here](images/nb0_gee_token_4.png)

# %% [markdown] pycharm={"name": "#%% md\n"}
# 7. ... and paste it into the designated field in the notebook.
#
# ![enter image description here](images/nb0_gee_token_5.png)

# %% [markdown] pycharm={"name": "#%% md\n"}
# 8. You should get a message saying *Successfully saved authorization token.* 🎉 You are now ready to start with the MATILDA workflow. Before we dive into data handling, let's have a look at ...

# %% [markdown]
# ## ⚙️ The *config.ini* file

# %% [markdown]
# This file contains a list of essential information for the workflow and allows customization. If you want to try MATILDA-Online with the example dataset, you only need to edit the entry ```CLOUD_PROJECT``` and change it to your project ID (check the <a href="#gee-auth">Authorization tutorial</a>).  If you want to use your own data, replace the file with the discharge observation in the ```input/``` folder and adapt the reference coordinates accordingly.

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
