

# Biological and Non-Biological neuroimaging confounding effects removal

# deconfounders_pyClasse
Deconfounders python classe is a repository with functions to correct neuroimaging data from non-biological and biological confounding variables integrated in a python classe compatible with sklearn Pipelines and fit/transform methods.
Includes:
# neurocombat_pyClasse
neurocombat function (Fortin, J. P. et al.) implementation in a python classe in order to be compatible with python fit/transform methods and sklearn Pipelines.

update submodule changes
```python
git submodule update --remote
```
```python
git add neurocombat_pyClasse
git commit -m "Updated neurocombatPyclasse submodule to the latest version"
git push origin main
```
When cloning this repository do:

```python
git clone https://github.com/yourusername/deconfounders_pyClasse.git
cd deconfoundersPyClasse
git submodule init
git submodule update
```

# linear_regression_pyClasse
linear regression to model biological covariates and remove them from neuroimaging data, compatible with python fit/transform methods and sklearn Pipelines.

# References for development of this work:
- Original ComBat model: Johnson, W. E., Li, C. & Rabinovic, A. Adjusting batch effects in microarray expression data using empirical Bayes methods. Biostatistics 8, 118–127 (2007).
- First ComBat adaptation to neuroimaging : Fortin, J. et al. NeuroImage Harmonization of multi-site diffusion tensor imaging data. Neuroimage 161, 149–170 (2017).
- First ComBat adaptation for CT: Fortin, J. P. et al. Harmonization of cortical thickness measurements across scanners and sites. Neuroimage 167, 104–120 (2018).
- Using a standard/reference batch/site to estimate ComBat and harmonize data (M-ComBat): Stein, C. K. et al. Removing batch effects from purified plasma cell gene expression microarrays with modified ComBat. BMC Bioinformatics 16, 1–9 (2015).
- (Linear) Regressing-out biological covariates which are considered confounding effects in neuroimaging data: Snoek, L., Miletić, S. & Scholte, H. S. How to control for confounds in decoding analyses of neuroimaging data. Neuroimage 184, 741–760 (2019).

# Cite this repository and respective work: 
- ComBat for Machine learning analysis and internal validation frameworks: I. W. Sampaio et al.: "Comparison of Multi-site Neuroimaging Data Harmonization Techniques for Machine Learning Applications," IEEE EUROCON 2023 - 20th International Conference on Smart Technologies, Torino, Italy, 2023, pp. 307-312, doi: 10.1109/EUROCON56442.2023.10198911.
