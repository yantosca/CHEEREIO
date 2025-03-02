#!/bin/bash

# This script sets up the global control run directory. Users never run this directly.

source setup_ensemble_prelims.sh #get the relevant variables.

##=======================================================================
##  Set up control (no assimilation) run directory
##=======================================================================

printf "${thickline}CHEERIO CONTROL (no assimilation) RUN DIRECTORY CREATION${thickline}"

if [ "${DO_CONTROL_WITHIN_ENSEMBLE_RUNS}" = false ]; then 

    cd ${MY_PATH}/${RUN_NAME}

    ### Define the run name
    control_name="${RUN_NAME}_Control"

    ### Make the directory
    runDir="control_run"
    mkdir -p ${runDir}

    ### Copy and point to the necessary data
    cp -r ${RUN_TEMPLATE}/*  ${runDir}
    cp -RLv ${ASSIM_PATH}/templates/ensemble_run.template ${runDir}
    cd $runDir

    ### Link to GEOS-Chem executable instead of having a copy in each rundir
    rm -rf gcclassic
    ln -s ../${RUN_TEMPLATE}/gcclassic .
    # Link to restart file
    ln -s $RESTART_FILE GEOSChem.Restart.${CONTROL_START}_0000z.nc4

    #Switch HEMCO_Config to base/nature one.
    rm HEMCO_Config.rc #This one has updated scaling factors.
    mv HEMCO_Config_SPINUP_NATURE_TEMPLATE.rc HEMCO_Config.rc #This one only updates a few settings.
    if [ "${ENS_SPINUP_FROM_BC_RESTART}" = true ]; then
        sed -i -e "s|SpeciesRst|SpeciesBC|g" HEMCO_Config.rc #If we are spinning up from BCs, handle this
    fi

    #CD to run core scripts
    cd ${ASSIM_PATH}/core

    #update history collections for production-style run (not spinups)
    source activate $(jq -r ".CondaEnv" ../ens_config.json)
    python update_history.py "SETCONTROL"
    conda deactivate

    bash change_hemcodiag_freq.sh "control" #update hemco diagnostics frequency.

    #Back to rundir
    cd ${MY_PATH}/${RUN_NAME}/${runDir}

    ### Update settings in input.geos
    sed -i -e "s:{DATE1}:${CONTROL_START}:g" \
           -e "s:{DATE2}:${CONTROL_END}:g" \
           -e "s:{TIME1}:000000:g" \
           -e "s:{TIME2}:000000:g" input.geos

    ### Create run script from template
    sed -e "s:namename:${control_name}:g" \
        -e "s:{NumCores}:${NumCtrlCores}:g" \
        -e "s:{Partition}:${Partition}:g" \
        -e "s:{Memory}:${EnsCtrlSpinupMemory}:g" \
        -e "s:{ASSIM}:${ASSIM_PATH}:g" \
        -e "s:{SpinupWallTime}:${ControlWallTime}:g" ensemble_run.template > ${control_name}.run #change
    chmod 755 ${control_name}.run
    rm -f ensemble_run.template

    ### Print diagnostics
    printf "${thinline}CREATED: ${runDir}${thinline}"

    ### Navigate back to top-level directory
    cd ${MY_PATH}/${RUN_NAME}

else

    printf "ens_config indicates you are running the control run within the ensemble runs directory.\n"
    printf "In your case, the control directory will be created in the SetupEnsembleRuns phase.\n"
    printf "See the documentation for more information.\n"
    printf "${thinline}SKIPPED CONTROL RUN DIRECTORY CREATION${thinline}"

fi #DO_CONTROL_WITHIN_ENSEMBLE_RUNS
