#!/bin/bash
#SBATCH --job-name=metric_mist
#SBATCH --time=12:00:00
#SBATCH --account=rrg-pbellec
#SBATCH --output=logs/metric.out
#SBATCH --error=logs/metric.err
#SBATCH --cpus-per-task=4
#SBATCH --mem=4G 
#SBATCH --array=0-9


INPUTS="/home/${USER}/projects/def-pbellec/${USER}/fmriprep-denoise-benchmark/inputs/dataset-ds000228.tar.gz"
OUTPUT="/home/${USER}/scratch/fmriprep-denoise-benchmark"
DIMENSIONS=(7 12 20 36 64 122 197 325 444 ROI)

source /home/${USER}/.virtualenvs/fmriprep-denoise-benchmark/bin/activate

cd /home/${USER}/projects/def-pbellec/${USER}/fmriprep-denoise-benchmark/

python ./fmriprep_denoise/process_denoise_metrics.py ${INPUTS} ${OUTPUT} --atlas mist --dimension ${DIMENSIONS[${SLURM_ARRAY_TASK_ID}]}
 
