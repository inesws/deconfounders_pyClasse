# -*- coding: utf-8 -*-

import sys
sys.path.insert(0,'path_to_neurocombat_modified')

from sklearn.utils.validation import check_X_y, check_array, check_is_fitted
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
import neurocombat_correct_fun_with_modmean
#neurocombat_transform: dat,covars, batch_col, cat_cols, num_cols,estimates
from neurocombat_correct_fun_with_modmean import neuroCombat_estimate, neuroCombat_transform
from sklearn.preprocessing import StandardScaler



"""Changes: I add the reference option to both LR and StandardScalerDict in order to be able to perform a smooth pipeline where the refeence batch can be chosen in all fuunction to serve as data to fit the estimations. I add the option of outputting the corrected data or the dictionary data + covariates to the regression class"""

# Standard Scaler to use with dictionares {data, covariates}

class StandardScalerDict(BaseEstimator, TransformerMixin):
  def __init__(self,ref_batch,std_data,std_cov,output_dict):
    self.std_data=std_data
    self.std_cov=std_cov
    self.output_dict=output_dict
    self.ref_batch=ref_batch

  def check_data(self,X):
    if type(X) is not dict:
      data=X.copy()
      X={}
      X["data"]=data
      print(X)
      print('Data was not type dictonary. The output will be set to numpy() data only')
      self.output_dict=False
      self.std_cov=None

    return X

  def fit(self, X, y=None):

    X=self.check_data(X)
    print('SS: Shape of the whole dataset {}'.format(X['data'].shape))

    batch_col=['batch']
    if self.ref_batch is not None:
      X_fit={}
      print('SS: Selecting only the reference data')
      ref_batch_index=X["covariates"][X["covariates"][batch_col[0]]==self.ref_batch].index
      X_fit["data"]=X["data"][ref_batch_index,:].copy()

      print('SS: Shape of reference dataset {}'.format(X_fit['data'].shape))

      if self.std_data==True:
        self.scaler_data_ = StandardScaler().fit(X_fit["data"])
      if self.std_cov==True:
        X_fit["covariates"]=X["covariates"].iloc[ref_batch_index,:].copy()
        self.scaler_cov_ = StandardScaler().fit(X_fit["covariates"])

    else:
      if self.std_data==True:
        self.scaler_data_ = StandardScaler().fit(X["data"])
      if self.std_cov==True:
        self.scaler_cov_ = StandardScaler().fit(X["covariates"])

    return self

  def transform(self,X):

    X=self.check_data(X)

    print('SS: Transforming dataset shape {}'.format(X['data'].shape))

    if self.std_data==True:
      X_std= self.scaler_data_.transform(X["data"])
    else:
      X_std=X["data"]

    if self.std_cov==True:
      COV_std= self.scaler_cov_.transform(X["covariates"])
    elif self.std_cov==False:
      COV_std= X["covariates"]

    if self.output_dict==True:
      output={"data":X_std, "covariates": COV_std}
    else:
      output=X_std

    return output

#ADAPTED TO REFERENCE STRATEGY

#it applies neurocombat to specific brain features extracted from images
#feat_index is a dic with the name of the morphological features and the corresponding id columns


# Limitations:
# Not compatible with (R/G)SearchCV from keras
# Cannot choose not to harmonize validaiton set in the (R/G)SearchCV
# Cannot choose a cv method
# It harmonizes globals like TIV which are included in covariates if feat_of_no_interest is set BUT
# only using fit_transform method. Otherwise it corrects 2xtimes the TIV

class ComBatHarmonization(BaseEstimator, TransformerMixin):
  """
  Multi-site Harmonization compatible with sklearn pipeline

  Limitations:
  -Not compatible with sklearn Random/Grid search
  -covariates are being changed in place and it only works with method fit_transform()
  not fit() method


  """
  def __init__(self, cv_method, ref_batch, regression_fit, feat_detail, feat_of_no_interest):
    """ Creates a new ComBat """

    # Attribute that defines the CV method
    # Dictionary: cv_strategy or holdout_strategy
    self.cv_method=cv_method
    self.ref_batch=ref_batch
    self.regression_fit=regression_fit
    self.feat_detail=feat_detail
    self.feat_of_no_interest=feat_of_no_interest


  def extract_data(self,X):
    """
    Function is called to extract data since X.
    X dictonary containes the data (samples x features) and
    covariates (samples x covariates) .

    """
    global X_data, covars_fit_sorted

    if type(X) is dict:
      X_data=X['data'].copy()
      covars_fit_sorted=X['covariates']

    elif self.cv_method: #This is wrong -> Correct it! The cv_method could contain 'holdout'?
      X_data=X.copy()
      index=list(X_data.index.values)
      X_data=X_data.to_numpy()
      covars_fit_sorted=self.cv_method['covariates'].iloc[index,:]

    return X_data, covars_fit_sorted

  def check_feat_no_int_harmonization(self,X, covariates, batch=None):

    if self.feat_of_no_interest: #If there are cov. to harmonize?
      if hasattr(self, 'n_features_'): # If was already fitted
        print('Applying estimations')
        cov_id=self.feat_of_no_interest['covariate']['id']
        cov_to_harm=covars_fit_sorted[[cov_id]].to_numpy()
        feat_concat=self.feat_of_no_interest['feat_concat']
        X_new=np.concatenate((X[:,feat_concat].copy(),cov_to_harm),axis=1)
        categorical_cols=self.feat_of_no_interest['covariate']['categorical']
        continuous_cols=self.feat_of_no_interest['covariate']['continuous']
        batch_col=['batch']
        X_feat_harm=neuroCombat_transform(dat=np.transpose(X_new), covars=covariates, batch_col=batch_col,
                                          cat_cols=categorical_cols, num_cols=continuous_cols,
                                          estimates=self.combat_estimations_[cov_id])["data"]
        cov_harm=np.transpose(X_feat_harm)[:,-cov_to_harm.shape[1]:]
        covariates.loc[:,(cov_id)]=cov_harm # Covariates are changed 'inplace'

      else: # Not fitted
        print('Fitting the regressor')
        self.combat_estimations_={} # initilize
        cov_id=self.feat_of_no_interest['covariate']['id'] # extract name of covar
        cov_to_harm=covars_fit_sorted[[cov_id]].to_numpy().copy()
        feat_concat=self.feat_of_no_interest['feat_concat'] # extract id features to harmonize
        X_new=np.concatenate((X[:,feat_concat].copy(),cov_to_harm),axis=1) # concat
        categorical_cols=self.feat_of_no_interest['covariate']['categorical']
        continuous_cols=self.feat_of_no_interest['covariate']['continuous']
        batch_col=['batch']
        if self.ref_batch is not None: #I CHANGED THIS CONDITION BC self.ref_batch: DIDN'T INCLUDE THE CASES WHERE REF_BATCH=0
          cov_feat_combat=neuroCombat_estimate(dat=np.transpose(X_new),covars=covariates,
                                               batch_col=batch_col, categorical_cols=categorical_cols,
                                               continuous_cols=continuous_cols, ref_batch=self.ref_batch)
          self.combat_estimations_[cov_id]=cov_feat_combat["estimates"]

        else:
          cov_feat_combat=neuroCombat_estimate(dat=np.transpose(X_new),covars=covariates,
                                               batch_col=batch_col, categorical_cols=categorical_cols,
                                               continuous_cols=continuous_cols)
          self.combat_estimations_[cov_id]=cov_feat_combat["estimates"]

        #X_feat_harm=cov_feat_combat["data"]
        #cov_harm=np.transpose(X_feat_harm)[:,-cov_to_harm.shape[1]:]

    return X

  def check_feat_harmonization(self,X,covariates, batch=None):
    output=[]
    if self.feat_detail:
      if hasattr(self, 'n_features_'): #if it was fitted
        ('it was fitted, it enter in transform')
        X_harm=[]
        for key_1,val_1 in self.feat_detail.items():
          id=self.feat_detail[key_1]['id']
          X_feat=X[:,id].copy()
          categorical_cols=self.feat_detail[key_1]['categorical']
          continuous_cols=self.feat_detail[key_1]['continuous']
          batch_col=['batch']
          #dat,covars, batch_col, cat_cols, num_cols,estimates
          X_feat_harm=neuroCombat_transform(dat=np.transpose(X_feat), covars=covariates, batch_col=batch_col,
                                            cat_cols=categorical_cols,num_cols=continuous_cols,
                                            estimates=self.combat_estimations_[key_1])["data"]
          X_harm.append(np.transpose(X_feat_harm)) #list with (samples x feat_i) with final len = feat_of_int
        output=np.concatenate(X_harm, axis=1)  # harm data (samples x feat_all)

      else: #if was not fitted
        batch_col=['batch']
        self.combat_estimations_={}
        for key_1,val_1 in self.feat_detail.items():
          id=self.feat_detail[key_1]['id']
          X_feat=X[:,id].copy()
          categorical_cols=self.feat_detail[key_1]['categorical']
          continuous_cols=self.feat_detail[key_1]['continuous']
          if self.ref_batch is not None:
            combat=neuroCombat_estimate(dat=np.transpose(X_feat),covars=covariates,
                                        batch_col=batch_col,
                                        categorical_cols=categorical_cols,
                                        continuous_cols=continuous_cols, ref_batch=self.ref_batch)
            self.combat_estimations_[key_1]=combat["estimates"]


          else:
            combat=neuroCombat_estimate(dat=np.transpose(X_feat),covars=covariates,
                                        batch_col=batch_col,
                                        categorical_cols=categorical_cols,
                                        continuous_cols=continuous_cols)
            self.combat_estimations_[key_1]=combat["estimates"]

    return output # If it was already fitted, returns harm data, otherwise empty


  def fit(self, X, y=None):

    X, covars_fit_sorted=self.extract_data(X)
    X = check_array(X, accept_sparse=True)

    if self.feat_of_no_interest: # To harmonize TIV or other globals in covariates
      ouput=self.check_feat_no_int_harmonization(X, covars_fit_sorted)

    if self.feat_detail:
      output=self.check_feat_harmonization(X,covars_fit_sorted)

    self.n_features_ = X.shape[1] # For the check_is_fitted method

    return self

  def transform(self, X):

    # Check is fit had been called
    check_is_fitted(self)

    X, covars_fit_sorted=self.extract_data(X)
    #batch_trans_sorted=covars_fit_sorted[['batch']] # We only need the batch

    X = check_array(X, accept_sparse=True)

    if self.feat_of_no_interest:
      output=self.check_feat_no_int_harmonization(X, covars_fit_sorted)
      #The output should be X -> the input data because the covariates are changed inplace

    if self.feat_detail:
      output=self.check_feat_harmonization(X, covars_fit_sorted)
      # The ouput should be the X_harm

    if self.regression_fit==1:
      output={'data': output, 'covariates': covars_fit_sorted}

    return output

from sklearn.utils.validation import check_X_y, check_array, check_is_fitted
import statsmodels.api as sm
from scipy import stats

#GIVE COVARIATES IN INPUT WITH DICTIONARY
"""
X_feat are not standardize here, why? because we fit the regression for
feature type separatly: Ycort= Bage + B_sex / Y_vol= B_age + B_sex + B_TIV
But we standardize before and after when defining the pipeline: is it necessary before?

To do: Include diagnosis in covariates to estimate Betas but don't remove it
Include the partial correlation option for it?
"""
class BiocovariatesRegression(BaseEstimator, TransformerMixin):
  def __init__(self, ref_batch, cv_method, feat_detail, output_dict):
    self.feat_detail=feat_detail
    self.cv_method=cv_method
    self.ref_batch=ref_batch
    self.output_dict=output_dict

  def extract_data(self,X):
    """
    Function is called to extract data since X.
    X dictonary containes the data (samples x features) and
    covariates (samples x covariates).
    """
    global X_data, covars_fit_sorted

    if type(X) is dict:
      X_data=X['data'].copy()
      covars_fit_sorted=X['covariates']

    elif self.cv_method:
      X_data=X.copy()
      index=list(X_data.index.values)
      X_data=X_data.to_numpy()
      covars_fit_sorted=self.cv_method['covariates'].iloc[index,:]

    return X_data, covars_fit_sorted


  def fit(self,X, y=None):

    X, covars_fit_sorted=self.extract_data(X)
    X = check_array(X, accept_sparse=True)

    batch_col=['batch']
    print('LR: Shape of the whole dataset {}'.format(X.shape))

    # In case self.ref_batch exists we want to fit the LR only
    # on the reference batch

    if self.ref_batch is not None:

      ref_batch_index=covars_fit_sorted[covars_fit_sorted[batch_col[0]]==self.ref_batch].index
      X_ref=X[ref_batch_index,:].copy()
      covars_fit_sorted_ref=covars_fit_sorted[covars_fit_sorted[batch_col[0]]==self.ref_batch].copy()

      print('LR:Fitting on reference dataset of shape {}'.format(X_ref.shape))

      self.scaler_ = StandardScaler().fit(X_ref)
      #X=self.scaler_.transform(X)

      self.beta_estimations_={}
      self.mod_mean_={}
      for key_1,val_1 in self.feat_detail.items():
        print(key_1)
        id=self.feat_detail[key_1]['id'] #cortical/volumes etc
        X_feat=X_ref[:,id].copy()
        categorical_cols=self.feat_detail[key_1]['categorical']
        continuous_cols=self.feat_detail[key_1]['continuous']
        biocov=categorical_cols + continuous_cols
        C= sm.add_constant(covars_fit_sorted_ref[biocov]) #If we want to add a constant to our model
        est = sm.OLS(X_feat,C)
        estimates=est.fit()
        self.beta_estimations_[key_1] = estimates.params.to_numpy() #.loc[biocov]
        self.mod_mean_[key_1]=np.dot(C.to_numpy(), self.beta_estimations_[key_1])

    else:

      self.scaler_ = StandardScaler().fit(X)
      #X=self.scaler_.transform(X)

      self.beta_estimations_={}
      self.mod_mean_={}

      for key_1,val_1 in self.feat_detail.items():
        print(key_1)
        id=self.feat_detail[key_1]['id'] #cortical/volumes etc
        X_feat=X[:,id].copy()
        categorical_cols=self.feat_detail[key_1]['categorical']
        continuous_cols=self.feat_detail[key_1]['continuous']
        biocov=categorical_cols + continuous_cols
        C= sm.add_constant(covars_fit_sorted[biocov]) #If we want to add a constant to our model
        est = sm.OLS(X_feat,C)
        estimates=est.fit()
        self.beta_estimations_[key_1] = estimates.params.to_numpy() #.loc[biocov]
        self.mod_mean_[key_1]=np.dot(C.to_numpy(), self.beta_estimations_[key_1])

    return self

  def transform(self, X):
    # Check is fit had been called
    check_is_fitted(self)
    X, covars_fit_sorted=self.extract_data(X)
    X = check_array(X, accept_sparse=True)

    print('LR: Transforming dataset shape {}'.format(X.shape))
    #X=self.scaler_.transform(X)

    X_corr_partial=[]
    for key_1,val_1 in self.feat_detail.items():
      id=self.feat_detail[key_1]['id'] #cortical/volumes etc
      X_feat=X[:,id].copy()
      categorical_cols=self.feat_detail[key_1]['categorical']
      continuous_cols=self.feat_detail[key_1]['continuous']
      biocov=categorical_cols + continuous_cols
      C= sm.add_constant(covars_fit_sorted[biocov], has_constant='add') #I need a way to have covariates here for either train or test
      X_corr_partial.append(X_feat - np.dot(C.to_numpy(),self.beta_estimations_[key_1]))
    X_corr=np.concatenate(X_corr_partial, axis=1)

    if self.output_dict==True:
      output={"data":X_corr, "covariates": covars_fit_sorted}
    else:
      output=X_corr

    return output
