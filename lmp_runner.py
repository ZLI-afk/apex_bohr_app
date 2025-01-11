from pathlib import Path
import os
import shutil
import json
from monty.serialization import loadfn
from apex.submit import submit_workflow
from lmp_model import LammpsModel


def get_global_config(opts: LammpsModel):
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
        "run_image_name": opts.lammps_image_name,
        "group_size": opts.group_size,
        "pool_size": opts.pool_size,
        "run_command": opts.lammps_run_command,
        "is_bohrium_dflow": True,
    }
    json.dump(global_config, open('global_config_tmp.json', 'w'), indent=2)
    global_config = loadfn('global_config_tmp.json')
    #os.remove('global_config_tmp.json')
    return global_config


def get_interaction(opts: LammpsModel):

    interaction = {
        "type": opts.inter_type,
        "model": [Path(ii).name for ii in opts.potential_models] if len(opts.potential_models) > 1 \
            else Path(opts.potential_models[0]).name,
        "type_map": opts.type_map,
        "deepmd_version": opts.dpmd_version,
    }
    if opts.relax_in_lmp:
        with open('custom_relax_in.lammps', 'w') as f:
            f.write(opts.relax_in_lmp)
        interaction["in_lammps"] = "custom_relax_in.lammps"
    return interaction


def get_relaxation(opts: LammpsModel):
    relaxation = {
        "cal_setting": {
            "etol": opts.etol,
            "ftol": opts.ftol,
            "maxiter": opts.maxiter,
            "maxeval": opts.maxeval,
            "relax_pos": opts.relax_pos,
            "relax_shape": opts.relax_shape,
            "relax_vol": opts.relax_vol,
        }
    }
    return relaxation


def get_properties(opts: LammpsModel):
    properties = []
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
                "etol": opts.eos_etol,
                "ftol": opts.eos_ftol,
                "maxiter": opts.eos_maxiter,
                "maxeval": opts.eos_maxeval,
                "relax_pos": opts.eos_relax_pos,
                "relax_shape": opts.eos_relax_shape,
                "relax_vol": opts.eos_relax_vol,
            }
            if opts.eos_in_lmp:
                with open('custom_eos_in.lammps', 'w') as f:
                    f.write(opts.eos_in_lmp)
                eos_params["cal_setting"]["input_prop"] = "custom_eos_in.lammps"
        properties.append(eos_params)

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
                "etol": opts.elastic_etol,
                "ftol": opts.elastic_ftol,
                "maxiter": opts.elastic_maxiter,
                "maxeval": opts.elastic_maxeval,
                "relax_pos": opts.elastic_relax_pos,
                "relax_shape": opts.elastic_relax_shape,
                "relax_vol": opts.elastic_relax_vol,
            }
            if opts.elastic_in_lmp:
                with open('custom_elastic_in.lammps', 'w') as f:
                    f.write(opts.elastic_in_lmp)
                elastic_params["cal_setting"]["input_prop"] = "custom_elastic_in.lammps"
        properties.append(elastic_params)
    
    if opts.select_surface:
        surface_params = {
            "type": "surface",
            "skip": False,
            "max_miller": opts.max_miller,
            "min_slab_size": opts.min_slab_size,
            "min_vacuum_size": opts.min_vacuum_size,
            "pert_xz": opts.pert_xz,
            "cal_type": opts.surface_cal_type
        }
        if opts.custom_surface_calc:
            surface_params["cal_setting"] = {
                "etol": opts.surface_etol,
                "ftol": opts.surface_ftol,
                "maxiter": opts.surface_maxiter,
                "maxeval": opts.surface_maxeval,
                "relax_pos": opts.surface_relax_pos,
                "relax_shape": opts.surface_relax_shape,
                "relax_vol": opts.surface_relax_vol,
            }
            if opts.surface_in_lmp:
                with open('custom_surface_in.lammps', 'w') as f:
                    f.write(opts.surface_in_lmp)
                surface_params["cal_setting"]["input_prop"] = "custom_surface_in.lammps"
        properties.append(surface_params)

    if opts.select_interstitial:
        interstitial_params = {
            "type": "interstitial",
            "skip": False,
            "supercell_size": opts.interstitial_supercell_size,
            "insert_ele": opts.insert_ele,
            "cal_type": opts.interstitial_cal_type
        }
        if opts.custom_interstitial_calc:
            interstitial_params["cal_setting"] = {
                "etol": opts.interstitial_etol,
                "ftol": opts.interstitial_ftol,
                "maxiter": opts.interstitial_maxiter,
                "maxeval": opts.interstitial_maxeval,
                "relax_pos": opts.interstitial_relax_pos,
                "relax_shape": opts.interstitial_relax_shape,
                "relax_vol": opts.interstitial_relax_vol,
            }
            if opts.interstitial_in_lmp:
                with open('custom_interstitial_in.lammps', 'w') as f:
                    f.write(opts.interstitial_in_lmp)
                interstitial_params["cal_setting"]["input_prop"] = "custom_interstitial_in.lammps"
        properties.append(interstitial_params)

    if opts.select_vacancy:
        vacancy_params = {
            "type": "vacancy",
            "skip": False,
            "supercell_size": opts.vacancy_supercell_size,
            "cal_type": opts.vacancy_cal_type
        }
        if opts.custom_vacancy_calc:
            vacancy_params["cal_setting"] = {
                "etol": opts.vacancy_etol,
                "ftol": opts.vacancy_ftol,
                "maxiter": opts.vacancy_maxiter,
                "maxeval": opts.vacancy_maxeval,
                "relax_pos": opts.vacancy_relax_pos,
                "relax_shape": opts.vacancy_relax_shape,
                "relax_vol": opts.vacancy_relax_vol,
            }
            if opts.vacancy_in_lmp:
                with open('custom_vacancy_in.lammps', 'w') as f:
                    f.write(opts.vacancy_in_lmp)
                vacancy_params["cal_setting"]["input_prop"] = "custom_vacancy_in.lammps"
        properties.append(vacancy_params)
        
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
            "cal_type": opts.gamma_cal_type,
            "add_fix": [
                "true" if opts.add_fix_x else "false", 
                "true" if opts.add_fix_y else "false", 
                "true" if opts.add_fix_z else "false"
                ]
        }
        if opts.custom_gamma_calc:
            gamma_params["cal_setting"] = {
                "etol": opts.gamma_etol,
                "ftol": opts.gamma_ftol,
                "maxiter": opts.gamma_maxiter,
                "maxeval": opts.gamma_maxeval,
                "relax_pos": opts.gamma_relax_pos,
                "relax_shape": opts.gamma_relax_shape,
                "relax_vol": opts.gamma_relax_vol,
            }
            if opts.gamma_in_lmp:
                with open('custom_gamma_in.lammps', 'w') as f:
                    f.write(opts.gamma_in_lmp)
                gamma_params["cal_setting"]["input_prop"] = "custom_gamma_in.lammps"
        properties.append(gamma_params)
        
    if opts.select_phonon:
        phonon_params = {
            "type": "phonon",
            "skip": False,
            "primitive_cell": opts.primitive_cell,
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
        if opts.phonon_in_lmp:
            with open('custom_phonon_in.lammps', 'w') as f:
                f.write(opts.phonon_in_lmp)
            phonon_params["cal_setting"]["input_prop"] = "custom_phonon_in.lammps"
        properties.append(phonon_params)

    return properties


def get_parameter_dict(opts: LammpsModel):
    parameter_dict = {
        "structures":  ["returns/conf.*"],
        "interaction": get_interaction(opts),
        "relaxation": get_relaxation(opts)
    }
    if get_properties(opts):
        parameter_dict["properties"] = get_properties(opts)
        
    return parameter_dict


def lmp_runner(opts: LammpsModel):
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

    # papare potential files
    for ii in opts.potential_models:
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