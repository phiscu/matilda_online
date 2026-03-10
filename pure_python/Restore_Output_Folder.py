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
# # Restore previous results
#
# Use this notebook to restore a saved MATILDA output folder after a Binder interruption.
#
# ## Before you start
#
# Please make sure that:
#
# - your backup file is named **`output_download.zip`**
# - the file is uploaded to the **same folder** as this notebook
#
# ## How to use this notebook
#
# 1. Upload `output_download.zip` to this folder
# 2. Run the code cell below
# 3. Confirm whether the current `output/` folder should be replaced
#
# After that, your saved results should be available again in `output/`.

# %%
from tools.helpers import restore_output_archive

restore_output_archive()
