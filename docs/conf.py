# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys
sys.path.insert(0, os.path.abspath(".."))

project = 'Matilda ONLINE'
copyright = '2025, Alexander Georgi, Phillip Schuster, Mia Janzen'
author = 'Alexander Georgi, Phillip Schuster, Mia Janzen'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

import logging
logging.basicConfig(level=logging.DEBUG)

extensions = [
    'myst_parser',        
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'myst_parser',
    'nbsphinx',
    'sphinx.ext.mathjax'
]

myst_enable_extensions = ["dollarmath"]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

autodoc_mock_imports = [
    'matplotlib','HydroErr', 'hydroeval', 'numpy', 'pandas',
    'plotly', 'scipy', 'xarray', 'DateTime', 'pyyaml',
    'spotpy', 'SciencePlots','fastparquet','seaborn','bias_correction',
    'scienceplots','matilda','probscale','climate_indices','dash','jupyter_server',
    'retry','ee','tqdm'
]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_book_theme'
html_static_path = ['_static']
html_logo = "_static/matilda_cupcake.png"
# html_theme_options = {
#     'logo_only': True,
#     'display_version': False,
# }

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}
