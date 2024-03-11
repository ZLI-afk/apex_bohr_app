from pathlib import Path
import os
import shutil
import json
from copy import deepcopy

from dp.launching.typing import BaseModel, Field
from dp.launching.typing import InputFilePath, OutputDirectory
from dp.launching.typing import Int, Float, List, Enum, String, Dict
from dp.launching.typing.addon.sysmbol import Exists, NotExists, Equal, NotEqual
import dp.launching.typing.addon.ui as ui
from dp.launching.typing import BohriumUsername, BohriumTicket, BohriumProjectId
from dp.launching.typing import (
    DflowArgoAPIServer, DflowK8sAPIServer,
    DflowAccessToken, DflowStorageEndpoint,
    DflowStorageRepository, DflowLabels
)
from dp.launching.cli import to_runner

import dflow
from dflow.plugins import bohrium
from dflow.plugins.bohrium import TiefblueClient
from dflow import Workflow

from apex.submit import submit_workflow


def get_global_config(opts: Model) -> Dict:
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
            "projectId": opts.bohrium_project_id
        },
        "machine": {
                "batch_type": "Bohrium",
                "context_type": "Bohrium",
                "remote_profile": {
                    "email": opts.bohrium_username,
                    "password": opts.bohrium_ticket,
                    "program_id": int(opts.bohrium_project_id),
                    "input_data": {
                        "job_type": "container",
                        "platform": "ali",
                        "scass_type": opts.scass_type,
                    },
                },
            },
        "apex_image_name": opts.apex_image_name,
        "run_image_name": opts.run_image_name,
        "group_size": opts.group_size,
        "pool_size": opts.pool_size,
        "run_command": opts.run_command,
        "is_bohrium_dflow": True,
    }
    return global_config


def prep_parameter(opts: Model) -> Dict:
    parameter_dict = {
        "structures":  ["returns/conf.*"],
        "interaction": {},
        "relaxation": {},
        "properties": []
    }
    return parameter_dict


class DflowConfig(BaseModel):
    # Bohrium config
    bohrium_username: BohriumUsername
    bohrium_ticket: BohriumTicket
    bohrium_project_id: BohriumProjectId

    # dflow config
    dflow_labels: DflowLabels
    dflow_argo_api_server: DflowArgoAPIServer
    dflow_k8s_api_server: DflowK8sAPIServer
    dflow_access_token: DflowAccessToken
    dflow_storage_endpoint: DflowStorageEndpoint
    dflow_storage_repository: DflowStorageRepository


class UploadFiles(BaseModel):
    configuration_path: List[InputFilePath] = \
        Field(..., description='Configuration POSCAR to be tested (name differently for multiple files)')
    optional_file_path: List[InputFilePath] = \
        Field(description='Other optional files required during test (e.g. *.pb, INCAR, POTCAR)')
    parameter_json_path: List[InputFilePath] = \
        Field(ftypes=['json'], description='Test parameter json files (maximum 2 allowed)')


class CalculatorOptions(String, Enum):
    """
    枚举类型，多选一。
    表示APEX的指定calculator的optional argument
    """
    lammps = "LAMMPS"
    vasp = "VASP"
    abacus = "ABACUS"


class FlowTypeOptions(String, Enum):
    """
    枚举类型，多选一。
    表示APEX的指定flow_type的optional argument
    """
    default = "Auto-detect"
    relaxation = "Relaxation Workflow"
    joint = "Joint (relaxation and property-test) Workflow"


class Model(BaseModel):
    """
    用于定义参数和原始文件
    """
    # `...`表示这个是必须的参数

    #global_json_path: InputFilePath = Field(..., ftypes=[
    #                                           'json'], description='输入的全局配置JSON文件')

    output_directory: OutputDirectory = Field(default='./outputs')
    calculator: CalculatorOptions = Field(default=CalculatorOptions.lammps, description='Specify type of calculator')
    flow_type: FlowTypeOptions = Field(default=FlowTypeOptions.default, description='Specify type of workflow (optional)')


    run_image_name: String = Field(
        default=None, 
        description='Run step image address'
    )
    run_command: String = Field(
        default=None, 
        description='Run step command'
    )
    scass_type: String = Field(
        default=None, 
        description='Bohrium machine node type for running'
    )
    apex_image_name: String = Field(
        default="registry.dp.tech/dptech/prod-11045/apex-dependency:1.1.0", 
        description='APEX image address'
    )
    group_size: Int = Field(
        default=1, 
        description='Number of tasks per parallel run group'
    )
    pool_size: Int = Field(
        default=1, 
        description='For multi tasks per parallel group, the pool size of multiprocessing pool to handle each task (1 for serial, -1 for infinity)'
    )
    #custom_global: Dict = Field(
    #    default=None, 
    #    description='Customize global configuration dictionary'
    #)


def runner(opts: Model):
    print('start running....')
    prep_global_config(opts)
    cwd = Path.cwd()
    output_dir = cwd / 'returns'
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    output_dir.mkdir()
    count = 0
    for ii in opts.configuration_path:
        os.chdir(output_dir)
        conf_dir = output_dir / ("conf.%06d" % count)
        conf_dir.mkdir()
        os.chdir(cwd)
        shutil.copy(ii, conf_dir/'POSCAR')
        count += 1

    os.chdir(cwd)
    for ii in opts.parameter_json_path:
        with open(ii, 'r') as f:
            j = json.load(f)
        j["structures"] = ["returns/conf.*"]
        with open(ii, 'w') as r:
            json.dump(j, r, indent=2)

    for ii in opts.optional_file_path:
        shutil.copy(ii, cwd)

    param_args_str = ' '.join(opts.parameter_json_path)

    if opts.flow_type == "Auto-detect":
        flow_type = None
    elif opts.flow_type == "Relaxation Workflow":
        flow_type = "relax"
    elif opts.flow_type == "Joint Workflow":
        flow_type = "joint"
    else:
        raise RuntimeError('Wrong argument type')
    

    submit_workflow(
        parameter=opts.parameter_json_path,
        config_file='global.json',
        work_dir='.',
        flow_type=flow_type,
        labels=opts.dflow_labels
    )

    #cmd = f'apex submit {param_args_str} -c global_config.json {flow_type}'
    # 运行命令行
    #os.system(cmd)

    os.chdir(cwd)
    shutil.copytree(output_dir, Path(opts.output_directory)/'returns', dirs_exist_ok = True)


if __name__ == "__main__":
    import sys

    # 传入命令行参数运行程序
    to_runner(Model, runner)(sys.argv[1:])