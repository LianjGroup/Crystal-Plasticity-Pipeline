WARNING: RE-RUNNING SIMULATIONS DELETE PREVIOUS SIMULATION DIRECTORIES. MOVE 
.HDF5 FILES TO ANOTHER DIRECTORY BEFORE HAND, AND CHECK CONFIGURATION CAREFULLY.

Config file in syntax:

    <Material 1> <load case 1> <load case 2> ...
    <Material 2> <load case 3> <load case 4> ...
    ...

Accept load cases with and without .yaml file extension. Example:
QP1000_DP linear_tensionX.yaml linear_tensionY.yaml tension_relax_cycle

To run DAMASK simulations:

    1.  Make sure that damask-grid.sif is in the working directory. If not, build
        a damask image following https://docs.csc.fi/computing/containers/creating/.
        Use docker://eisenforschung/damask-grid:<version>.
        Note that the current latest version may not be the one used in this
        project, 3.0.0-alpha
    2.  Check and edit config.txt. Make sure that config.txt is in the working
        directory.
    3.  Add materials and load cases to corresponding folder.
    4.  Edit partition and time in pipeline.sh Recommended partition is
        test or medium. Time should be ~ 0.5 hour per simulation
    5.  Open terminal in the working directory and submit job with
        sbatch pipeline.sh
        
Note: the simulations are currently parallel, but post-processings are NOT. To run
simulations with a full node and run postprocessing in a separate interactive shell,
you can run
        $ sbatch pipeline.sh nopost
Then use interactive shell according to
        https://docs.csc.fi/computing/running/interactive-usage/
and directly call python postprocessing file
        $ module load python-data
        $ python3 postprocessing.py -f simulations/<simulation directory>/<result .hdf5 file>
This efficiently uses billing units. Note that this can only be done only after 
the simulations are finished, otherwise an error may occur and damask may be
interrupted.

The following video demonstrate how the team used the pipeline to run simulations, get
automated post-processing results, and perform some visualization.
https://aaltofi-my.sharepoint.com/:v:/g/personal/minh_h_tran_aalto_fi/EbgTLuW1nhtAinwtPAaAjsEBPYronB6eUPGToNtG-bRt0A?nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJPbmVEcml2ZUZvckJ1c2luZXNzIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXciLCJyZWZlcnJhbFZpZXciOiJNeUZpbGVzTGlua0NvcHkifX0&e=l37XIH

