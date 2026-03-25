# MATILDA-Online: important note for Binder users

## ⚠️ Binder is currently less stable than before

MATILDA-Online still runs on **Binder**, but the service is currently under pressure.

- Since the **largest Binder provider (Google)** left the `mybinder.org` federation, overall capacity has been reduced.
- Binder is also experiencing **technical instabilities**, which can lead to repeated server connection interruptions.

Because of this, longer sessions may stop unexpectedly.

---

## ✅ How to work more safely in Binder


### >> Use only *one* notebook at a time! <<

---

### After finishing a notebook:

1. **Download the `output_download.zip` file** as a backup (see below).
2. **Close the notebook and shut down its kernel** (see below).
3. Then open the next notebook.

### 📤 If the server connection breaks:

1. **Restart** the binder.
2. Click on the **upload icon** 📤 in the tool bar.
3. Select your saved **`output_download.zip`** file from your computer
4. Run the Notebook **`Restore_Output_Folder.ipynb`**.
5. When ask, if you want to overwrite the *output/* folder, **type** **`y`**.
6. **Close the Notebook** `Restore_Output_Folder.ipynb` and **shut down the kernel**.
7. Continue with the next notebook in the workflow.





---

## 💾 How to download `output_download.zip` in JupyterLab

In the **file browser** on the left side of JupyterLab:

1. Find the file **`output_download.zip`**
2. **Right-click** the file
3. Choose **Download** and save the file on your computer.

If the Binder session breaks, you can upload it again...

---

## 🔒How to shut down a kernel in JupyterLab:

- Open the **Running Terminals and Kernels** panel in the left sidebar  
  *(usually shown as a* ⏹ *symbol)*
- Under **Kernels**, find the notebook you just used
- Click the 🗙 for **Shut Down** next to that kernel

You can then close the notebook tab.

> **Important:** Closing the notebook tab alone is **not enough**.  
> The kernel may keep running in the background until it is shut down manually.

---

## 🛠️ We are working on better hosting

We are currently exploring other ways to host MATILDA-Online on a more stable platform.

Until then, the most reliable option is to **run the tool locally** on your own computer.

➡️ Please follow the **local installation guidelines** in the Github repository for a more stable experience.
