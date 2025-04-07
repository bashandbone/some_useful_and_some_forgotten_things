# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys

sys.path.insert(0, os.path.abspath("../../"))

project = "fedcal"
copyright = "2023, Adam Poulemanos"
author = "Adam Poulemanos"

version = "pre-alpha"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    # 'sphinx.ext.autodoc'
    # 'autoapi.extension',
    "sphinx.ext.intersphinx",
    #    'sphinxcontrib-napoleon',
    "sphinx.ext.autosummary",
    "sphinx.ext.autodoc.typehints",
    "autoapi.extension",
    "numpydoc",
]

# autodoc
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "private-members": False,
    "special-members": "__init__, __new__",
    "show_inheritance": True,
}

# napoleon


# autosummary
autosummary_generate = True

# autoapi
autoapi_dirs = ["../../fedcal"]
autoapi_type = "python"
autoapi_options = ["members", "show-inheritance", "show-module-summary"]
autoapi_ignore = [
    "/home/uniquemarlin/anaconda3/envs/fedcal/lib/python3.11/site-packages/*",
    "*/__init__.py",
]
autoapi_python_use_implicit_namespaces = True

# autodoc typehints
autodoc_typehints = "description"
always_document_param_types = True
typehints_defaults = "braces"
typehints_use_signature = True
typehints_use_signature_return = True

# numpydoc
numpydoc_xref_param_type = True


templates_path = ["_templates"]
exclude_patterns = []

language = "en"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# -- Options for intersphinx extension ---------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}
