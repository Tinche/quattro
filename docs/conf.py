# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from importlib import metadata

project = "quattro"
copyright = "2025, Tin Tvrtkovic"
author = "Tin Tvrtkovic"

# The full version, including alpha/beta/rc tags.
release = metadata.version("quattro")
# The short X.Y version.
version = release.rsplit(".", 1)[0]

if "dev" in release:
    release = version = "UNRELEASED"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autodoc", "myst_parser", "sphinx.ext.napoleon"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_theme_options = {
    "light_css_variables": {
        "font-stack": "Inter,sans-serif",
        "font-stack--monospace": "'Ubuntu Mono', monospace",
        "code-font-size": "90%",
        "color-highlight-on-target": "transparent",
    },
    "dark_css_variables": {"color-highlight-on-target": "transparent"},
}

myst_heading_anchors = 3
myst_enable_extensions = ["attrs_block"]
autodoc_typehints = "description"
autoclass_content = "both"
