import numpy as np
import pandas as pd

from sklearn.utils import Bunch

from nilearn.connectome import ConnectivityMeasure
from nilearn.input_data import fmriprep_confounds


def fetch_fmriprep_derivative(participant_tsv_path, path_fmriprep_derivative,
                              specifier, space="MNI152NLin2009cAsym"):
    """Fetch fmriprep derivative and return nilearn.dataset.fetch* like output.
    Load functional image, confounds, and participants.tsv only.
    """

    # participants tsv from the main dataset
    if not participant_tsv_path.is_file():
        raise(FileNotFoundError,
              f"Cannot find {participant_tsv_path}")
    if participant_tsv_path.name != "participants.tsv":
        raise(FileNotFoundError,
              f"File {participant_tsv_path} "
              "is not a BIDS participant file.")
    participant_tsv = pd.read_csv(participant_tsv_path,
                                  index_col=["participant_id"],
                                  sep="\t")
    # images and confound files
    subject_dirs = path_fmriprep_derivative.glob("sub-*/")
    func_img_path, confounds_tsv_path, include_subjects = [], [], []
    for subject_dir in subject_dirs:
        subject = subject_dir.name
        cur_func = (subject_dir / "func" /
            f"{subject}_{specifier}_space-{space}_desc-preproc_bold.nii.gz")
        cur_confound = (subject_dir / "func" /
            f"{subject}_{specifier}_desc-confounds_timeseries.tsv")

        if cur_func.is_file() and cur_confound.is_file():
            func_img_path.append(str(cur_func))
            confounds_tsv_path.append(str(cur_confound))
            include_subjects.append(subject)

    return Bunch(func=func_img_path,
                 confounds=confounds_tsv_path,
                 phenotypic=participant_tsv.loc[include_subjects, :]
                 )


def deconfound_connectome_single_strategy(func_img, masker, strategy):
    """Create confound-removed by one strategy connectomes for a dataset.

    Parameters
    ----------
    func_img : List of string
        List of path to functional images

    masker :
        Nilearn masker object

    strategy : Dict
        Dictionary with a strategy name as key and a parameter set as value.
        Pass to `nilearn.input_data.fmriprep_confounds`

    Returns
    -------
    pandas.DataFrame
        Flattened connectome of a whole dataset.
        Index: subjets
        Columns: ROI-ROI pairs
    """
    dataset_connectome = pd.DataFrame()
    strategy_name, parameters = strategy.popitem()
    for img in func_img:
        subject_id = img.split("/")[-1].split("_")[0]

        # remove confounds based on strategy
        if strategy_name == "no_cleaning":
            subject_timeseries = masker.fit_transform(img)

        reduced_confounds, sample_mask = fmriprep_confounds(img, **parameters)

        # scrubbing related issue: subject with too many frames removed
        # should not be included
        if sample_mask is None or len(sample_mask) != 0:
            subject_timeseries = masker.fit_transform(
                img, confounds=reduced_confounds, sample_mask=sample_mask)
            correlation_measure = ConnectivityMeasure(kind='correlation',
                                            vectorize=True,
                                            discard_diagonal=True)
            # save the correlation matrix flatten
            flat_connectome = correlation_measure.fit_transform(
                [subject_timeseries])
            flat_connectome = pd.DataFrame(flat_connectome, index=[subject_id])
            dataset_connectome = pd.concat((dataset_connectome,
                                            flat_connectome))
        else:
            subject_timeseries = None
            dataset_connectome.loc[subject_id, :] = np.nan
    return dataset_connectome
