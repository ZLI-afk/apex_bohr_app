from pathlib import Path
import os
import shutil
import json
from monty.serialization import loadfn
from apex.submit import submit_workflow
from vasp_model import VaspModel


def get_global_config(opts: VaspModel):
    global_config = {
        "dflow_config": {
            "host": opts.dflow_argo_api_server,
            "k8s_api_server": opts.dflow_k8s_api_server,
            "token": opts.dflow_access_token,
            "dflow_labels": opts.dflow_labels.get_value()
        },
        "dflow_s3_config": {
            "endpoint": opts.dflow_storage_endpoint,
            "repo_key": opts.dflow_storage_repository
        },
        "bohrium_config":{
            "username": opts.bohrium_username,
            "ticket": opts.bohrium_ticket,
            "projectId": opts.bohrium_project_id,
            "project_id": opts.bohrium_project_id
        },
        "machine": {
                "batch_type": "Bohrium",
                "context_type": "Bohrium",
                "remote_profile": {
                    "email": opts.bohrium_username,
                    "password": opts.bohrium_ticket,
                    "program_id": int(opts.bohrium_project_id),
                    "input_data": {
                        "job_type": opts.bohrium_job_type,
                        "platform": opts.bohrium_platform,
                        "scass_type": opts.scass_type
                    },
                },
            },
        "apex_image_name": opts.apex_image_name,
        "run_image_name": opts.vasp_image_name,
        "group_size": opts.group_size,
        "pool_size": opts.pool_size,
        "run_command": opts.vasp_run_command,
        "is_bohrium_dflow": True,
    }
    json.dump(global_config, open('global_config_tmp.json', 'w'), indent=2)
    global_config = loadfn('global_config_tmp.json')
    #os.remove('global_config_tmp.json')
    return global_config


def get_interaction(opts: VaspModel):
    interaction = {
        "type": "vasp",
        "incar": Path(opts.incar).name,
        "potcar_prefix": ".",
        "potcars": opts.potcar_map
    }
    return interaction


def get_relaxation(opts: VaspModel):
    relaxation = {}
    relaxation["cal_setting"] = {
        "kgamma": opts.kgamma,
        "relax_pos": opts.relax_pos,
        "relax_shape": opts.relax_shape,
        "relax_vol": opts.relax_vol,
    }
    if opts.ediff:
        relaxation["cal_setting"]["ediff"] = opts.ediff
    if opts.ediffg:
        relaxation["cal_setting"]["ediffg"] = opts.ediffg
    if opts.encut:
        relaxation["cal_setting"]["encut"] = opts.encut
    if opts.kspacing:
        relaxation["cal_setting"]["kspacing"] = opts.kspacing
    return relaxation


def get_properties(opts: VaspModel):
    properties = []

    #EOS
    if opts.select_eos:
        eos_params = {
            "type": "eos",
            "skip": False,
            "vol_start": opts.vol_start,
            "vol_end": opts.vol_end,
            "vol_step": opts.vol_step,
            "vol_abs": opts.vol_abs,
            "cal_type": opts.eos_cal_type
        }
        if opts.custom_eos_calc:
            eos_params["cal_setting"] = {
                "kgamma": opts.eos_kgamma,
                "relax_pos": opts.eos_relax_pos,
                "relax_shape": opts.eos_relax_shape,
                "relax_vol": opts.eos_relax_vol,
            }
            if opts.eos_ediff:
                eos_params["cal_setting"]["ediff"] = opts.eos_ediff
            if opts.eos_ediffg:
                eos_params["cal_setting"]["ediffg"] = opts.eos_ediffg
            if opts.eos_encut:
                eos_params["cal_setting"]["encut"] = opts.eos_encut
            if opts.eos_kspacing:
                eos_params["cal_setting"]["kspacing"] = opts.eos_kspacing

            if opts.eos_incar:
                with open('INCAR.eos', 'w') as f:
                    f.write(opts.eos_incar)
                eos_params["cal_setting"]["input_prop"] = "INCAR.eos"
        properties.append(eos_params)

    # Elasitc
    if opts.select_elastic:
        elastic_params = {
            "type": "elastic",
            "skip": False,
            "norm_deform": opts.norm_deform,
            "shear_deform": opts.shear_deform,
            "cal_type": opts.elastic_cal_type,
            "conventional": opts.conventional,
            "ieee": opts.ieee,
            "modulus_type": opts.modulus_type
        }
        if opts.custom_elastic_calc:
            elastic_params["cal_setting"] = {
                "kgamma": opts.eos_kgamma,
                "relax_pos": opts.eos_relax_pos,
                "relax_shape": opts.eos_relax_shape,
                "relax_vol": opts.eos_relax_vol,
            }
            if opts.elastic_ediff:
                elastic_params["cal_setting"]["ediff"] = opts.elastic_ediff
            if opts.elastic_ediffg:
                elastic_params["cal_setting"]["ediffg"] = opts.elastic_ediffg
            if opts.elastic_encut:
                elastic_params["cal_setting"]["encut"] = opts.elastic_encut
            if opts.elastic_kspacing:
                elastic_params["cal_setting"]["kspacing"] = opts.elastic_kspacing
            
            if opts.elastic_incar:
                with open('INCAR.elastic', 'w') as f:
                    f.write(opts.elastic_incar)
                elastic_params["cal_setting"]["input_prop"] = "INCAR.elastic"
        properties.append(elastic_params)
    
    # Surface
    if opts.select_surface:
        surface_params = {
            "type": "surface",
            "skip": False,
            "max_miller": opts.max_miller,
            "min_slab_size": opts.min_slab_size,
            "min_vacuum_size": opts.min_vacuum_size,
            "pert_xz": opts.pert_xz,
            "cal_type": opts.surface_cal_type,
        }
        if opts.custom_surface_calc:
            surface_params["cal_setting"] = {
                "kgamma": opts.surface_kgamma,
                "relax_pos": opts.surface_relax_pos,
                "relax_shape": opts.surface_relax_shape,
                "relax_vol": opts.surface_relax_vol,
            }
            if opts.surface_ediff:
                surface_params["cal_setting"]["ediff"] = opts.surface_ediff
            if opts.surface_ediffg:
                surface_params["cal_setting"]["ediffg"] = opts.surface_ediffg
            if opts.surface_encut:
                surface_params["cal_setting"]["encut"] = opts.surface_encut
            if opts.surface_kspacing:
                surface_params["cal_setting"]["kspacing"] = opts.surface_kspacing
            
            if opts.surface_incar:
                with open('INCAR.surface', 'w') as f:
                    f.write(opts.surface_incar)
                surface_params["cal_setting"]["input_prop"] = "INCAR.surface"
        properties.append(surface_params)

    # Interstitial
    if opts.select_interstitial:
        interstitial_params = {
            "type": "interstitial",
            "skip": False,
            "supercell_size": opts.interstitial_supercell_size,
            "insert_ele": opts.insert_ele,
            "cal_type": opts.interstitial_cal_type,
        }
        if opts.custom_interstitial_calc:
            interstitial_params["cal_setting"] = {
                "kgamma": opts.interstitial_kgamma,
                "relax_pos": opts.interstitial_relax_pos,
                "relax_shape": opts.interstitial_relax_shape,
                "relax_vol": opts.interstitial_relax_vol,
            }
            if opts.interstitial_ediff:
                interstitial_params["cal_setting"]["ediff"] = opts.interstitial_ediff
            if opts.interstitial_ediffg:
                interstitial_params["cal_setting"]["ediffg"] = opts.interstitial_ediffg
            if opts.interstitial_encut:
                interstitial_params["cal_setting"]["encut"] = opts.interstitial_encut
            if opts.interstitial_kspacing:
                interstitial_params["cal_setting"]["kspacing"] = opts.interstitial_kspacing
            
            if opts.interstitial_incar:
                with open('INCAR.interstitial', 'w') as f:
                    f.write(opts.interstitial_incar)
                interstitial_params["cal_setting"]["input_prop"] = "INCAR.interstitial"
        properties.append(interstitial_params)

    # Vacancy
    if opts.select_vacancy:
        vacancy_params = {
            "type": "vacancy",
            "skip": False,
            "supercell_size": opts.vacancy_supercell_size,
            "cal_type": opts.vacancy_cal_type,
        }
        if opts.custom_vacancy_calc:
            vacancy_params["cal_setting"] = {
                "kgamma": opts.vacancy_kgamma,
                "relax_pos": opts.vacancy_relax_pos,
                "relax_shape": opts.vacancy_relax_shape,
                "relax_vol": opts.vacancy_relax_vol,
            }
            if opts.vacancy_ediff:
                vacancy_params["cal_setting"]["ediff"] = opts.vacancy_ediff
            if opts.vacancy_ediffg:
                vacancy_params["cal_setting"]["ediffg"] = opts.vacancy_ediffg
            if opts.vacancy_encut:
                vacancy_params["cal_setting"]["encut"] = opts.vacancy_encut
            if opts.vacancy_kspacing:
                vacancy_params["cal_setting"]["kspacing"] = opts.vacancy_kspacing
            
            if opts.vacancy_incar:
                with open('INCAR.vacancy', 'w') as f:
                    f.write(opts.vacancy_incar)
                vacancy_params["cal_setting"]["input_prop"] = "INCAR.vacancy"  
        properties.append(vacancy_params)
    
    # Vacancy
    if opts.select_gamma:
        gamma_params = {
            "type": "gamma",
            "skip": False,
            "plane_miller": opts.plane_miller,
            "slip_direction": opts.slip_direction,
            "slip_length": opts.slip_length,
            "plane_shift": opts.plane_shift,
            "n_steps": opts.gamma_n_steps,
            "supercell_size": opts.gamma_supercell_size,
            "vacuum_size": opts.gamma_vacuum_size,
            "add_fix": [
                "true" if opts.add_fix_x else "false", 
                "true" if opts.add_fix_y else "false", 
                "true" if opts.add_fix_z else "false"
                ],
            "cal_type": opts.gamma_cal_type,
        }
        if opts.custom_gamma_calc:
            gamma_params["cal_setting"] = {
                "kgamma": opts.gamma_kgamma,
                "relax_pos": opts.gamma_relax_pos,
                "relax_shape": opts.gamma_relax_shape,
                "relax_vol": opts.gamma_relax_vol,
            }
            if opts.gamma_ediff:
                gamma_params["cal_setting"]["ediff"] = opts.gamma_ediff
            if opts.gamma_ediffg:
                gamma_params["cal_setting"]["ediffg"] = opts.gamma_ediffg
            if opts.gamma_encut:
                gamma_params["cal_setting"]["encut"] = opts.gamma_encut
            if opts.gamma_kspacing:
                gamma_params["cal_setting"]["kspacing"] = opts.gamma_kspacing
            
            if opts.gamma_incar:
                with open('INCAR.gamma', 'w') as f:
                    f.write(opts.gamma_incar)
                gamma_params["cal_setting"]["input_prop"] = "INCAR.gamma"
        properties.append(gamma_params)
        
    if opts.select_phonon:
        phonon_params = {
            "type": "phonon",
            "skip": False,
            "primitive_cell": opts.primitive_cell,
            "approach": opts.approach,
            "supercell_size": opts.phonon_supercell_size,
            "seekpath_from_original": opts.seekpath_from_original,
            "BAND": opts.band,
            "BAND_LABELS": opts.band_labels,
            "MESH": opts.mesh,
            "PRIMITIVE_AXES": opts.primitive_axes,
            "BAND_POINTS": opts.band_points,
            "BAND_CONNECTION": opts.band_connection,
            "cal_setting": {}
        }
        if opts.phonon_incar:
            with open('INCAR.phonon', 'w') as f:
                f.write(opts.phonon_incar)
            phonon_params["cal_setting"]["input_prop"] = "INCAR.phonon"
        properties.append(phonon_params)

    return properties


def get_parameter_dict(opts: VaspModel):
    parameter_dict = {
        "structures":  ["returns/conf.*"],
        "interaction": get_interaction(opts),
        "relaxation": get_relaxation(opts)
    }
    if get_properties(opts):
        parameter_dict["properties"] = get_properties(opts)
        
    return parameter_dict


def vasp_runner(opts: VaspModel):
    cwd = Path.cwd()
    parameter_dicts = []
    print('start running....')
    workdir = cwd / 'workdir'
    returns_dir = workdir / 'returns'
    if os.path.exists(workdir):
        shutil.rmtree(workdir)
    workdir.mkdir()
    returns_dir.mkdir()

    # papare input POSCAR
    count = 0
    for ii in opts.configurations:
        os.chdir(workdir)
        conf_dir = returns_dir / ("conf.%06d" % count)
        conf_dir.mkdir()
        os.chdir(cwd)
        shutil.copy(ii, conf_dir/'POSCAR')
        count += 1

    # papare INCAR
    shutil.copy(opts.incar, workdir)

    # papare POTCAR
    for ii in opts.potcar:
        shutil.copy(ii, workdir)

    os.chdir(workdir)
    # papare global config
    config_dict = get_global_config(opts)
    
    # papare parameter files
    if opts.parameter_files:
        for ii in opts.parameter_files:
            os.chdir(cwd)
            with open(ii, 'r') as f:
                j = json.load(f)
                j["structures"] = ["returns/conf.*"]
            with open(ii, 'w') as r:
                json.dump(j, r, indent=2)
            shutil.copy(ii, workdir)
            parameter_dicts.append(loadfn(ii))
            os.chdir(workdir)
    else:
        parsed_parameter_dict = get_parameter_dict(opts)
        json.dump(parsed_parameter_dict, open('parameter_tmp.json', 'w'), indent=2)
        parsed_parameter_dict = loadfn('parameter_tmp.json')
        parameter_dicts.append(parsed_parameter_dict)
    
    # submit APEX workflow
    submit_workflow(
        parameter_dicts=parameter_dicts,
        config_dict=config_dict,
        work_dirs=['./'],
        indicated_flow_type=None,
        labels=opts.dflow_labels
    )

    os.chdir(cwd)
    shutil.copytree(workdir, Path(opts.output_directory)/'workdir', dirs_exist_ok = True)