#!/bin/bash
# arguments: material, load, geometry, path from current project directory
# to simulation directory
mat="${1}"; matyaml="${2}"; load="${3}"; geom="${4}"; path="${5}"; n=$((${6}));
cd "${project_dir}/${path:2}"

apptainer run --pwd "/wd" --env OMP_NUM_THREADS=${OMP_NUM_THREADS} -B "${PWD}:/wd, /tmp" "damask-grid.sif" -numerics --load "${load}" --geom "${geom}" --material "${matyaml}" > "slurm_${geom}_${load:0:(-5)}.out"
