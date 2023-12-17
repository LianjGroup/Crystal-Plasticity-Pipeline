#!/bin/bash -l
# created: Feb 14, 2020 2:22 PM
# author: minhhoan
#SBATCH --job-name=DAMASK_array
#SBATCH --account=project_2008630
#SBATCH --partition=medium
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=32
#SBATCH --hint=multithread
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=tran.minhhoang@aalto.fi
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
echo '=== Reading config.txt ==='
module load python-data
# Compatibility reasons
dos2unix config.txt
# Read config file
file="config.txt"
# Record which material and load case to run
declare -a materials
declare -a loadcases
declare -a geometries
declare -a matyamls
N=0
while IFS= read -r line
do
    if [[ ${line:0:1} != "#" ]]
    then
        IFS=' ' read -a temp <<< "$line"
        for loadcase in "${temp[@]:1}"
        do
            # Save a combination of load case and material onto arrays
            N=$((N+1))
            materials+=("${temp[0]}")
            # Make sure load case name works whether if .yaml extension is there
            if [ ${loadcase:(-5)} != ".yaml" ]
            then
                loadcase=("${loadcase}.yaml")
            fi
            loadcases+=("${loadcase}")
            # Find the geometry .vti file in material directory
            dir="./materials/${temp[0]}/"
            file="$(find $dir -type f -name '*.vti')"
            geometry=("${file#"$dir"}")
            geometries+=("${geometry}")
            # Find the material .yaml file in material directory, make sure it
            # is not numerics.yaml
            file="$(find $dir -type f -name '*.yaml' ! -name 'numerics.yaml')"
            matyaml=("${file#"$dir"}")
            matyamls+=("${matyaml}")
            # Create folders in simulations and copy needed files
            rm -rf "./simulations/${temp[0]}_${loadcase:0:(-5)}"
            mkdir "./simulations/${temp[0]}_${loadcase:0:(-5)}"
            cp "./materials/${temp[0]}/${matyaml}" "./simulations/${temp[0]}_${loadcase:0:(-5)}/${matyaml}"
            cp "./materials/${temp[0]}/numerics.yaml" "./simulations/${temp[0]}_${loadcase:0:(-5)}/numerics.yaml"
            cp "./materials/${temp[0]}/${geometry}" "./simulations/${temp[0]}_${loadcase:0:(-5)}/${geometry}"
            cp "./loadcases/${loadcase}" "./simulations/${temp[0]}_${loadcase:0:(-5)}/${loadcase}"
            cp "./damask-grid.sif" "./simulations/${temp[0]}_${loadcase:0:(-5)}/damask-grid.sif"
        done
    fi
done < $file
export project_dir=$PWD
echo "=== Submitting ${N} jobs ==="
for ((n=0; n<$N; n++))
do
    mat=("${materials[n]}")
    matyaml=("${matyamls[n]}")
    load=("${loadcases[n]}")
    geom=("${geometries[n]}")
    path=("./simulations/${mat}_${load:0:(-5)}")
    echo "=== Running simulation for ${mat} and load ${load} ==="
    sh pipeline_internal.sh $mat $matyaml $load $geom $path $n &
done
wait
if [[ $1 != 'nopost' ]]
then
    echo "=== Finished ${N} simulations, runnning post-processing scripts ==="
    for ((n=0; n<$N; n++))
    do
        mat=("${materials[n]}")
        matyaml=("${matyamls[n]}")
        load=("${loadcases[n]}")
        geom=("${geometries[n]}")
        path=("./simulations/${mat}_${load:0:(-5)}")
        python3 postprocessing.py -f "${path}/${geom::(-4)}_${load::(-5)}_${matyaml::(-5)}.hdf5" > "${path}/py_postprocessing.out" 2>&1 &
    done
    wait
    echo "Finished post-processing"
fi
echo "Finished job"
